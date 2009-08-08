from mysite.base.tests import make_twill_url, TwillTests

from mysite.profile.models import Person
import mysite.customs.miro

import django.test
from .models import Project, Bug
from . import views
import lpb2json
import datetime
import mysite.search.launchpad_crawl

import simplejson
import os
import mock
import time
import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
from django.test import TestCase
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler
from django.core.urlresolvers import reverse

from django.conf import settings
from StringIO import StringIO

class AutoCompleteTests(TwillTests):
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
        suggestions = views.get_autocompletion_suggestions('')
        self.assert_("lang:Vogon" in suggestions)

    def testSuggestForAllFields(self):
        c_suggestions = views.get_autocompletion_suggestions('C')
        self.assert_('lang:C++' in c_suggestions)
        self.assert_('project:ComicChat' in c_suggestions)

    def testQueryNotFieldSpecificFindProject(self):
        c_suggestions = views.get_autocompletion_suggestions('Comi')
        self.assert_('project:ComicChat' in c_suggestions)

    def testQueryFieldSpecific(self):
        lang_C_suggestions = views.get_autocompletion_suggestions(
                'lang:C')
        self.assert_('lang:C++' in lang_C_suggestions)
        self.assert_('lang:Python' not in lang_C_suggestions)
        self.assert_('project:ComicChat' not in lang_C_suggestions)

    def testSuggestsCorrectStringsFormattedForJQueryAutocompletePlugin(self):
        suggestions_list = views.get_autocompletion_suggestions('')
        suggestions_string = views.list_to_jquery_autocompletion_format(
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

class TestNonJavascriptSearch(TwillTests):
    fixtures = ['bugs-for-two-projects.json']

    def testSearch(self):
        bugs = Bug.objects.order_by('last_touched')[:10]

        response = self.client.get('/search/')
        # Search shows nothing when you have no query.
        self.assertEqual(response.context[0]['bunch_of_bugs'], [])

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

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.objects.filter(project__name=
                                  'Exaile').order_by('last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

        tc.fv('search_opps', 'language', 'c#')
        tc.submit()
        
        # Grab descriptions of first 10 GNOME-Do bugs
        bugs = Bug.objects.filter(project__name=
                                  'GNOME-Do').order_by('last_touched')[:10]
        for bug in bugs:
            tc.find(bug.description)

    def testSearchCombinesQueries(self):
        response = self.client.get('/search/',
                                   {'language': 'python "Description #10"'})

        found_it = False
        for bug in response.context[0]['bunch_of_bugs']:
            if bug.title == 'Title #10':
                found_it = True

        self.assert_(found_it)

    def testSearchProjectName(self):
        response = self.client.get('/search/',
                                   {'language': 'exaile #10'})

        found_it = False
        for bug in response.context[0]['bunch_of_bugs']:
            if bug.title == 'Title #10':
                found_it = True

        self.assert_(found_it)

    def test_json_view(self):
        tc.go(make_twill_url('http://openhatch.org/search/?format=json&jsoncallback=callback&language=python'))
        response = tc.show()
        self.assert_(response.startswith('callback'))
        json_string_with_parens = response.split('callback', 1)[1]
        self.assert_(json_string_with_parens[0] == '(')
        self.assert_(json_string_with_parens[-1] == ')')
        json_string = json_string_with_parens[1:-1]
        objects = simplejson.loads(json_string)
        self.assert_('pk' in objects[0])

    def testPagination(self):
        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.objects.filter(project__name=
                                  'Exaile').order_by('last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

        # Hit the next button
        tc.follow('Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.objects.filter(project__name=
                                  'Exaile').order_by('last_touched')[10:20]

        for bug in bugs:
            tc.find(bug.description)

    def testPaginationAndChangingSearchQuery(self):

        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.objects.filter(project__name=
                                  'Exaile').order_by('last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

        # Hit the next button
        tc.follow('Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.objects.filter(project__name=
                                  'Exaile').order_by('last_touched')[10:20]

        for bug in bugs:
            tc.find(bug.description)

        # Now, change the query - do we stay that paginated?
        tc.fv('search_opps', 'language', 'c#')
        tc.submit()

        # Grab descriptions of first 10 GNOME-Do bugs
        bugs = Bug.objects.filter(project__name=
                                  'GNOME-Do').order_by(
            'last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

sample_launchpad_data_dump = mock.Mock()
sample_launchpad_data_dump.return_value = [dict(
        url='', project='rose.makesad.us', text='', status='',
        importance='low', reporter={'lplogin': 'a',
                                    'realname': 'b'},
        comments=[], date_updated=time.localtime(),
        date_reported=time.localtime(),
        title="Joi's Lab AFS",)]

class AutoCrawlTests(TwillTests):
    @mock.patch('mysite.search.launchpad_crawl.dump_data_from_project', 
                sample_launchpad_data_dump)
    def testSearch(self):
        # Verify that we can't find a bug with the right description
        self.assertRaises(mysite.search.models.Bug.DoesNotExist,
                          mysite.search.models.Bug.objects.get,
                          title="Joi's Lab AFS")
        # Now get all the bugs about rose
        mysite.search.launchpad_crawl.grab_lp_bugs(lp_project='rose',
                                            openhatch_project=
                                            'rose.makesad.us')
        # Now see, we have one!
        b = mysite.search.models.Bug.objects.get(title="Joi's Lab AFS")
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

class LaunchpadImporterTests(TwillTests):
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
        mysite.search.launchpad_crawl.handle_launchpad_bug_update(query_data, new_data)
        # Verify that the bug was stored.
        bug = Bug.objects.get(canonical_bug_link=
                                       query_data['canonical_bug_link'])
        for key in new_data:
            self.assertEqual(getattr(bug, key), new_data[key])

        # Now re-do the update, this time with more people involved
        new_data['people_involved'] = 1000 * 1000 * 1000
        # pass the data in...
        bug = mysite.search.launchpad_crawl.handle_launchpad_bug_update(query_data,
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
        out_q, out_d = mysite.search.launchpad_crawl.clean_lp_data_dict(sample_in)
        self.assertEqual(sample_out_query, out_q)
        # Make sure last_polled is at least in the same year
        self.assertEqual(out_d['last_polled'].year, datetime.date.today().year)
        del out_d['last_polled']
        self.assertEqual(sample_out_data, out_d)

class Recommend(TwillTests):
    fixtures = ['user-paulproteus.json',
            'person-paulproteus.json',
            'cchost-data-imported-from-ohloh.json',
            'bugs-for-two-projects.json',
            'extra-fake-cchost-related-projectexps.json']

    def test_get_recommended_search_terms_for_user(self):
        person = Person.objects.get(user__username='paulproteus')
        terms = person.get_recommended_search_terms()
        self.assertEqual(terms,
                [u'Automake', u'C#', u'C++', u'Make', u'Mozilla Firefox', 
                 u'Python', u'shell script', u'XUL'])

    def test_search_page_context_includes_recommendations(self):
        client = self.login_with_client()
        response = client.get('/search/')
        self.assertEqual(
                response.context[0]['suggestions'],
                [
                    (0, 'Automake',        False),
                    (1, 'C#',              False),
                    (2, 'C++',             False),
                    (3, 'Make',            False),
                    (4, 'Mozilla Firefox', False),
                    (5, 'Python',          False),
                    (6, 'shell script',    False),
                    (7, 'XUL',             False),
                    ])

# We're not doing this one because at the moment suggestions only work in JS.
#    def test_recommendations_with_twill(self):
#        self.login_with_twill()
#        tc.go(make_twill_url('http://openhatch.org/search/'))
#        tc.fv('suggested_searches', 'use_0', '0') # Automake
#        tc.fv('suggested_searches', 'use_1', '0') # C
#        tc.fv('suggested_searches', 'use_2', '0') # C++
#        tc.fv('suggested_searches', 'use_3', '0') # Firefox
#        tc.fv('suggested_searches', 'use_4', '0') # Python
#        tc.fv('suggested_searches', 'use_5', '1') # XUL
#        tc.fv('suggested_searches', 'start', '0')
#        tc.fv('suggested_searches', 'end', '100')
#        tc.submit()
#
#        # Check that if you click checkboxes,
#        # you get the right list of bugs.
#        # Test for bugs that ought to be there
#        # and bugs that ought not to be. 
#        tc.find("Yo! This is a bug in XUL but not Firefox")
#        tc.find("Oy! This is a bug in XUL and Firefox")
#
#        tc.fv('suggested_searches', 'use_0', '0') # Automake
#        tc.fv('suggested_searches', 'use_1', '0') # C
#        tc.fv('suggested_searches', 'use_2', '0') # C++
#        tc.fv('suggested_searches', 'use_3', '1') # Firefox
#        tc.fv('suggested_searches', 'use_4', '0') # Python
#        tc.fv('suggested_searches', 'use_5', '1') # XUL
#        tc.fv('suggested_searches', 'start', '0')
#        tc.fv('suggested_searches', 'end', '100')
#        tc.submit()
#
#        tc.notfind("Yo! This is a bug in XUL but not Firefox")
#        tc.find("Oy! This is a bug in XUL and Firefox")

class TestQuerySplitter(django.test.TestCase):
    def test_split_query_words(self):
        easy = '1 2 3'
        self.assertEqual(mysite.search.views.split_query_words(easy),
                         ['1', '2', '3'])

        easy = '"1"'
        self.assertEqual(mysite.search.views.split_query_words(easy),
                         ['1'])

        easy = 'c#'
        self.assertEqual(mysite.search.views.split_query_words(easy),
                         ['c#'])

# vim: set ai et ts=4 sw=4 columns=80:
