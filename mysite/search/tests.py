from mysite.base.tests import make_twill_url, TwillTests

import mysite.account.tests
from mysite.profile.models import Person
import mysite.customs.miro
import mysite.search.controllers

import django.test
from mysite.search.models import Project, Bug
from mysite.search import views
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
from django.core.files.base import ContentFile

from django.db.models import Q 

from django.conf import settings
from StringIO import StringIO

class SearchTest(TwillTests):

    def search_via_twill(self, query=None):
        search_url = "http://openhatch.org/search/" 
        if query:
            search_url += '?q=%s' % query
        tc.go(make_twill_url(search_url))

    def search_via_client(self, query=None):
        search_url = "/search/" 
        return self.client.get(search_url, {'q': query})

class AutoCompleteTests(SearchTest):
    """
    Test whether the autocomplete can handle
     - a field-specific query
     - a non-field-specific (fulltext) query
    """

    def setUp(self):
        SearchTest.setUp(self)
        self.project_chat = Project.objects.create(name='ComicChat', language='C++')
        self.project_kazaa = Project.objects.create(name='Kazaa', language='Vogon')
        self.bug_in_chat = Bug.all_bugs.create(project=self.project_chat,
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

class SearchResultsSpecificBugs(SearchTest):
    fixtures = ['short_list_of_bugs.json']

    def setUp(self):
        SearchTest.setUp(self)

        query = 'PYTHON'

        # The four canonical_filters by which a bug can match a query
        whole_word = "[[:<:]]%s[[:>:]]" % query
        self.canonical_filters = [
                Q(project__language__iexact=query),
                Q(title__iregex=whole_word),
                Q(project__name__iregex=whole_word),
                Q(description__iregex=whole_word)
                ]

    def no_canonical_filters(self, except_one=Q()):
        """Returns the complex filter, 'Matches no canonical filters except the specified one.'"""

        # Create the complex filter, 'Matches no canonical filters,
        # except perhaps the specified one.'
        other_c_filters = Q() # Initial value
        for cf in self.canonical_filters:
            if cf != except_one: 
                other_c_filters = other_c_filters | cf 

        # Read this as "Just that one filter and no others."
        return except_one & ~other_c_filters

    def test_that_fixture_works_properly(self):
        """Is the fixture is wired correctly?
        
        To test the search engine, I've loaded the fixture with six
        'canonical' bugs. Four of them are canonical matches, two
        are canonical non-matches. A working search engine will return
        just the matches.

        There are four ways a bug can match a query:
            - project language = the query
            - project name contains the query
            - project title contains the query
            - project description contains the query

        Let's call each of these a 'canonical filter'.

        For each of these canonical filters, there should be a canonical bug
        in the fixture that matches that, and only that, filter.

        This test checks the fixture for the existence of these
        canonical bugs.

        If the fixture is wired correctly, when we search it for 
        'python', it will return bugs 1, 2, 3 and 4, and exclude
        bugs 400 and 401. """

        # Remember, a canonical bug meets ONLY ONE criterion.
        # Assert there's just one canonical bug per criterion.
        for cf in self.canonical_filters:
            matches = Bug.all_bugs.filter(self.no_canonical_filters(except_one=cf))[:]
            self.failUnlessEqual(len(matches), 1,
                    "There are %d, not 1, canonical bug(s) for the filter %s" % (len(matches), cf))

        # Assert there's at least one canonical nonmatch.
        canonical_non_matches = Bug.all_bugs.filter(self.no_canonical_filters())
        self.assert_(len(canonical_non_matches) > 1)

    def test_search_single_query(self):
        """Test that Query.get_bugs_unordered()
        produces the expected results."""
        response = self.client.get('/search/', {'q': 'python'})
        returned_bugs = response.context[0]['bunch_of_bugs']
        for cf in self.canonical_filters:
            self.failUnless(Bug.all_bugs.filter(cf)[0] in returned_bugs,
                    "Search engine did not correctly use the filter %s" % cf)

        for bug in Bug.all_bugs.filter(self.no_canonical_filters()):
            self.failIf(bug in returned_bugs, "Search engine returned a false positive: %s." % bug)

    def test_search_two_queries(self):

        title_of_bug_to_include = 'An interesting title'
        title_of_bug_to_exclude = "This shouldn't be in the results for [pyt*hon 'An interesting description']."

        # If either of these bugs aren't there, then this test won't work properly.
        self.assert_(len(list(Bug.all_bugs.filter(title=title_of_bug_to_include))) == 1)
        self.assert_(len(list(Bug.all_bugs.filter(title=title_of_bug_to_exclude))) == 1)

        response = self.client.get('/search/',
                                   {'q': 'python "An interesting description"'})

        included_the_right_bug = False
        excluded_the_wrong_bug = True
        for bug in response.context[0]['bunch_of_bugs']:
            if bug.title == title_of_bug_to_include:
                included_the_right_bug = True
            if bug.title == title_of_bug_to_exclude:
                excluded_the_wrong_bug = False

        self.assert_(included_the_right_bug)
        self.assert_(excluded_the_wrong_bug)

class SearchResults(TwillTests):
    fixtures = ['bugs-for-two-projects.json']

    def test_show_no_bugs_if_no_query(self):
        # Call up search page with no query.
        response = self.client.get('/search/')

        # The variable 'bunch_of_bugs', passed to the template, is a blank list.
        self.assertEqual(response.context[0]['bunch_of_bugs'], [])

    def test_paginate_by_default(self):
        response = self.client.get('/search/')
        ctxt_we_care_about = [c for c in response.context if 'start' in c][0]
        self.failUnlessEqual(ctxt_we_care_about['start'], 1)
        self.failUnlessEqual(ctxt_we_care_about['end'], 0)

    def test_json_view(self):
        tc.go(make_twill_url('http://openhatch.org/search/?format=json&jsoncallback=callback&q=python'))
        response = tc.show()
        self.assert_(response.startswith('callback'))
        json_string_with_parens = response.split('callback', 1)[1]
        self.assert_(json_string_with_parens[0] == '(')
        self.assert_(json_string_with_parens[-1] == ')')
        json_string = json_string_with_parens[1:-1]
        objects = simplejson.loads(json_string)
        self.assert_('pk' in objects[0]['bugs'][0])

    def testPagination(self):
        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'q', 'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  'Exaile').order_by('-last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

        # Hit the next button
        tc.follow('Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  'Exaile').order_by('-last_touched')[10:20]

        for bug in bugs:
            tc.find(bug.description)

    def testPaginationAndChangingSearchQuery(self):

        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'q', 'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  'Exaile').order_by('-last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

        # Hit the next button
        tc.follow('Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  'Exaile').order_by('-last_touched')[10:20]

        for bug in bugs:
            tc.find(bug.description)

        # Now, change the query - do we stay that paginated?
        tc.fv('search_opps', 'q', 'c#')
        tc.submit()

        # Grab descriptions of first 10 GNOME-Do bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  'GNOME-Do').order_by(
            '-last_touched')[:10]

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

class AutoCrawlTests(SearchTest):
    @mock.patch('mysite.search.launchpad_crawl.dump_data_from_project', 
                sample_launchpad_data_dump)
    def testSearch(self):
        # Verify that we can't find a bug with the right description
        self.assertRaises(mysite.search.models.Bug.DoesNotExist,
                          mysite.search.models.Bug.all_bugs.get,
                          title="Joi's Lab AFS")
        # Now get all the bugs about rose
        mysite.search.launchpad_crawl.grab_lp_bugs(lp_project='rose',
                                            openhatch_project=
                                            'rose.makesad.us')
        # Now see, we have one!
        b = mysite.search.models.Bug.all_bugs.get(title="Joi's Lab AFS")
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

class LaunchpadImporterTests(SearchTest):
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
        bug = Bug.all_bugs.get(canonical_bug_link=
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
        bug = Bug.all_bugs.get(canonical_bug_link=
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

class Recommend(SearchTest):
    fixtures = ['user-paulproteus.json',
            'person-paulproteus.json',
            'cchost-data-imported-from-ohloh.json',
            'bugs-for-two-projects.json',
            'extra-fake-cchost-related-projectexps.json',
            'tags']

    # FIXME: Add a 'recommend_these_in_bug_search' field to TagType
    # Use that to exclude 'will never understand' tags from recommended search terms.
    def test_get_recommended_search_terms_for_user(self):
        person = Person.objects.get(user__username='paulproteus')
        recommended_terms = person.get_recommended_search_terms()

        # By 'source' I mean a source of recommendations.
        source2terms = {
                'languages in citations': ['Automake', 'C#', 'C++', 'Make', 
                    'Python', 'shell script', 'XUL'],
                'projects in citations': ['Mozilla Firefox'], 
                'tags': ['algol', 'symbolist poetry', 'rails', 'chinese chess']
                }

        for source, terms in source2terms.items():
            for term in terms:
                self.assert_(term in recommended_terms,
                        "Expected %s in recommended search terms "
                        "inspired by %s." % (term, source))

    # FIXME: Include recommendations from tags.
    def test_search_page_context_includes_recommendations(self):
        client = self.login_with_client()
        response = client.get('/search/')

        source2terms = {
                'languages in citations': ['Automake', 'C#', 'C++', 'Make', 
                    'Python', 'shell script', 'XUL'],
                'projects in citations': ['Mozilla Firefox'], 
                'tags': ['algol', 'symbolist poetry', 'rails', 'chinese chess']
                }

        tags_in_template = [tup[1] for tup in response.context[0]['suggestions']]

        for source, terms in source2terms.items():
            for term in terms:
                self.assert_(term in tags_in_template,
                        "Expected %s in template"
                        "inspired by %s." % (term, source))

        def compare_lists(one, two):
            self.assertEqual(len(one), len(two))
            self.assertEqual(set(one), set(two))

        expected_tags = sum(source2terms.values(), [])
        compare_lists(expected_tags, tags_in_template)

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

class SplitIntoTerms(django.test.TestCase):
    def test_split_into_terms(self):
        easy = '1 2 3'
        self.assertEqual(
                mysite.search.controllers.Query.split_into_terms(easy),
                ['1', '2', '3'])

        easy = '"1"'
        self.assertEqual(
                mysite.search.controllers.Query.split_into_terms(easy),
                ['1'])

        easy = 'c#'
        self.assertEqual(
                mysite.search.controllers.Query.split_into_terms(easy),
                ['c#'])

class IconGetsScaled(SearchTest):
    def test_project_scales_its_icon_down_for_use_in_badge(self):
        '''This test shows that the Project class successfully stores
        a scaled-down version of its icon in the icon_smaller_for_badge
        field.'''

        # Step 1: Create a project with an icon
        p = mysite.search.models.Project()
        image_data = open(mysite.account.tests.photo('static/sample-photo.png')).read()
        p.icon_raw.save('', ContentFile(image_data))
        p.save()

        # Assertion 1: p.icon_smaller_for_badge is false (since not scaled yet)
        self.assertFalse(p.icon_smaller_for_badge)

        # Step 2: Call the scaling method
        p.update_scaled_icons_from_self_icon()
        p.save()

        # Assertion 2: Verify that it is now a true value
        self.assert_(p.icon_smaller_for_badge, 
                     "Expected p.icon_smaller_for_badge to be a true value.")

        # Assertion 3: Verify that it has the right width
        self.assertEqual(p.icon_smaller_for_badge.width, 40,
                         "Expected p.icon_smaller_for_badge to be 40 pixels wide.")

    def test_short_icon_is_scaled_correctly(self):
        '''Sometimes icons are rectangular and more wide than long. These icons shouldn't be trammeled into a square, but scaled respectfully of their original ratios.'''
        # Step 1: Create a project with an icon
        p = mysite.search.models.Project()

        # account.tests.photo finds the right path.
        image_data = open(mysite.account.tests.photo(
            'static/images/icons/test-project-icon-64px-by-18px.png')).read()
        p.icon_raw.save('', ContentFile(image_data))
        p.save()

        # Assertion 1: p.icon_smaller_for_badge is false (since not scaled yet)
        self.assertFalse(p.icon_smaller_for_badge)

        # Step 2: Call the scaling method
        p.update_scaled_icons_from_self_icon()
        p.save()

        # Assertion 2: Verify that it is now a true value
        self.assert_(p.icon_smaller_for_badge, 
                     "Expected p.icon_smaller_for_badge to be a true value.")

        # Assertion 3: Verify that it has the right width
        self.assertEqual(p.icon_smaller_for_badge.width, 40,
                         "Expected p.icon_smaller_for_badge to be 40 pixels wide.")

        # Assertion 3: Verify that it has the right height
        # If we want to scale exactly we'll get 11.25 pixels, which rounds to 11.
        self.assertEqual(p.icon_smaller_for_badge.height, 11)

class SearchOnFullWords(SearchTest):
    def test_find_perl_not_properly(self):
        project = Project.create_dummy()
        properly_bug = Bug.create_dummy(description='properly')
        perl_bug = Bug.create_dummy(description='perl')
        self.assertEqual(Bug.all_bugs.all().count(), 2)
        results = mysite.search.controllers.Query(
                terms=['perl']).get_bugs_unordered()
        self.assertEqual(list(results), [perl_bug])

class SearchTemplateDecodesQueryString(SearchTest):
    def test_facets_appear_in_search_template_context(self):
        response = self.client.get('/search/', {'language': 'Python'})
        expected_facets = { 'language': 'Python' }
        self.assertEqual(response.context['query'].facets, expected_facets)

class FacetsFilterResults(SearchTest):
    def test_facets_filter_results(self):
        facets = {'language': 'Python'}

        # Those facets should pick up this bug:
        python_project = Project.create_dummy(language='Python')
        python_bug = Bug.create_dummy(project=python_project)

        # But not this bug
        not_python_project = Project.create_dummy(language='Nohtyp')
        not_python_bug = Bug.create_dummy(project=not_python_project)

        results = mysite.search.controllers.Query(
                terms=[], facets=facets).get_bugs_unordered()
        self.assertEqual(list(results), [python_bug])

class QueryGetPossibleFacets(SearchTest):
    """Ask a query, what facets are you going to show on the left?
    E.g., search for gtk, it says C, 541."""

    def test_get_possible_facets(self):
        project1 = Project.create_dummy(language='c')
        project2 = Project.create_dummy(language='d')
        project3 = Project.create_dummy(language='e')
        Bug.create_dummy(project=project1, description='bug', good_for_newcomers=True)
        Bug.create_dummy(project=project2, description='bug')
        Bug.create_dummy(project=project3, description='bAg')
        query = mysite.search.controllers.Query(
                terms=['bug'],
                terms_string='bug',
                facets={'language': 'c'}) # active facets
        possible_facets = query.get_possible_facets()
        self.assert_(
                possible_facets['language']['values'],
                [
                    { 'name': 'all', 'count': 2 },
                    { 'name': 'c', 'count': 1 },
                    { 'name': 'd', 'count': 1 },
                    # not e
                    ]
                    )
        self.assert_(
                possible_facets['toughness']['values'],
                [
                    { 'name': 'all', 'count': 2 },
                    { 'name': 'bitesize', 'count': 1 },
                    ]
                    )

#class OneFacetDoesntLimitAnother

# vim: set nu ai et ts=4 sw=4 columns=100:
