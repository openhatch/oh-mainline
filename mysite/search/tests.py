from mysite.base.tests import make_twill_url, TwillTests
import mysite.base.unicode_sanity

import mysite.account.tests
from mysite.profile.models import Person
import mysite.profile.models
import mysite.search.controllers
from mysite.search.models import Project, Bug, HitCountCache, \
        ProjectInvolvementQuestion, Answer, BugAlert
from mysite.search import views
import datetime
import mysite.project.views

import simplejson
import mock
from twill import commands as tc

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from django.db.models import Q

import MySQLdb

class SearchTest(TwillTests):

    def search_via_twill(self, query=None):
        search_url = "http://openhatch.org/search/"
        if query:
            search_url += '?q=%s' % query
        tc.go(make_twill_url(search_url))

    def search_via_client(self, query=None):
        search_url = "/search/"
        return self.client.get(search_url, {u'q': query})

    def compare_lists(self, one, two):
        self.assertEqual(len(one), len(two))
        self.assertEqual(set(one), set(two))

    def compare_lists_of_dicts(self, one, two, sort_key=None):

        if sort_key is not None:
            sort_fn = lambda thing: thing[sort_key]
        else:
            sort_fn = None

        sorted_one = sorted(one, key=sort_fn)
        sorted_two = sorted(two, key=sort_fn)
        for k in range(len(sorted_one)):
            try:
                self.assertEqual(sorted_one[k], sorted_two[k])
            except AssertionError:
                import sys
                print >> sys.stderr, sorted_one
                print >> sys.stderr, sorted_two
                raise
        for k in range(len(sorted_two)):
            try:
                self.assertEqual(sorted_one[k], sorted_two[k])
            except AssertionError:
                import sys
                print >> sys.stderr, sorted_one
                print >> sys.stderr, sorted_two
                raise

class AutoCompleteTests(SearchTest):
    """
    Test whether the autocomplete can handle
     - a field-specific query
     -l a non-field-specific (fulltext) query
    """

    def setUp(self):
        SearchTest.setUp(self)
        self.project_chat = Project.create_dummy(name=u'ComicChat', language=u'C++')
        self.project_kazaa = Project.create_dummy(name=u'Kazaa', language=u'Vogon')
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
        suggestions = views.get_autocompletion_suggestions(u'')
        self.assert_("lang:Vogon" in suggestions)

    def testSuggestForAllFields(self):
        c_suggestions = views.get_autocompletion_suggestions(u'C')
        self.assert_(u'lang:C++' in c_suggestions)
        self.assert_(u'project:ComicChat' in c_suggestions)

    def testQueryNotFieldSpecificFindProject(self):
        c_suggestions = views.get_autocompletion_suggestions(u'Comi')
        self.assert_(u'project:ComicChat' in c_suggestions)

    def testQueryFieldSpecific(self):
        lang_C_suggestions = views.get_autocompletion_suggestions(
                u'lang:C')
        self.assert_(u'lang:C++' in lang_C_suggestions)
        self.assert_(u'lang:Python' not in lang_C_suggestions)
        self.assert_(u'project:ComicChat' not in lang_C_suggestions)

    def testSuggestsCorrectStringsFormattedForJQueryAutocompletePlugin(self):
        suggestions_list = views.get_autocompletion_suggestions(u'')
        suggestions_string = views.list_to_jquery_autocompletion_format(
                suggestions_list)
        suggestions_list_reconstructed = suggestions_string.split("\n")
        self.assert_("project:ComicChat" in suggestions_list_reconstructed)
        self.assert_("lang:Vogon" in suggestions_list_reconstructed)
        self.assert_("lang:C++" in suggestions_list_reconstructed)

    def testSuggestsSomethingOverHttp(self):
        response = self.client.get( u'/search/get_suggestions', {u'q': u'C'})
        self.assertContains(response, "project:ComicChat\nlang:C++")

    def testSuggesterFailsOnEmptyString(self):
        response = self.client.get( u'/search/get_suggestions', {u'q': u''})
        self.assertEquals(response.status_code, 500)

    def testSuggesterFailsWithImproperQueryString(self):
        response = self.client.get( u'/search/get_suggestions', {})
        self.assertEquals(response.status_code, 500)

class SearchResultsSpecificBugs(SearchTest):
    fixtures = ['short_list_of_bugs.json']

    def setUp(self):
        SearchTest.setUp(self)

        query = u'PYTHON'

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
        response = self.client.get(u'/search/', {u'q': u'python'})
        returned_bugs = response.context[0][u'bunch_of_bugs']
        for cf in self.canonical_filters:
            self.failUnless(Bug.all_bugs.filter(cf)[0] in returned_bugs,
                    "Search engine did not correctly use the filter %s" % cf)

        for bug in Bug.all_bugs.filter(self.no_canonical_filters()):
            self.failIf(bug in returned_bugs, "Search engine returned a false positive: %s." % bug)

    def test_search_two_queries(self):

        title_of_bug_to_include = u'An interesting title'
        title_of_bug_to_exclude = "This shouldn't be in the results for [pyt*hon 'An interesting description']."

        # If either of these bugs aren't there, then this test won't work properly.
        self.assert_(len(list(Bug.all_bugs.filter(title=title_of_bug_to_include))) == 1)
        self.assert_(len(list(Bug.all_bugs.filter(title=title_of_bug_to_exclude))) == 1)

        response = self.client.get(u'/search/',
                                   {u'q': u'python "An interesting description"'})

        included_the_right_bug = False
        excluded_the_wrong_bug = True
        for bug in response.context[0][u'bunch_of_bugs']:
            if bug.title == title_of_bug_to_include:
                included_the_right_bug = True
            if bug.title == title_of_bug_to_exclude:
                excluded_the_wrong_bug = False

        self.assert_(included_the_right_bug)
        self.assert_(excluded_the_wrong_bug)

class TestThatQueryTokenizesRespectingQuotationMarks(TwillTests):
    def test(self):
        difficult = "With spaces (and parens)"
        query = mysite.search.controllers.Query.create_from_GET_data({u'q': u'"%s"' % difficult})
        self.assertEqual(query.terms, [difficult])
        # Make there be a bug to find
        project = Project.create_dummy(name=difficult)
        Bug.create_dummy(project=project)
        # How many bugs?
        num_bugs = query.get_bugs_unordered().count()
        self.assertEqual(num_bugs, 1)

class SearchResults(TwillTests):
    fixtures = [u'bugs-for-two-projects.json']

    def test_query_object_is_false_when_no_terms_or_facets(self):
        query = mysite.search.controllers.Query.create_from_GET_data({})
        self.assertFalse(query)

    def test_show_no_bugs_if_no_query(self):
        # Call up search page with no query.
        response = self.client.get(u'/search/')

        # The variable u'bunch_of_bugs', passed to the template, is a blank list.
        self.assertEqual(response.context[0][u'bunch_of_bugs'], [])

    def test_json_view(self):
        tc.go(make_twill_url(u'http://openhatch.org/search/?format=json&jsoncallback=callback&q=python'))
        response = tc.show()
        self.assert_(response.startswith(u'callback'))
        json_string_with_parens = response.split(u'callback', 1)[1]
        self.assert_(json_string_with_parens[0] == u'(')
        self.assert_(json_string_with_parens[-1] == u')')
        json_string = json_string_with_parens[1:-1]
        objects = simplejson.loads(json_string)
        self.assert_(u'pk' in objects[0][u'bugs'][0])

    def testPagination(self):
        url = u'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv(u'search_opps', u'q', u'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  u'Exaile').order_by(u'-last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

        # Hit the next button
        tc.follow(u'Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  u'Exaile').order_by(u'-last_touched')[10:20]

        for bug in bugs:
            tc.find(bug.description)

    def testPaginationAndChangingSearchQuery(self):

        url = u'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv(u'search_opps', u'q', u'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  u'Exaile').order_by(u'-last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

        # Hit the next button
        tc.follow(u'Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  u'Exaile').order_by(u'-last_touched')[10:20]

        for bug in bugs:
            tc.find(bug.description)

        # Now, change the query - do we stay that paginated?
        tc.fv(u'search_opps', u'q', u'c#')
        tc.submit()

        # Grab descriptions of first 10 GNOME-Do bugs
        bugs = Bug.all_bugs.filter(project__name=
                                  u'GNOME-Do').order_by(
            u'-last_touched')[:10]

        for bug in bugs:
            tc.find(bug.description)

class Recommend(SearchTest):
    fixtures = ['user-paulproteus.json',
            'person-paulproteus.json',
            'cchost-data-imported-from-ohloh.json',
            'bugs-for-two-projects.json',
            'extra-fake-cchost-related-citations.json',
            'tags']

    # FIXME: Add a 'recommend_these_in_bug_search' field to TagType
    # Use that to exclude 'will never understand' tags from recommended search terms.
    @mock.patch('mysite.search.controllers.Query.get_or_create_cached_hit_count')
    def test_get_recommended_search_terms_for_user(self, mocked_hit_counter):

        # Make all the search terms appear to return results, so
        # that none are excluded when we try to trim away
        # the terms that don't return results.
        # We test this functionality separately in
        # search.tests.DontRecommendFutileSearchTerms.
        mocked_hit_counter.return_value = 1

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

    # Use that to exclude 'will never understand' tags from recommended search terms.
    @mock.patch('mysite.search.models.HitCountCache.objects.get_or_create')
    def test_recomender_raises_integrity_error(self, mocked_get_or_create):
        mocked_get_or_create.side_effect = MySQLdb.IntegrityError()
        person = Person.objects.get(user__username='paulproteus')
        person.get_recommended_search_terms()

    # FIXME: Include recommendations from tags.

    @mock.patch('mysite.search.controllers.Query.get_or_create_cached_hit_count')
    def test_search_page_context_includes_recommendations(self, mocked_hit_counter):

        # Make all the search terms appear to return results, so
        # that none are excluded when we try to trim away
        # the terms that don't return results.
        # We test this functionality separately in
        # search.tests.DontRecommendFutileSearchTerms.
        mocked_hit_counter.return_value = 1

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

        expected_tags = sum(source2terms.values(), [])
        self.compare_lists(expected_tags, tags_in_template)

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

class SplitIntoTerms(TestCase):
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
        p = mysite.search.models.Project.create_dummy()
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
        p = mysite.search.models.Project.create_dummy()

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
        Project.create_dummy()
        Bug.create_dummy(description='properly')
        perl_bug = Bug.create_dummy(description='perl')
        self.assertEqual(Bug.all_bugs.all().count(), 2)
        results = mysite.search.controllers.Query(
                terms=['perl']).get_bugs_unordered()
        self.assertEqual(list(results), [perl_bug])

class SearchTemplateDecodesQueryString(SearchTest):
    def test_facets_appear_in_search_template_context(self):
        response = self.client.get('/search/', {'language': 'Python'})
        expected_facets = { 'language': 'Python' }
        self.assertEqual(response.context['query'].active_facet_options,
                         expected_facets)

class FacetsFilterResults(SearchTest):
    def test_facets_filter_results(self):
        facets = {u'language': u'Python'}

        # Those facets should pick up this bug:
        python_project = Project.create_dummy(language='Python')
        python_bug = Bug.create_dummy(project=python_project)

        # But not this bug
        not_python_project = Project.create_dummy(language='Nohtyp')
        Bug.create_dummy(project=not_python_project)

        results = mysite.search.controllers.Query(
                terms=[], active_facet_options=facets).get_bugs_unordered()
        self.assertEqual(list(results), [python_bug])

class QueryGetPossibleFacets(SearchTest):
    """Ask a query, what facets are you going to show on the left?
    E.g., search for gtk, it says C (541)."""

    def test_get_possible_facets(self):
        # Create three projects
        project1 = Project.create_dummy(language=u'c')
        project2 = Project.create_dummy(language=u'd')
        project3 = Project.create_dummy(language=u'e')

        # Give each project a bug
        Bug.create_dummy(project=project1, description=u'bug', good_for_newcomers=True)
        Bug.create_dummy(project=project2, description=u'bug')
        Bug.create_dummy(project=project3, description=u'bAg')

        # Search for bugs matching "bug", while constraining to the language C
        query = mysite.search.controllers.Query(
                terms=[u'bug'],
                terms_string=u'bug',
                active_facet_options={u'language': u'c'})
        possible_facets = dict(query.get_possible_facets())

        self.assertEqual(query.get_bugs_unordered().count(), 1)

        # We expect that, language-wise, you should be able to select any of
        # the other languages, or 'deselect' your language constraint.
        self.compare_lists_of_dicts(
                possible_facets[u'language'][u'options'],
                [
                    { u'name': u'c', u'query_string': u'q=bug&language=c',
                        u'is_active': True, u'count': 1 },
                    { u'name': u'd', u'query_string': u'q=bug&language=d',
                        u'is_active': False, u'count': 1 },
                    # e is excluded because its bug (u'bAg') doesn't match the term 'bug'
                    ],
                sort_key=u'name'
                )

        self.compare_lists_of_dicts(
                possible_facets[u'toughness'][u'options'],
                [
                    # There's no 'any' option for toughness unless you've
                    # selected a specific toughness value
                    { u'name': u'bitesize', u'is_active': False,
                        u'query_string': u'q=bug&toughness=bitesize&language=c', u'count': 1 },
                    ],
                sort_key=u'name'
                )

        self.assertEqual(
                possible_facets['language']['the_any_option'],
                { u'name': u'any', u'query_string': u'q=bug&language=',
                    u'is_active': False, u'count': 2 },
                )

    def test_possible_facets_always_includes_active_facet(self):
        # even when active facet has no results.
        c = Project.create_dummy(language=u'c')
        Project.create_dummy(language=u'd')
        Project.create_dummy(language=u'e')
        Bug.create_dummy(project=c, description=u'bug')
        query = mysite.search.controllers.Query.create_from_GET_data(
                {u'q': u'nothing matches this', u'language': u'c'})

        language_options = dict(query.get_possible_facets())['language']['options']
        language_options_named_c = [opt for opt in language_options if opt['name'] == 'c']
        self.assertEqual(len(language_options_named_c), 1)

class SingleTerm(SearchTest):
    """Search for just a single term."""

    def setUp(self):
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language='Python')
        perl_project = Project.create_dummy(language='Perl')
        c_project = Project.create_dummy(language='C')

        # bitesize, matching bug in Python
        Bug.create_dummy(project=python_project, good_for_newcomers=True,
                         description='screensaver')

        # nonbitesize, matching bug in Python
        Bug.create_dummy(project=python_project, good_for_newcomers=False,
                         description='screensaver')

        # nonbitesize, matching bug in Perl
        Bug.create_dummy(project=perl_project, good_for_newcomers=False,
                         description='screensaver')

        # nonbitesize, nonmatching bug in C
        Bug.create_dummy(project=c_project, good_for_newcomers=False,
                         description='toast')

        GET_data = { 'q': 'screensaver' }
        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        self.assertEqual(query.terms, ['screensaver'])
        self.assertFalse(query.active_facet_options) # No facets

        self.output_possible_facets = dict(query.get_possible_facets())

    def test_toughness_facet(self):
        # What options do we expect?
        toughness_option_bitesize = {'name': 'bitesize', 'count': 1,
                'is_active': False,
                'query_string': 'q=screensaver&toughness=bitesize'}
        toughness_option_any = {'name': 'any', 'count': 3,
                'is_active': True,
                'query_string': 'q=screensaver&toughness='}
        expected_toughness_facet_options = [toughness_option_bitesize]

        self.assertEqual(
                self.output_possible_facets['toughness']['options'],
                expected_toughness_facet_options
                )
        self.assertEqual(
                self.output_possible_facets['toughness']['the_any_option'],
                toughness_option_any
                )

    def test_languages_facet(self):
        # What options do we expect?
        languages_option_python = {'name': 'Python', 'count': 2,
                'is_active': False,
                'query_string': 'q=screensaver&language=Python'}
        languages_option_perl = {'name': 'Perl', 'count': 1,
                'is_active': False,
                'query_string': 'q=screensaver&language=Perl'}
        languages_option_any = {'name': 'any', 'count': 3,
                'is_active': True,
                'query_string': 'q=screensaver&language='}
        expected_languages_facet_options = [
                languages_option_python,
                languages_option_perl,
                ]

        self.compare_lists_of_dicts(
                self.output_possible_facets['language']['options'],
                expected_languages_facet_options
                )

        self.assertEqual(
                self.output_possible_facets['language']['the_any_option'],
                languages_option_any)

class SingleFacetOption(SearchTest):
    """Browse bugs matching a single facet option."""

    def setUp(self):
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language='Python')
        perl_project = Project.create_dummy(language='Perl')
        c_project = Project.create_dummy(language='C')

        # bitesize, matching bug in Python
        Bug.create_dummy(project=python_project, good_for_newcomers=True,
                         description='screensaver')

        # nonbitesize, matching bug in Python
        Bug.create_dummy(project=python_project, good_for_newcomers=False,
                         description='screensaver')

        # nonbitesize, matching bug in Perl
        Bug.create_dummy(project=perl_project, good_for_newcomers=False,
                         description='screensaver')

        # nonbitesize, nonmatching bug in C
        Bug.create_dummy(project=c_project, good_for_newcomers=False,
                         description='toast')

        GET_data = { u'language': u'Python' }
        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        self.assertFalse(query.terms) # No terms
        self.assertEqual(query.active_facet_options, {u'language': u'Python'})

        self.output_possible_facets = dict(query.get_possible_facets())

    def test_toughness_facet(self):
        # What options do we expect?
        toughness_option_bitesize = {u'name': u'bitesize', u'count': 1,
                u'is_active': False,
                u'query_string': u'q=&toughness=bitesize&language=Python'}
        toughness_option_any = {u'name': u'any', u'count': 2,
                u'is_active': True,
                u'query_string': u'q=&toughness=&language=Python'}
        expected_toughness_facet_options = [toughness_option_bitesize]

        self.compare_lists_of_dicts(
                self.output_possible_facets[u'toughness'][u'options'],
                expected_toughness_facet_options
                )
        self.assertEqual(
                self.output_possible_facets[u'toughness'][u'the_any_option'],
                toughness_option_any
                )

    def test_languages_facet(self):
        # What options do we expect?
        languages_option_python = {u'name': u'Python', u'count': 2,
                u'is_active': True,
                u'query_string': u'q=&language=Python'}
        languages_option_perl = {u'name': u'Perl', u'count': 1,
                u'is_active': False,
                u'query_string': u'q=&language=Perl'}
        languages_option_c = {u'name': u'C', u'count': 1,
                u'is_active': False,
                u'query_string': u'q=&language=C'}
        languages_option_any = {u'name': u'any', u'count': 4,
                u'is_active': False,
                u'query_string': u'q=&language='}
        expected_languages_facet_options = [
                languages_option_python,
                languages_option_perl,
                languages_option_c,
                ]

        self.compare_lists_of_dicts(
                self.output_possible_facets[u'language'][u'options'],
                expected_languages_facet_options
                )

        self.assertEqual(
                self.output_possible_facets[u'language'][u'the_any_option'],
                languages_option_any,
                )

class QueryGetToughnessFacetOptions(SearchTest):
    def test_get_toughness_facet_options(self):
        # We create three "bitesize" bugs, but constrain the Query so
        # that we're only looking at bugs in Python.

        # Since only two of the bitesize bugs are in Python (one is 
        # in a project whose language is Perl), we expect only 1 bitesize
        # bug to show up, and 2 total bugs.
        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')

        Bug.create_dummy(project=python_project, good_for_newcomers=True)
        Bug.create_dummy(project=python_project, good_for_newcomers=False)
        Bug.create_dummy(project=perl_project, good_for_newcomers=True)

        query = mysite.search.controllers.Query(
                active_facet_options={u'language': u'Python'},
                terms_string=u'')
        output = query.get_facet_options(u'toughness', [u'bitesize', u''])
        bitesize_dict = [d for d in output if d[u'name'] == u'bitesize'][0]
        all_dict = [d for d in output if d[u'name'] == u'any'][0]
        self.assertEqual(bitesize_dict[u'count'], 1)
        self.assertEqual(all_dict[u'count'], 2)

    def test_get_toughness_facet_options_with_terms(self):

        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')

        Bug.create_dummy(project=python_project, good_for_newcomers=True,
                         description=u'a')

        Bug.create_dummy(project=python_project, good_for_newcomers=False,
                         description=u'a')

        Bug.create_dummy(project=perl_project, good_for_newcomers=True,
                         description=u'b')

        GET_data = {u'q': u'a'}
        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        output = query.get_facet_options(u'toughness', [u'bitesize', u''])
        bitesize_dict = [d for d in output if d[u'name'] == u'bitesize'][0]
        all_dict = [d for d in output if d[u'name'] == u'any'][0]
        self.assertEqual(bitesize_dict[u'count'], 1)
        self.assertEqual(all_dict[u'count'], 2)

class QueryGetPossibleLanguageFacetOptionNames(SearchTest):

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def setUp(self, do_nothing):
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')
        c_project = Project.create_dummy(language=u'C')
        unknown_project = Project.create_dummy(language=u'')

        Bug.create_dummy(project=python_project, title=u'a')
        Bug.create_dummy(project=perl_project, title=u'a')
        Bug.create_dummy(project=c_project, title=u'b')
        Bug.create_dummy(project=unknown_project, title=u'unknowable')

    def test_with_term(self):
        # In the setUp we create three bugs, but only two of them would match
        # a search for 'a'. They are in two different languages, so let's make
        # sure that we show only those two languages.
        GET_data = {u'q': u'a'}

        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        language_names = query.get_language_names()
        self.assertEqual(
                sorted(language_names),
                sorted([u'Python', u'Perl']))

    def test_with_active_language_facet(self):
        # In the setUp we create bugs in three languages.
        # Here, we verify that the get_language_names() method correctly returns
        # all three languages, even though the GET data shows that we are
        # browsing by language.

        GET_data = {u'language': u'Python'}

        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        language_names = query.get_language_names()
        self.assertEqual(
                sorted(language_names),
                sorted([u'Python', u'Perl', u'C', u'Unknown']))

    def test_with_language_as_unknown(self):
        # In the setUp we create bugs in three languages.
        # Here, we verify that the get_language_names() method correctly returns
        # all three languages, even though the GET data shows that we are
        # browsing by language.

        GET_data = {u'language': u'Unknown'}

        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        language_names = query.get_language_names()
        self.assertEqual(
                sorted(language_names),
                sorted([u'Python', u'Perl', u'C', u'Unknown']))

    def test_with_language_as_unknown_and_query(self):
        # In the setUp we create bugs in three languages.
        # Here, we verify that the get_language_names() method correctly returns
        # all three languages, even though the GET data shows that we are
        # browsing by language.

        GET_data = {u'language': u'Unknown', u'q': u'unknowable'}

        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        match_count = query.get_bugs_unordered().count()

        self.assertEqual(match_count, 1)

class QueryGetPossibleProjectFacetOptions(SearchTest):

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def setUp(self, do_nothing):
        SearchTest.setUp(self)
        projects = [
                Project.create_dummy(name=u'Miro'),
                Project.create_dummy(name=u'Dali'),
                Project.create_dummy(name=u'Magritte')
                ]
        for p in projects:
            Bug.create_dummy(project=p)

    def test_select_a_project_and_see_other_project_options(self):
        GET_data = {u'project': u'Miro'}
        query = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        possible_project_names = [x['name'] for x in dict(query.get_possible_facets())['project']['options']]
        self.assertEqual(
                sorted(possible_project_names),
                sorted(list(Project.objects.values_list('name', flat=True))))

class QueryContributionType(SearchTest):

    def setUp(self):
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')
        c_project = Project.create_dummy(language=u'C')

        Bug.create_dummy(project=python_project, title=u'a')
        Bug.create_dummy(project=perl_project, title=u'a',
                         concerns_just_documentation=True)
        Bug.create_dummy(project=c_project, title=u'b')

    def test_contribution_type_is_an_available_facet(self):
        GET_data = {}
        starting_query = mysite.search.controllers.Query.create_from_GET_data(
            GET_data)
        self.assert_(u'contribution type' in dict(starting_query.get_possible_facets()))

    def test_contribution_type_options_are_reasonable(self):
        GET_data = {}
        starting_query = mysite.search.controllers.Query.create_from_GET_data(
            GET_data)
        cto = starting_query.get_facet_options(u'contribution_type',
                                               [u'documentation'])
        documentation_one, = [k for k in cto if k[u'name'] == u'documentation']
        any_one = starting_query.get_facet_options(u'contribution_type', [u''])[0]
        self.assertEqual(documentation_one[u'count'], 1)
        self.assertEqual(any_one[u'count'], 3)

class QueryProject(SearchTest):

    def setUp(self):
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language=u'Python',
                                              name='thingamajig')
        c_project = Project.create_dummy(language=u'C',
                                         name='thingamabob')

        Bug.create_dummy(project=python_project, title=u'a')
        Bug.create_dummy(project=python_project, title=u'a',
                         concerns_just_documentation=True)
        Bug.create_dummy(project=c_project, title=u'b')

    def test_project_is_an_available_facet(self):
        GET_data = {}
        starting_query = mysite.search.controllers.Query.create_from_GET_data(
            GET_data)
        self.assert_(u'project' in dict(starting_query.get_possible_facets()))

    def test_contribution_type_options_are_reasonable(self):
        GET_data = {}
        starting_query = mysite.search.controllers.Query.create_from_GET_data(
            GET_data)
        cto = starting_query.get_facet_options(u'project',
                                               [u'thingamajig',
                                                u'thingamabob' ])
        jig_ones, = [k for k in cto if k[u'name'] == u'thingamajig']
        any_one = starting_query.get_facet_options(u'project', [u''])[0]
        self.assertEqual(jig_ones[u'count'], 2)
        self.assertEqual(any_one[u'count'], 3)

class QueryStringCaseInsensitive(SearchTest):

    def test_Language(self):
        """Do we redirect queries that use non-lowercase facet keys to pages
        that use lowercase facet keys?"""
        redirects = self.client.get(u'/search/',
                {u'LANguaGE': u'pytHon'}, follow=True).redirect_chain
        self.assertEqual(redirects, [(u'http://testserver/search/?language=pytHon', 302)])

class HashQueryData(SearchTest):

    def test_queries_with_identical_data_hash_alike(self):
        GET_data = {u'q': u'socialguides', u'language': u'looxii'}
        one = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        two = mysite.search.controllers.Query.create_from_GET_data(GET_data)
        self.assertEqual(one.get_sha1(), two.get_sha1())

    def test_queries_with_equiv_data_expressed_differently_hash_alike(self):
        GET_data_1 = {u'q': u'socialguides zetapage', u'language': u'looxii'}
        GET_data_2 = {u'q': u'zetapage socialguides', u'language': u'looxii'}
        one = mysite.search.controllers.Query.create_from_GET_data(GET_data_1)
        two = mysite.search.controllers.Query.create_from_GET_data(GET_data_2)
        self.assertEqual(one.get_sha1(), two.get_sha1())

    def test_queries_with_different_data_hash_differently(self):
        GET_data_1 = {u'q': u'socialguides zetapage', u'language': u'looxii'}
        GET_data_2 = {u'q': u'socialguides ninjapost', u'language': u'looxii'}
        one = mysite.search.controllers.Query.create_from_GET_data(GET_data_1)
        two = mysite.search.controllers.Query.create_from_GET_data(GET_data_2)
        self.assertNotEqual(one.get_sha1(), two.get_sha1())

    # How on earth do we test for collisions?

class QueryGrabHitCount(SearchTest):

    def test_eventhive_grab_hitcount_once_stored(self):

        data = {u'q': u'eventhive', u'language': u'shoutNOW'}
        query = mysite.search.controllers.Query.create_from_GET_data(data)
        stored_hit_count = 10
        HitCountCache.objects.create(
                hashed_query=query.get_sha1(),
                hit_count=stored_hit_count)
        self.assertEqual(query.get_or_create_cached_hit_count(), stored_hit_count)

    def test_shoutnow_cache_hitcount_on_grab(self):

        project = Project.create_dummy(language=u'shoutNOW')

        Bug.create_dummy(project=project)
        data = {u'language': u'shoutNOW'}
        query = mysite.search.controllers.Query.create_from_GET_data(data)

        expected_hit_count = 1
        self.assertEqual(query.get_or_create_cached_hit_count(), expected_hit_count)

        hcc = HitCountCache.objects.get(hashed_query=query.get_sha1())
        self.assertEqual(hcc.hit_count, expected_hit_count)

class ClearCacheWhenBugsChange(SearchTest):

    def test_cached_cleared_after_bug_save_or_delete(self):
        data = {u'language': u'shoutNOW'}
        query = mysite.search.controllers.Query.create_from_GET_data(data)

        # Cache entry created after hit count retrieval
        query.get_or_create_cached_hit_count()
        self.assert_(HitCountCache.objects.all())

        # Cache cleared after bug save
        project = Project.create_dummy(language=u'shoutNOW')
        bug = Bug.create_dummy(project=project)
        self.assertFalse(HitCountCache.objects.all())

        # Cache entry created after hit count retrieval
        query.get_or_create_cached_hit_count()
        self.assert_(HitCountCache.objects.all())

        # Cache cleared after bug deletion
        bug.delete()
        self.assertFalse(HitCountCache.objects.all())

class DontRecommendFutileSearchTerms(TwillTests):

    def test_removal_of_futile_terms(self):
        mysite.search.models.Bug.create_dummy_with_project(description=u'useful')
        self.assertEqual(
                Person.only_terms_with_results([u'useful', u'futile']),
                [u'useful'])


class PublicizeBugTrackerIndex(SearchTest):

    def setUp(self):
        SearchTest.setUp(self)
        self.search_page_response = self.client.get(reverse(mysite.search.views.fetch_bugs))
        self.bug_tracker_count = mysite.search.controllers.get_project_count()

    def test_search_template_contains_bug_tracker_count(self):
        self.assertEqual(
                self.search_page_response.context[0][u'project_count'],
                self.bug_tracker_count)

class TestPotentialMentors(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test(self):
        '''Create a Banshee mentor who can do C#
        and a separate C# mentor, and verify that Banshee thinks it has
        two potential mentors.'''

        banshee = Project.create_dummy(name='Banshee', language='C#')
        can_mentor, _ = mysite.profile.models.TagType.objects.get_or_create(name=u'can_mentor')

        willing_to_mentor_banshee, _ = mysite.profile.models.Tag.objects.get_or_create(
            tag_type=can_mentor,
            text=u'Banshee')

        willing_to_mentor_c_sharp, _ = mysite.profile.models.Tag.objects.get_or_create(
            tag_type=can_mentor,
            text=u'C#')

        link = mysite.profile.models.Link_Person_Tag(
            person=Person.objects.get(user__username=u'paulproteus'),
            tag=willing_to_mentor_banshee)
        link.save()

        link = mysite.profile.models.Link_Person_Tag(
            person=Person.objects.get(user__username=u'paulproteus'),
            tag=willing_to_mentor_c_sharp)
        link.save()

        link = mysite.profile.models.Link_Person_Tag(
            person=Person.objects.get(user__username=u'barry'),
            tag=willing_to_mentor_c_sharp)
        link.save()

        banshee_mentors = banshee.potential_mentors
        self.assertEqual(len(banshee_mentors), 2)

class SuggestAlertOnLastResultsPage(TwillTests):
    fixtures = ['user-paulproteus']

    def exercise_alert(self, anonymous=True):
        """The 'anonymous' parameter allows the alert functionality to be
        tested for anonymous and logged-in users."""

        if not anonymous:
            self.login_with_twill()

        # Create some dummy data
        p = Project.create_dummy(language='ruby')
        # 15 bugs matching 'ruby'
        for i in range(15):
            b = Bug.create_dummy(description='ruby')
            b.project = p
            b.save()

        # Visit the first page of a vol. opp. search results page.
        opps_view = mysite.search.views.fetch_bugs
        query = u'ruby'
        opps_query_string = { u'q': query, u'start': 1, u'end': 10}
        opps_url = make_twill_url('http://openhatch.org'+reverse(opps_view) + '?' + mysite.base.unicode_sanity.urlencode(opps_query_string))
        tc.go(opps_url)

        # Make sure we *don't* have the comment that flags this as a page that offers an email alert subscription button
        tc.notfind("this page should offer a link to sign up for an email alert")

        # Visit the last page of results
        GET = { u'q': query, u'start': 11, u'end': 20}
        query_string = mysite.base.unicode_sanity.urlencode(GET)
        opps_url = make_twill_url('http://openhatch.org'+reverse(opps_view) + '?' + query_string)
        tc.go(opps_url)
        # make sure we /do/ have the comment that flags this as a page that
        # offers an email alert subscription button
        tc.find("this page should offer a link to sign up for an email alert")

        if not anonymous:
            # if the user is logged in, make sure that we have autopopulated
            # the form with her email address
            tc.find(User.objects.get(username='paulproteus').email)

        # Submit the 'alert' form.
        email_address = 'yetanother@ema.il'
        tc.fv('alert', 'email', email_address)
        tc.submit()

        if anonymous:
            client = self.client
        else:
            client = self.login_with_client()


        alert_data_in_form = {
                'query_string': query_string,
                'how_many_bugs_at_time_of_request': Bug.open_ones.filter(project=p).count(),
                'email': email_address,
                }
        # Twill fails here for some reason, so let's continue the journey with
        # Django's built-in testing sweeeet
        response = client.post(reverse(mysite.search.views.subscribe_to_bug_alert_do), alert_data_in_form)

        # This response should be a HTTP redirect instruction
        self.assertEqual(response.status_code, 302)
        redirect_target_url = response._headers['location'][1]
        self.assert_(query_string in redirect_target_url)

        # The page redirects to the old kk
        response = client.get(redirect_target_url)
        self.assertContains(response, "this page should confirm that an email alert has been registered")

        # At this point, make sure that the DB contains a record of
        #     * What the query was.
        #     * When the request was made.
        #     * How many bugs were returned by the query at the time of request.

        # There should be only one alert
        all_alerts = BugAlert.objects.all()
        self.assertEqual(all_alerts.count(), 1)
        alert_record = all_alerts[0]
        self.assert_(alert_record)

        assert_that_record_has_this_data = alert_data_in_form

        # For the logged-in user, also check that the record contains the
        # identity of the user who made the alert request.

        if not anonymous:
            assert_that_record_has_this_data['user'] = User.objects.get(username='paulproteus')

        for key, expected_value in assert_that_record_has_this_data.items():
            self.assertEqual(alert_record.__getattribute__(key), expected_value,
                    'alert.%s = %s not (expected) %s' % (key, alert_record.__getattribute__(key), expected_value))

    # run the above test for our two use cases: logged in and not
    def test_alert_anon(self):
        self.exercise_alert(anonymous=True)
    def test_alert_logged_in(self):
        self.exercise_alert(anonymous=False)


class DeleteAnswer(TwillTests):
    fixtures = ['user-paulproteus']

    def test_delete_paragraph_answer(self):
        # create dummy question
        p = Project.create_dummy(name='Ubuntu')
        question__pk = 0
        q = ProjectInvolvementQuestion.create_dummy(pk=question__pk, is_bug_style=False)
        # create our dummy answer
        a = Answer.create_dummy(text='i am saying thigns', question=q, project=p, author=User.objects.get(username='paulproteus'))
        # delete our answer
        POST_data = {
                'answer__pk': a.pk,
                }
        POST_handler = reverse(mysite.project.views.delete_paragraph_answer_do)
        response = self.login_with_client().post(POST_handler, POST_data)
        # go back to the project page and make sure that our answer isn't there anymore
        project_url = p.get_url()
        self.assertRedirects(response, project_url)
        project_page = self.login_with_client().get(project_url)

        self.assertNotContains(project_page, a.text)

        # and make sure our answer isn't in the db anymore
        self.assertEqual(Answer.objects.filter(pk=a.pk).count(), 0)

    def test_delete_bug_answer(self):
        # create dummy question
        p = Project.create_dummy(name='Ubuntu')
        # it's important that this pk correspond to the pk of an actual
        # bug_style question, as specified in our view otherwise, we'll
        # get_or_create will try to create, but it won't be able to because of
        # a unique key error
        question__pk = 2
        q = ProjectInvolvementQuestion.create_dummy(pk=question__pk, is_bug_style=True)
        # create our dummy answer
        a = Answer.create_dummy(title='i want this bug fixed', text='for these reasons',question=q, project=p, author=User.objects.get(username='paulproteus'))
        # delete our answer
        POST_data = {
                'answer__pk': a.pk,
                }
        POST_handler = reverse(mysite.project.views.delete_paragraph_answer_do)
        response = self.login_with_client().post(POST_handler, POST_data)
        # go back to the project page and make sure that our answer isn't there anymore
        project_url = p.get_url()
        self.assertRedirects(response, project_url)
        project_page = self.login_with_client().get(project_url)

        self.assertNotContains(project_page, a.title)

        # and make sure our answer isn't in the db anymore
        self.assertEqual(Answer.objects.filter(pk=a.pk).count(), 0)



class CreateBugAnswer(TwillTests):
    fixtures = ['user-paulproteus']
    def test_create_bug_answer(self):
        # go to the project page
        p = Project.create_dummy(name='Ubuntu')
        question__pk = 1
        question = ProjectInvolvementQuestion.create_dummy(
                key_string='non_code_participation', is_bug_style=True)
        question.save()
        title = 'omfg i wish this bug would go away'
        text = 'kthxbai'
        POST_data = {
                'project__pk': p.pk,
                'question__pk': str(question__pk),
                'answer__title': title,
                'answer__text': text
                }
        POST_handler = reverse(mysite.project.views.create_answer_do)
        response = self.login_with_client().post(POST_handler, POST_data)

        # try to get the BugAnswer which we just submitted from the database
        our_bug_answer = Answer.objects.get(title=title)

        # make sure it has the right attributes
        self.assertEqual(our_bug_answer.text, text)
        self.assertEqual(our_bug_answer.question.pk, question__pk)
        self.assertEqual(our_bug_answer.project.pk, p.pk)

        project_url = p.get_url()
        self.assertRedirects(response, project_url)

        project_page = self.login_with_client().get(project_url)

        # make sure that our data shows up on the page
        self.assertContains(project_page, title)
        self.assertContains(project_page, text)

class WeTakeOwnershipOfAnswersAtLogin(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_create_answer_but_take_ownership_at_login_time(self):
        session = {}

        # Create the Answer object, but set its User to None
        answer = Answer.create_dummy()
        answer.author = None
        answer.is_published = False
        answer.save()

        # Verify that the Answer object is not available by .objects()
        self.assertFalse(Answer.objects.all())

        # Store the Answer IDs in the session
        mysite.project.controllers.note_in_session_we_control_answer_id(session, answer.id)
        self.assertEqual(session['answer_ids_that_are_ours'], [answer.id])

        # If you want to look at those answers, you can this way:
        stored_answers = mysite.project.controllers.get_unsaved_answers_from_session(session)
        self.assertEqual([answer.id for answer in stored_answers], [answer.id])

        # Verify that the Answer object is still not available by .objects()
        self.assertFalse(Answer.objects.all())

        # At login time, take ownership of those Answer IDs
        mysite.project.controllers.take_control_of_our_answers(
            User.objects.get(username='paulproteus'), session)

        # And now we own it!
        self.assertEqual(Answer.objects.all().count(), 1)

class CreateAnonymousAnswer(TwillTests):
    fixtures = ['user-paulproteus']

    def test_create_answer_anonymously(self):
        # Steps for this test
        # 1. User fills in the form anonymously
        # 2. We test that the Answer is not yet saved
        # 3. User logs in
        # 4. We test that the Answer is saved

        p = Project.create_dummy(name='Myproject')
        q = ProjectInvolvementQuestion.create_dummy(
                key_string='where_to_start', is_bug_style=False)

        # Do a GET on the project page to prove cookies work.
        self.client.get(p.get_url())

        # POST some text to the answer creation post handler
        answer_text = """Help produce official documentation, share the solution to a problem, or check, proof and test other documents for accuracy."""
        POST_data = {
                'project__pk': p.pk,
                'question__pk': q.pk,
                'answer__text': answer_text,
                    }
        response = self.client.post(reverse(mysite.project.views.create_answer_do), POST_data,
                                    follow=True)
        self.assertEqual(response.redirect_chain,
            [('http://testserver/account/login/?next=%2F%2Bprojects%2FMyproject', 302)])

        # If this were an Ajaxy post handler, we might assert something about
        # the response, like
        #   self.assertEqual(response.content, '1')

        # check that the db contains a record with this text
        try:
            record = Answer.all_even_unowned.get(text=POST_data['answer__text'])
        except Answer.DoesNotExist:
            print "All Answers:", Answer.all_even_unowned.all()
            raise Answer.DoesNotExist
        self.assertEqual(record.project, p)
        self.assertEqual(record.question, q)

        self.assertFalse(Answer.objects.all()) # it's unowned

        # Now, the session will know about the answer, but the answer will not be published.
        # Visit the login page, assert that the page contains the text of the answer.
        response = self.client.get(reverse('oh_login'))
        self.assertContains(response, POST_data['answer__text'])


        # But when the user is logged in and *then* visits the project page
        login_worked = self.client.login(username='paulproteus',
                                         password="paulproteus's unbreakable password")
        self.assert_(login_worked)

        self.client.get(p.get_url())

        # Now, the Answer should have an author whose username is paulproteus
        answer = Answer.objects.get()
        self.assertEqual(answer.text, POST_data['answer__text'])
        self.assertEqual(answer.author.username, 'paulproteus')

        # Finally, go to the project page and make sure that our Answer has appeared
        response = self.client.get(p.get_url())
        self.assertContains(response, answer_text)

class CreateAnswer(TwillTests):
    fixtures = ['user-paulproteus']

    def test_create_answer(self):

        p = Project.create_dummy()
        q = ProjectInvolvementQuestion.create_dummy(
                key_string='where_to_start', is_bug_style=False)

        # POST some text to the answer creation post handler
        POST_data = {
                'project__pk': p.pk,
                'question__pk': q.pk,
                'answer__text': """Help produce official documentation, share \
the solution to a problem, or check, proof and test other documents for \
accuracy.""",
                    }
        self.login_with_client().post(reverse(mysite.project.views.create_answer_do), POST_data)
        # If this were an Ajaxy post handler, we might assert something about
        # the response, like
        #   self.assertEqual(response.content, '1')

        # check that the db contains a record with this text
        try:
            record = Answer.objects.get(text=POST_data['answer__text'])
        except Answer.DoesNotExist:
            print "All Answers:", Answer.objects.all()
            raise Answer.DoesNotExist
        self.assertEqual(record.author, User.objects.get(username='paulproteus'))
        self.assertEqual(record.project, p)
        self.assertEqual(record.question, q)

        # check that the project page now includes this text
        project_page = self.client.get(p.get_url())
        self.assertContains(project_page, POST_data['answer__text'])
        self.assertContains(project_page, record.author.username)

    def test_multiparagraph_answer(self):
        """
        If a multi-paragraph answer is submitted, display it as a
        multi-paragraph answer.
        """
        # go to the project page
        p = Project.create_dummy(name='Ubuntu')
        q = ProjectInvolvementQuestion.create_dummy(
            key_string='where_to_start', is_bug_style=False)
        q.save()
        text = ['This is a multiparagraph answer.',
                'This is the second paragraph.',
                'This is the third paragraph.']
        POST_data = {
                'project__pk': p.pk,
                'question__pk': q.pk,
                'answer__text': "\n".join(text)
                }

        POST_handler = reverse(mysite.project.views.create_answer_do)
        self.login_with_client().post(POST_handler, POST_data)
        project_page = self.login_with_client().get(p.get_url())

        # Django documents publicly that linebreaks replaces one "\n" with "<br />".
        # http://docs.djangoproject.com/en/dev/ref/templates/builtins/#linebreaks
        self.assertContains(project_page, "<br />".join(text))

class TestEpoch(TwillTests):
    def test_on_mark_looks_closed(self):
        # There's no Epoch for bugs yet, right?
        now = mysite.search.models.Epoch.get_for_model(mysite.search.models.Bug)
        self.assertEqual(now, mysite.search.models.Epoch.zero_o_clock)

        # Making a Bug should not bump the Epoch
        p = mysite.search.models.Project.create_dummy()
        b = mysite.search.models.Bug.create_dummy(project=p)

        now = mysite.search.models.Epoch.get_for_model(mysite.search.models.Bug)
        self.assertEqual(now,
                         mysite.search.models.Epoch.zero_o_clock)

        # Setting the bug to looks_closed should bump the Epoch
        b.looks_closed = True
        b.save()

        # Now it's higher, right?
        now = mysite.search.models.Epoch.get_for_model(mysite.search.models.Bug)
        self.assert_(now > mysite.search.models.Epoch.zero_o_clock)

    def test_on_delete(self):
        # There's no Epoch for bugs yet, right?
        now = mysite.search.models.Epoch.get_for_model(mysite.search.models.Bug)
        self.assertEqual(now, mysite.search.models.Epoch.zero_o_clock)

        # Making a Bug should not bump the Epoch
        p = mysite.search.models.Project.create_dummy()
        b = mysite.search.models.Bug.create_dummy(project=p)

        now = mysite.search.models.Epoch.get_for_model(mysite.search.models.Bug)
        self.assertEqual(now,
                         mysite.search.models.Epoch.zero_o_clock)

        # Deleting that Bug should bump the Epoch
        b.delete()
        later = mysite.search.models.Epoch.get_for_model(mysite.search.models.Bug)
        self.assert_(later > now)

class BugKnowsItsFreshness(TestCase):
    def test(self):
        b = mysite.search.models.Bug.create_dummy_with_project()
        b.last_polled = datetime.datetime.now()
        self.assertTrue(b.data_is_more_fresh_than_one_day())
        b.last_polled -= datetime.timedelta(
            days=1, hours=1)
        self.assertFalse(b.data_is_more_fresh_than_one_day())

class WeCanPollSomethingToCheckIfAProjectIconIsLoaded(TestCase):
    def test(self):
        # Create a dummy project
        p = Project.create_dummy()

        # Make sure its ohloh icon download time is null
        self.assertEqual(p.date_icon_was_fetched_from_ohloh, None)

        # get the thing we poll
        response = self.client.get(reverse(
            mysite.search.views.project_has_icon,
            kwargs={'project_name': p.name}))
        self.assertEqual(response.content, 'keep polling')

        # okay, so now say we finished polling
        p.date_icon_was_fetched_from_ohloh = datetime.datetime.utcnow()
        p.save()

        # so what now?
        response = self.client.get(reverse(
            mysite.search.views.project_has_icon,
            kwargs={'project_name': p.name}))
        self.assertEqual(response.content, p.get_url_of_icon_or_generic())

# vim: set nu ai et ts=4 sw=4:
