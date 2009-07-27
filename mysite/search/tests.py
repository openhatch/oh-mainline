import django.test
from search.models import Project, Bug
import search.views
import lpb2json
import datetime
import search.launchpad_crawl

import mock
import time
import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
from django.test import TestCase
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler
from StringIO import StringIO

# FIXME: Later look into http://stackoverflow.com/questions/343622/how-do-i-submit-a-form-given-only-the-html-source

# Functions you'll need:

def twill_setup():
    app = AdminMediaHandler(WSGIHandler())
    twill.add_wsgi_intercept("127.0.0.1", 8080, lambda: app)

def twill_teardown():
    twill.remove_wsgi_intercept('127.0.0.1', 8080)

def make_twill_url(url):
    # modify this
    return url.replace("http://openhatch.org/",
            "http://127.0.0.1:8080/")

def twill_quiet():
    # suppress normal output of twill.. You don't want to
    # call this if you want an interactive session
    twill.set_output(StringIO())

class AutoCompleteTests(django.test.TestCase):
    """
    Test whether the autocomplete can handle
     - a field-specific query
     - a non-field-specific (fulltext) query
    """

    def setUp(self):
        self.project_chat = Project.objects.create(name='ComicChat', language='C++')
        self.project_kazaa = Project.objects.create(name='Kazaa', language='Vogon')
        self.bug_in_chat = Bug.objects.create(project=self.project_chat,
                people_involved=2,
                date_reported=datetime.date(2009, 4, 1),
                last_touched=datetime.date(2009, 4, 2),
                last_polled=datetime.date(2009, 4, 2),
                submitter_realname="Zaphod Beeblebrox",
                submitter_username="zb",
                canonical_bug_link="http://example.com/",
                )

    def testSuggestionsMinimallyWorks(self):
        suggestions = search.views.get_autocompletion_suggestions('')
        self.assert_("lang:Vogon" in suggestions)

    def testSuggestForAllFields(self):
        c_suggestions = search.views.get_autocompletion_suggestions('C')
        self.assert_('lang:C++' in c_suggestions)
        self.assert_('project:ComicChat' in c_suggestions)

    def testQueryNotFieldSpecificFindProject(self):
        c_suggestions = search.views.get_autocompletion_suggestions('Comi')
        self.assert_('project:ComicChat' in c_suggestions)

    def testQueryFieldSpecific(self):
        lang_C_suggestions = search.views.get_autocompletion_suggestions(
                'lang:C')
        self.assert_('lang:C++' in lang_C_suggestions)
        self.assert_('lang:Python' not in lang_C_suggestions)
        self.assert_('project:ComicChat' not in lang_C_suggestions)

    def testSuggestsCorrectStringsFormattedForJQueryAutocompletePlugin(self):
        suggestions_list = search.views.get_autocompletion_suggestions('')
        suggestions_string = search.views.list_to_jquery_autocompletion_format(
                suggestions_list)
        suggestions_list_reconstructed = suggestions_string.split("\n")
        self.assert_("project:ComicChat" in suggestions_list_reconstructed)
        self.assert_("lang:Vogon" in suggestions_list_reconstructed)
        self.assert_("lang:C++" in suggestions_list_reconstructed)

    def testSuggestsSomethingOverHttp(self):
        response = self.client.get( '/search/get_suggestions', {'q': 'C'})
        self.assertContains(response, "project:ComicChat\nlang:C++")

    def testSuggesterFailsOnEmptyString(self):
        response = self.client.get( '/search/get_suggestions', {'q': ''})
        self.assertEquals(response.status_code, 500)

    def testSuggesterFailsWithImproperQueryString(self):
        response = self.client.get( '/search/get_suggestions', {})
        self.assertEquals(response.status_code, 500)

class TestNonJavascriptSearch(django.test.TestCase):
    fixtures = ['bugs-for-two-projects.json']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testSearch(self):
        response = self.client.get('/search/')
        for n in range(1, 11):
            self.assertContains(response, 'Title #%d' % n)
            self.assertContains(response, 'Description #%d' % n)

    def testMatchingBugsFromMtoN(self):
        response = self.client.get('/search/')
        ctxt_we_care_about = [c for c in response.context if 'start' in c][0]
        self.failUnlessEqual(ctxt_we_care_about['start'], 1)
        self.failUnlessEqual(ctxt_we_care_about['end'], 10)

    def testSearchWithArgs(self):
        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()
        for n in range(1, 11):
            tc.find('Description #%d' % n)

        tc.fv('search_opps', 'language', 'c#')
        tc.submit()
        for n in range(717, 727):
            tc.find('Description #%d' % n)

    def testPagination(self):
        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()
        for n in range(1, 11):
            tc.find('Description #%d' % n)

        tc.follow('Next')
        for n in range(11, 21):
            tc.find('Description #%d' % n)

    def testPaginationAndChangingSearchQuery(self):

        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()
        for n in range(1, 11):
            tc.find('Description #%d' % n)

        tc.follow('Next')
        for n in range(11, 21):
            tc.find('Description #%d' % n)

        tc.fv('search_opps', 'language', 'c#')
        tc.submit()
        for n in range(717, 727):
            tc.find('Description #%d' % n)
        tc.follow('Next')
        for n in range(727, 737):
            tc.find('Description #%d' % n)

sample_launchpad_data_dump = mock.Mock()
sample_launchpad_data_dump.return_value = [dict(
        url='', project='rose.makesad.us', text='', status='',
        importance='low', reporter={'lplogin': 'a',
                                    'realname': 'b'},
        comments=[], date_updated=time.localtime(),
        date_reported=time.localtime(),
        title="Joi's Lab AFS",)]

class AutoCrawlTests(django.test.TestCase):
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    @mock.patch('search.launchpad_crawl.dump_data_from_project', 
                sample_launchpad_data_dump)
    def testSearch(self):
        # Verify that we can't find a bug with the right description
        self.assertRaises(search.models.Bug.DoesNotExist,
                          search.models.Bug.objects.get,
                          title="Joi's Lab AFS")
        # Now get all the bugs about rose
        search.launchpad_crawl.grab_lp_bugs(lp_project='rose',
                                            openhatch_project=
                                            'rose.makesad.us')
        # Now see, we have one!
        b = search.models.Bug.objects.get(title="Joi's Lab AFS")
        self.assertEqual(b.project.name, 'rose.makesad.us')
        # Ta-da.
        return b

    def test_running_job_twice_does_update(self):
        b = self.testSearch()
        b.description = 'Eat more potato starch'
        b.title = 'Yummy potato paste'
        b.save()

        new_b = self.testSearch()
        self.assertEqual(new_b.title, "Joi's Lab AFS") # bug title restored
        # thanks to fresh import

class LaunchpadImporterTests(django.test.TestCase):
    def test_lp_update_handler(self):
        '''Test the Launchpad import handler with some fake data.'''
        some_date = datetime.datetime(2009, 4, 1, 2, 2, 2)
        query_data = dict(project='GNOME-Do',
                          canonical_bug_link='http://example.com/1')
        new_data = dict(title='Title', status='Godforsaken',
                        description='Everything should be better',
                        importance='High',
                        people_involved=1000 * 1000,
                        submitter_username='yourmom',
                        submitter_realname='Your Mom',
                        date_reported=some_date,
                        last_touched=some_date,
                        last_polled=some_date)

        # Create the bug...
        search.launchpad_crawl.handle_launchpad_bug_update(query_data, new_data)
        # Verify that the bug was stored.
        bug = Bug.objects.get(canonical_bug_link=
                                       query_data['canonical_bug_link'])
        for key in new_data:
            self.assertEqual(getattr(bug, key), new_data[key])

        # Now re-do the update, this time with more people involved
        new_data['people_involved'] = 1000 * 1000 * 1000
        # pass the data in...
        bug = search.launchpad_crawl.handle_launchpad_bug_update(query_data,
                                                                 new_data)
        # Do a get; this will explode if there's more than one with the
        # canonical_bug_link, so it tests duplicate finding.
        bug = Bug.objects.get(canonical_bug_link=
                                       query_data['canonical_bug_link'])

        for key in new_data:
            self.assertEqual(getattr(bug, key), new_data[key])

    def test_lp_data_clean(self):
        now_t = (2009, 4, 1, 5, 13, 2) # partial time tuple
        now_d = datetime.datetime(2009, 4, 1, 5, 13, 2)
        # NOTE: We do not test for time zone correctness.
        sample_in = dict(project='GNOME-Do', url='http://example.com/1',
                         title='Title', text='Some long text',
                         importance=None, status='Ready for take-off',
                         comments=[{'user': {
                             'lplogin': 'jones', 'realname': 'Jones'}}],
                         reporter={'lplogin': 'bob', 'realname': 'Bob'},
                         date_reported=now_t,
                         date_updated=now_t,
                         )
        sample_out_query = dict(project='GNOME-Do',
                                canonical_bug_link='http://example.com/1')
        sample_out_data = dict(title='Title', description='Some long text',
                               importance='Unknown', status='Ready for take-off',
                               people_involved=2, submitter_realname='Bob',
                               submitter_username='bob',
                               date_reported=now_d,
                               last_touched=now_d)
        out_q, out_d = search.launchpad_crawl.clean_lp_data_dict(sample_in)
        self.assertEqual(sample_out_query, out_q)
        # Make sure last_polled is at least in the same year
        self.assertEqual(out_d['last_polled'].year, datetime.date.today().year)
        del out_d['last_polled']
        self.assertEqual(sample_out_data, out_d)

# vim: set ai et ts=4 sw=4 columns=80:
