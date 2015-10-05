# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 Jessica McKellar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import datetime
import json
import mock

from twill import commands as tc

import django.conf
from django.contrib.auth.models import User
import django.core.cache
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
import django.db
from django.test import TestCase
from django.utils import http
from django.utils.unittest import skipIf
from django_webtest import WebTest

from mysite.base.tests import make_twill_url, TwillTests
import mysite.base.models
import mysite.account.tests
from mysite.profile.models import Person
import mysite.profile.models
import mysite.search.view_helpers
from mysite.search.models import (Project, Bug, ProjectInvolvementQuestion,
                                  Answer, BugAlert)
from mysite.search import views
import mysite.project.views

logger = logging.getLogger(__name__)


# ##############################
# Searches
# ##############################


class SearchWebTest(WebTest):
    """ Search tests using WebTest """
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_get_search(self):
        """ Succeed if search page is reached """
        search_page = self.app.get('/search/')
        self.assertEqual(search_page.status_code, 200)


class SearchTest(TwillTests):
    """ Tests using Twill for Search submodule """

    def search_via_twill(self, query=None):
        search_url = "http://openhatch.org/search/"
        if query:
            search_url += '?q=%s' % query
        tc.go(make_twill_url(search_url))

    def search_via_client(self, query=None):
        search_url = "/search/"
        return self.client.get(search_url, {u'q': query})

    def compare_lists(self, one, two):
        """ DO NOT USE - Legacy code for Python 2.6 - Use assertListEqual now"""
        self.assertEqual(len(one), len(two))
        self.assertEqual(set(one), set(two))

    # TODO - Consider refactor
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


class QueryTokenizes(TwillTests):
    """ Query tokenizes tests """

    def test_query_tokenizes_respects_spaces_quotes(self):
        """ Check that spaces and quotes are correctly handled in a query """
        difficult = "With spaces (and parens)"
        query = mysite.search.view_helpers.Query.create_from_GET_data({u'q': u'"%s"' % difficult})
        self.assertEqual(query.terms, [difficult])

        # Create a dummy bug in a dummy project then query
        project = Project.create_dummy(name=difficult)
        Bug.create_dummy(project=project)
        number_bugs_matching = query.get_bugs_unordered().count()
        self.assertEqual(number_bugs_matching, 1)


class SearchResults(TwillTests):
    fixtures = [u'bugs-for-two-projects.json']

    def test_query_object_is_false_when_no_terms_or_facets(self):
        """
        Don't create a query object if there are no terms or facets for the query
        """
        query = mysite.search.view_helpers.Query.create_from_GET_data({})
        self.assertFalse(query)

    def test_show_no_bugs_if_no_query(self):
        """ Don't display bugs if there is no query """

        # Call up search page with no query.
        response = self.client.get(u'/search/')
        # The variable u'bunch_of_bugs', passed to template, is a blank list.
        self.assertEqual(response.context[0][u'bunch_of_bugs'], [])

    def test_json_view(self):
        tc.go(make_twill_url(u'http://openhatch.org/search/?format=json&jsoncallback=callback&q=python'))
        response = tc.show()
        self.assertTrue(response.startswith(u'callback'))
        json_string_with_parens = response.split(u'callback', 1)[1]
        self.assertTrue(json_string_with_parens[0] == u'(')
        self.assertTrue(json_string_with_parens[-1] == u')')
        json_string = json_string_with_parens[1:-1]
        objects = json.loads(json_string)
        self.assertTrue(u'pk' in objects[0][u'bugs'][0])

    def test_pagination(self):
        """ Check if bugs returned from search are paginated """
        url = u'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv(u'search_opps', u'q', u'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs and advance to next 10
        bugs = Bug.all_bugs.filter(project__name=u'Exaile').order_by(u'-last_touched')[:10]
        for bug in bugs:
            tc.find(bug.description)
        tc.follow(u'Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=u'Exaile').order_by(u'-last_touched')[10:20]
        for bug in bugs:
            tc.find(bug.description)

    def test_pagination_with_any_facet(self):
        """ Check if bugs returned from search with any facet are paginated """
        url = u'http://openhatch.org/search/?q=&language='
        tc.go(make_twill_url(url))

        bugs = Bug.all_bugs.order_by(u'-last_touched')

        for bug in bugs[:10]:
            tc.find(bug.description)
        tc.follow(u'Next')

        bugs = bugs[10:20]
        for bug in bugs:
            tc.find(bug.description)

    def test_pagination_and_changing_search_query(self):
        """
        Check if bugs returned from search are paginated
        even when the search query is later changed
        """

        url = u'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv(u'search_opps', u'q', u'python')
        tc.submit()

        # Grab descriptions of first 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=u'Exaile').order_by(u'-last_touched')[:10]
        for bug in bugs:
            tc.find(bug.description)
        # Hit the next button
        tc.follow(u'Next')

        # Grab descriptions of next 10 Exaile bugs
        bugs = Bug.all_bugs.filter(project__name=u'Exaile').order_by(u'-last_touched')[10:20]
        for bug in bugs:
            tc.find(bug.description)

        # Now, change the query - do we stay that paginated?
        tc.fv(u'search_opps', u'q', u'c#')
        tc.submit()

        # Grab descriptions of first 10 GNOME-Do bugs
        bugs = Bug.all_bugs.filter(project__name=u'GNOME-Do').order_by(u'-last_touched')[:10]
        for bug in bugs:
            tc.find(bug.description)


class SplitIntoTerms(TestCase):
    """ Tests to split a query into individual terms """

    def test_split_into_terms(self):
        """Test if a query is correctly split into terms"""
        easy = '1 2 3'
        self.assertEqual(mysite.search.view_helpers.Query.split_into_terms(easy), ['1', '2', '3'])

        easy = '"1"'
        self.assertEqual(mysite.search.view_helpers.Query.split_into_terms(easy), ['1'])

        easy = 'c#'
        self.assertEqual(mysite.search.view_helpers.Query.split_into_terms(easy), ['c#'])


class IconGetsScaled(SearchTest):
    """ Tests to check icon scaling """

    def test_project_scales_its_icon_down_for_use_in_badge(self):
        """This test shows that the Project class successfully stores
        a scaled-down version of its icon in the icon_smaller_for_badge
        field."""

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
        """Sometimes icons are rectangular and more wide than long. These
        icons shouldn't be trammeled into a square, but scaled respectfully
        of their original ratios."""
        # Step 1: Create a project with an icon
        p = mysite.search.models.Project.create_dummy()

        # account.tests.photo finds the right path.
        image_data = open(mysite.account.tests.photo('static/images/icons/test-project-icon-64px-by-18px.png')).read()
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
    """ Tests that search works when passed words """

    # TODO
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_search_finds_full_words(self):
        """ Test that search returns the correct bugs when passed a word"""

        # Set up: create project and bugs, then check if correct
        Project.create_dummy()
        Bug.create_dummy(description='properly')
        dummy_perl_bug = Bug.create_dummy(description='perl')
        self.assertEqual(Bug.all_bugs.all().count(), 2)

        # Search for 'perl' bugs and see if the results are as expected
        test_query = mysite.search.view_helpers.Query(terms=['perl'])
        results = test_query.get_bugs_unordered()
        self.assertEqual(results.count(), 1)
        self.assertEqual(list(results), [dummy_perl_bug])


class SearchWebOnFullWords(SearchWebTest):
    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_search_web_finds_full_words(self):
        """ Test that search returns the correct bugs when passed a word"""

        # Set up: create project and bugs, then check if correct
        test_project = Project.create_dummy()
        Bug.create_dummy(project=test_project, description=u'properly')
        dummy_perl_bug = Bug.create_dummy(project=test_project, description=u'perl')
        self.assertEqual(Bug.all_bugs.all().count(), 2)

        # *** Query is not returning correct match results
        # results = mysite.search.view_helpers.Query(terms=['perl']).get_bugs_unordered()
        # self.assertEqual(results.count(), 1)
        # self.assertEqual(list(results), [dummy_perl_bug])


# *****************************************
# * Queries                               *
# *****************************************


class SearchTemplateDecodesQueryString(SearchTest):
    """ Search template correctly decodes a query string """

    def test_facets_appear_in_search_template_context(self):
        """ Check that search response included expected facets """
        response = self.client.get('/search/', {'language': 'Python'})
        expected_facets = {'language': 'Python'}
        self.assertEqual(response.context['query'].active_facet_options, expected_facets)


class SearchWebTemplateDecodesQueryString(SearchWebTest):
    """ Search template correctly decodes a query string - WebTest"""

    def test_facets_appear_in_search_template_context(self):
        """ Check that search response included expected facets - WebTest """
        response = self.app.get('/search/', {'language': 'Python'})
        expected_facets = {'language': 'Python'}
        self.assertEqual(response.context['query'].active_facet_options, expected_facets)


class FacetsFilterResults(SearchTest):
    """ Checks if search filters using the correct facets passed """

    def test_facets_filter_results(self):
        """ Check if results filtered on facets given to search """

        facets = {u'language': u'Python'}

        # Those facets should pick up this bug:
        python_project = Project.create_dummy(language='Python')
        python_bug = Bug.create_dummy(project=python_project)

        # But not this bug
        not_python_project = Project.create_dummy(language='Nohtyp')
        Bug.create_dummy(project=not_python_project)

        results = mysite.search.view_helpers.Query(terms=[], active_facet_options=facets).get_bugs_unordered()
        self.assertEqual(list(results), [python_bug])

    def test_any_facet(self):
        """In the search_index() method in the search module, the
        truthfulness of the Query object is evaluated to determine whether
        or not any results should be returned.

        Here, we test that if a facet in the GET data is the empty string,
        the query is still considered to be True. A facet
        set to the empty string is used to signify that the user selected the
        "any" option on the search page.

        If a facet is not provided at all, the user did not select anything
        on the search page, meaning no results should be returned.
        """

        language_query = mysite.search.view_helpers.Query.create_from_GET_data({'language': ''})
        project_query = mysite.search.view_helpers.Query.create_from_GET_data({'project': ''})

        self.assertTrue(language_query)
        self.assertTrue(project_query)


class QueryGetPossibleFacets(SearchTest):
    """Ask a query, what facets are you going to show on the left?
    E.g., search for gtk, it says C (541)."""

    def test_get_possible_facets(self):
        """ Test query succeeds using the possible facets  """
        # Create three projects
        project1 = Project.create_dummy(language=u'c')
        project2 = Project.create_dummy(language=u'd')
        project3 = Project.create_dummy(language=u'e')

        # Give each project a bug
        Bug.create_dummy(project=project1, description=u'bug', good_for_newcomers=True)
        Bug.create_dummy(project=project2, description=u'bug')
        Bug.create_dummy(project=project3, description=u'bAg')

        # Search for bugs matching "bug", while constraining to the language C
        query = mysite.search.view_helpers.Query(terms=[u'bug'],
                                                 terms_string=u'bug',
                                                 active_facet_options={u'language': u'c'})
        possible_facets = dict(query.get_possible_facets())
        self.assertEqual(query.get_bugs_unordered().count(), 1)

        # We expect that, language-wise, you should be able to select any of
        # the other languages, or 'deselect' your language constraint.
        # Compare lists of dictionaries possible facets, dictionaries, sort key
        self.compare_lists_of_dicts(possible_facets[u'language'][u'options'], [{u'name': u'c', u'query_string': u'q=bug&language=c', u'is_active': True, u'count': 1}, {u'name': u'd', u'query_string': u'q=bug&language=d', u'is_active': False, u'count': 1}, ], sort_key=u'name')

        # There's no 'any' option for toughness unless you've selected a specific toughness value
        self.compare_lists_of_dicts(possible_facets[u'toughness'][u'options'], [{u'name': u'bitesize', u'is_active': False, u'query_string': u'q=bug&toughness=bitesize&language=c', u'count': 1}, ], sort_key=u'name')

        self.assertEqual(possible_facets['language']['the_any_option'], {u'name': u'any', u'query_string': u'q=bug&language=', u'is_active': False, u'count': 2}, )

    def test_possible_facets_always_includes_active_facet(self):
        """
        Test query succeeds using the possible facets that includes the active facet
        even when active facet has no results.
        """
        c = Project.create_dummy(language=u'c')
        Project.create_dummy(language=u'd')
        Project.create_dummy(language=u'e')
        Bug.create_dummy(project=c, description=u'bug')
        query = mysite.search.view_helpers.Query.create_from_GET_data({u'q': u'nothing matches this', u'language': u'c'})

        language_options = dict(query.get_possible_facets())['language']['options']
        language_options_named_c = [opt for opt in language_options if opt['name'] == 'c']
        self.assertEqual(len(language_options_named_c), 1)


class SingleTerm(SearchTest):
    """Search for just a single term."""

    def setUp(self):
        """ Set up tests for single term search queries """
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')
        c_project = Project.create_dummy(language=u'C')

        # Bug matches Python, bitesize
        Bug.create_dummy(project=python_project, good_for_newcomers=True, description=u'screensaver')

        # Bug matches Python, not-bitesize
        Bug.create_dummy(project=python_project, good_for_newcomers=False, description=u'screensaver')

        # Bug matches Perl, not-bitesize
        Bug.create_dummy(project=perl_project, good_for_newcomers=False, description=u'screensaver')

        # Bug matches C, not-bitesize
        Bug.create_dummy(project=c_project, good_for_newcomers=False, description=u'toast')

        GET_data = {u'q': u'screensaver'}
        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        self.assertEqual(query.terms, [u'screensaver'])
        self.assertFalse(query.active_facet_options)  # No facets

        self.output_possible_facets = dict(query.get_possible_facets())

    def test_toughness_facet(self):
        """ Search for toughness """
        toughness_option_bitesize = {
            u'name': u'bitesize',
            u'count': 1,
            u'is_active': False,
            u'query_string': u'q=screensaver&toughness=bitesize'
        }
        toughness_option_any = {
            u'name': u'any',
            u'count': 3,
            u'is_active': True,
            u'query_string': u'q=screensaver&toughness='
        }
        expected_toughness_facet_options = [toughness_option_bitesize]

        self.assertEqual(self.output_possible_facets[u'toughness'][u'options'], expected_toughness_facet_options)
        self.assertEqual(self.output_possible_facets[u'toughness'][u'the_any_option'], toughness_option_any)

    def test_languages_facet(self):
        """ Search for language """
        languages_option_python = {
            'name': 'Python',
            'count': 2,
            'is_active': False,
            'query_string': 'q=screensaver&language=Python'
        }
        languages_option_perl = {
            'name': 'Perl',
            'count': 1,
            'is_active': False,
            'query_string': 'q=screensaver&language=Perl'
        }
        languages_option_any = {
            'name': 'any',
            'count': 3,
            'is_active': True,
            'query_string': 'q=screensaver&language='
        }
        expected_languages_facet_options = [
            languages_option_python,
            languages_option_perl,
        ]

        self.compare_lists_of_dicts(self.output_possible_facets['language']['options'], expected_languages_facet_options)

        self.assertEqual(self.output_possible_facets['language']['the_any_option'], languages_option_any)


class SingleFacetOption(SearchTest):
    """Browse bugs matching a single facet option."""

    def setUp(self):
        """ Set up tests for single term search queries """
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language='Python')
        perl_project = Project.create_dummy(language='Perl')
        c_project = Project.create_dummy(language='C')

        # Bug matches Python, bitesize
        Bug.create_dummy(project=python_project, good_for_newcomers=True, description='screensaver')

        # Bug matches Python, not-bitesize
        Bug.create_dummy(project=python_project, good_for_newcomers=False, description='screensaver')

        # Bug matches Perl, not-bitesize
        Bug.create_dummy(project=perl_project, good_for_newcomers=False, description='screensaver')

        # Bug matches C, not-bitesize
        Bug.create_dummy(project=c_project, good_for_newcomers=False, description='toast')

        GET_data = {u'language': u'Python'}
        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        self.assertFalse(query.terms)  # No terms
        self.assertEqual(query.active_facet_options, {u'language': u'Python'})

        self.output_possible_facets = dict(query.get_possible_facets())

    def test_toughness_facet(self):
        """ Search for toughness facet"""
        toughness_option_bitesize = {
            u'name': u'bitesize',
            u'count': 1,
            u'is_active': False,
            u'query_string': u'q=&toughness=bitesize&language=Python'
        }
        toughness_option_any = {
            u'name': u'any',
            u'count': 2,
            u'is_active': True,
            u'query_string': u'q=&toughness=&language=Python'
        }
        expected_toughness_facet_options = [toughness_option_bitesize]

        self.compare_lists_of_dicts(self.output_possible_facets[u'toughness'][u'options'], expected_toughness_facet_options)
        self.assertEqual(self.output_possible_facets[u'toughness'][u'the_any_option'], toughness_option_any)

    def test_languages_facet(self):
        """ Search for language """
        languages_option_python = {
            u'name': u'Python',
            u'count': 2,
            u'is_active': True,
            u'query_string': u'q=&language=Python'
        }
        languages_option_perl = {
            u'name': u'Perl',
            u'count': 1,
            u'is_active': False,
            u'query_string': u'q=&language=Perl'
        }
        languages_option_c = {
            u'name': u'C',
            u'count': 1,
            u'is_active': False,
            u'query_string': u'q=&language=C'
        }
        languages_option_any = {
            u'name': u'any',
            u'count': 4,
            u'is_active': False,
            u'query_string': u'q=&language='
        }
        expected_languages_facet_options = [
            languages_option_python,
            languages_option_perl,
            languages_option_c,
        ]

        self.compare_lists_of_dicts(self.output_possible_facets[u'language'][u'options'], expected_languages_facet_options)

        self.assertEqual(self.output_possible_facets[u'language'][u'the_any_option'], languages_option_any)


class QueryGetToughnessFacetOptions(SearchTest):
    """ Tests for toughness search queries """

    def test_get_toughness_facet_options(self):
        """ Test that bitesize bugs are found correctly when a search option is set """
        # create three "bitesize" bugs, but constrain the Query to look for only bugs in Python.
        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')

        Bug.create_dummy(project=python_project, good_for_newcomers=True)
        Bug.create_dummy(project=python_project, good_for_newcomers=False)
        Bug.create_dummy(project=perl_project, good_for_newcomers=True)

        # Since only two of the bitesize bugs are in Python (one is in a project whose language is
        # Perl), we expect only 1 bitesize bug to show up, and 2 total bugs.
        query = mysite.search.view_helpers.Query(active_facet_options={u'language': u'Python'}, terms_string=u'')
        output = query.get_facet_options(u'toughness', [u'bitesize', u''])
        bitesize_dict = [d for d in output if d[u'name'] == u'bitesize'][0]
        all_dict = [d for d in output if d[u'name'] == u'any'][0]

        self.assertEqual(bitesize_dict[u'count'], 1)
        self.assertEqual(all_dict[u'count'], 2)

    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_get_toughness_facet_options_with_terms(self):
        """ Test that bitesize bugs are found correctly when a search option is set with terms"""
        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')

        Bug.create_dummy(project=python_project, good_for_newcomers=True, description=u'a')
        Bug.create_dummy(project=python_project, good_for_newcomers=False, description=u'a')
        Bug.create_dummy(project=perl_project, good_for_newcomers=True, description=u'b')

        GET_data = {u'q': u'a'}
        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)

        output = query.get_facet_options(u'toughness', [u'bitesize', u''])
        bitesize_dict = [d for d in output if d[u'name'] == u'bitesize'][0]
        all_dict = [d for d in output if d[u'name'] == u'any'][0]

        # self.assertEqual(bitesize_dict[u'count'], 1)
        # self.assertEqual(all_dict[u'count'], 2)


class QueryGetPossibleLanguageFacetOptionNames(SearchTest):
    """ Tests for language search queries """

    def setUp(self):
        """ Set up the test environment """
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
        """ Test that a search term returns the correct results"""

        # In the setUp we create three bugs, but only two of them would match
        # a search for 'a'. They are in two different languages, so let's make
        # sure that we show only those two languages.
        GET_data = {u'q': u'a'}

        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        matched_language_names = query.get_language_names()
        self.assertEqual(matched_language_names.sort(), [u'Python', u'Perl'].sort())

    def test_with_active_language_facet(self):
        """ Test that a search term and active language facet returns the correct results"""
        # Here, we verify that the get_language_names() method correctly
        # returns all three languages, even though the GET data shows that
        # we are browsing by language.

        GET_data = {u'language': u'Python'}

        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        language_names = query.get_language_names()
        self.assertEqual(language_names.sort(), [u'Python', u'Perl', u'C', u'Unknown'].sort())

    def test_with_language_as_unknown(self):
        """ Test that a search term and 'unknown' facet returns the correct results"""
        # Here, we verify that the get_language_names() method correctly
        # returns all three languages, even though the GET data shows that
        # we are browsing by language.

        GET_data = {u'language': u'Unknown'}

        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        language_names = query.get_language_names()
        self.assertEqual(language_names.sort(), [u'Python', u'Perl', u'C', u'Unknown'].sort())

    def test_with_language_as_unknown_and_query(self):
        """ Test that a search 'unknown' language facet returns the correct results"""
        # In the setUp we create bugs in three languages.
        # Here, we verify that the get_language_names() method correctly
        # returns all three languages, even though the GET data shows that
        # we are browsing by language.

        GET_data = {u'language': u'Unknown', u'q': u'unknowable'}

        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        match_count = query.get_bugs_unordered().count()

        self.assertEqual(match_count, 1)


class QueryGetPossibleProjectFacetOptions(SearchTest):
    def setUp(self):
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
        query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        possible_project_names = [x['name'] for x in dict(query.get_possible_facets())['project']['options']]
        self.assertEqual(sorted(possible_project_names), sorted(list(Project.objects.values_list('name', flat=True))))


class QueryContributionType(SearchTest):
    def setUp(self):
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language=u'Python')
        perl_project = Project.create_dummy(language=u'Perl')
        c_project = Project.create_dummy(language=u'C')

        Bug.create_dummy(project=python_project, title=u'a')
        Bug.create_dummy(project=perl_project, title=u'a', concerns_just_documentation=True)
        Bug.create_dummy(project=c_project, title=u'b')

    def test_contribution_type_is_an_available_facet(self):
        GET_data = {}
        starting_query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        self.assert_(u'contribution_type' in dict(starting_query.get_possible_facets()))

    def test_contribution_type_options_are_reasonable(self):
        GET_data = {}
        starting_query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        cto = starting_query.get_facet_options(u'contribution_type', [u'documentation'])
        documentation_one, = [k for k in cto if k[u'name'] == u'documentation']
        any_one = starting_query.get_facet_options(u'contribution_type', [u''])[0]
        self.assertEqual(documentation_one[u'count'], 1)
        self.assertEqual(any_one[u'count'], 3)


class QueryProject(SearchTest):
    def setUp(self):
        SearchTest.setUp(self)
        python_project = Project.create_dummy(language=u'Python', name='thingamajig')
        c_project = Project.create_dummy(language=u'C', name='thingamabob')

        Bug.create_dummy(project=python_project, title=u'a')
        Bug.create_dummy(project=python_project, title=u'a', concerns_just_documentation=True)
        Bug.create_dummy(project=c_project, title=u'b')

    def test_project_is_an_available_facet(self):
        GET_data = {}
        starting_query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        self.assert_(u'project' in dict(starting_query.get_possible_facets()))

    def test_contribution_type_options_are_reasonable(self):
        GET_data = {}
        starting_query = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        cto = starting_query.get_facet_options(u'project', [u'thingamajig', u'thingamabob'])
        jig_ones, = [k for k in cto if k[u'name'] == u'thingamajig']
        any_one = starting_query.get_facet_options(u'project', [u''])[0]
        self.assertEqual(jig_ones[u'count'], 2)
        self.assertEqual(any_one[u'count'], 3)


class QueryStringCaseInsensitive(SearchTest):
    def test_language(self):
        """Do we redirect queries that use non-lowercase facet keys to pages
        that use lowercase facet keys?"""
        redirects = self.client.get(u'/search/', {u'LANguaGE': u'pytHon'}, follow=True).redirect_chain
        self.assertEqual(redirects, [(u'http://testserver/search/?language=pytHon', 302)])


class HashQueryData(SearchTest):
    def test_queries_with_identical_data_hash_alike(self):
        GET_data = {u'q': u'socialguides', u'language': u'looxii'}
        one = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        two = mysite.search.view_helpers.Query.create_from_GET_data(GET_data)
        self.assertEqual(one.get_sha1(), two.get_sha1())

    def test_queries_with_equiv_data_expressed_differently_hash_alike(self):
        GET_data_1 = {u'q': u'socialguides zetapage', u'language': u'looxii'}
        GET_data_2 = {u'q': u'zetapage socialguides', u'language': u'looxii'}
        one = mysite.search.view_helpers.Query.create_from_GET_data(GET_data_1)
        two = mysite.search.view_helpers.Query.create_from_GET_data(GET_data_2)
        self.assertEqual(one.get_sha1(), two.get_sha1())

    def test_queries_with_different_data_hash_differently(self):
        GET_data_1 = {u'q': u'socialguides zetapage', u'language': u'looxii'}
        GET_data_2 = {u'q': u'socialguides ninjapost', u'language': u'looxii'}
        one = mysite.search.view_helpers.Query.create_from_GET_data(GET_data_1)
        two = mysite.search.view_helpers.Query.create_from_GET_data(GET_data_2)
        self.assertNotEqual(one.get_sha1(), two.get_sha1())

        # How on earth do we test for collisions?


class FakeCache(object):
    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key, None)

    def set(self, key, value):
        self._data[key] = value


class QueryGrabHitCount(SearchTest):

    @mock.patch('django.core.cache')
    def test_eventhive_grab_hitcount_once_stored(self, fake_cache):
        fake_cache.cache = FakeCache()
        data = {u'q': u'eventhive', u'language': u'shoutNOW'}
        query = mysite.search.view_helpers.Query.create_from_GET_data(data)
        stored_hit_count = 10
        # Get the cache key used to store the hit count.
        hit_count_cache_key = query.get_hit_count_cache_key()
        # Set the cache value.
        django.core.cache.cache.set(hit_count_cache_key, stored_hit_count)
        # Test that it is fetched correctly.
        self.assertEqual(stored_hit_count, django.core.cache.cache.get(hit_count_cache_key))
        self.assertEqual(query.get_or_create_cached_hit_count(), stored_hit_count)

    @mock.patch('django.core.cache')
    def test_shoutnow_cache_hitcount_on_grab(self, fake_cache):
        fake_cache.cache = FakeCache()

        project = Project.create_dummy(language=u'shoutNOW')

        Bug.create_dummy(project=project)
        data = {u'language': u'shoutNOW'}
        query = mysite.search.view_helpers.Query.create_from_GET_data(data)

        expected_hit_count = 1
        self.assertEqual(query.get_or_create_cached_hit_count(), expected_hit_count)

        # Get the cache key used to store the hit count.
        hit_count_cache_key = query.get_hit_count_cache_key()
        # Get the cache value.
        stored_hit_count = django.core.cache.cache.get(hit_count_cache_key)
        logger.debug("Stored: %s" % stored_hit_count)
        # Test that it was stored correctly.
        self.assertEqual(stored_hit_count, expected_hit_count)


# *****************************************
# * Trackers                              *
# *****************************************


class ClearCacheWhenBugsChange(SearchTest):

    # TODO Cache not clearing? timestamps are not updating so hcc isn't either
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_cached_cleared_after_bug_save_or_delete(self):
        data = {u'language': u'shoutNOW'}
        query = mysite.search.view_helpers.Query.create_from_GET_data(data)
        old_hcc_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string(
            'hit_count_cache_timestamp')
        query.get_or_create_cached_hit_count()
        new_hcc_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string(
            'hit_count_cache_timestamp')
        self.assertEqual(old_hcc_timestamp, new_hcc_timestamp)

        # project = Project.create_dummy(language=u'shoutNOW')
        # bug = Bug.create_dummy(project=project)
        # newproject_create_bug_hcc_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string('hit_count_cache_timestamp')
        # self.assertNotEqual(new_hcc_timestamp, newproject_create_bug_hcc_timestamp)

        # # Cache entry created after hit count retrieval
        # query.get_or_create_cached_hit_count()
        # post_newproject_query_hcc_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string('hit_count_cache_timestamp')
        # self.assertEqual(newproject_create_bug_hcc_timestamp, post_newproject_query_hcc_timestamp)
        #
        # # Cache cleared after bug deletion
        # bug.delete()
        # deleted_bug_hcc_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string('hit_count_cache_timestamp')
        # self.assertNotEqual(post_newproject_query_hcc_timestamp, deleted_bug_hcc_timestamp)


class DontRecommendFutileSearchTerms(TwillTests):

    def test_removal_of_futile_terms(self):
        mysite.search.models.Bug.create_dummy_with_project(description=u'useful')
        self.assertEqual(Person.only_terms_with_results([u'useful', u'futile']), [u'useful'])


class PublicizeBugTrackerIndex(SearchTest):

    def setUp(self):
        SearchTest.setUp(self)
        self.search_page_response = self.client.get(reverse(mysite.search.views.search_index))
        self.bug_tracker_count = mysite.search.view_helpers.get_project_count()

    def test_search_template_contains_bug_tracker_count(self):
        self.assertEqual(self.search_page_response.context[0][u'project_count'], self.bug_tracker_count)


class TestPotentialMentors(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_mentors_on_project(self):
        """Test that mentors on a project returns accurate number."""

        # Create a project mentor, verify project has one mentor
        banshee = Project.create_dummy(name='Banshee', language='C#')
        can_mentor, _ = mysite.profile.models.TagType.objects.get_or_create(name=u'can_mentor')

        willing_to_mentor_banshee, _ = (mysite.profile.models.Tag.objects.get_or_create(tag_type=can_mentor, text=u'Banshee'))

        link = mysite.profile.models.Link_Person_Tag(person=Person.objects.get(user__username=u'paulproteus'), tag=willing_to_mentor_banshee)
        link.save()

        banshee_mentor_count = banshee.mentor_count
        self.assertEqual(1, banshee_mentor_count)


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
        opps_view = mysite.search.views.search_index
        query = u'ruby'
        opps_query_string = {u'q': query, u'start': 1, u'end': 10}
        opps_url = make_twill_url('http://openhatch.org' + reverse(opps_view) + '?' + http.urlencode(opps_query_string))
        tc.go(opps_url)

        # Make sure we *don't* have the comment that flags this as a page that
        # offers an email alert subscription button
        tc.notfind("this page should offer a link to sign up for an email alert")

        # Visit the last page of results
        GET = {u'q': query, u'start': 11, u'end': 20}
        query_string = http.urlencode(GET)
        opps_url = make_twill_url('http://openhatch.org' + reverse(opps_view) + '?' + query_string)
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
            'how_many_bugs_at_time_of_request':
                Bug.open_ones.filter(project=p).count(),
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
        #     * How many bugs were returned by the query at the time of
        #       request.

        # There should be only one alert
        all_alerts = BugAlert.objects.all()
        self.assertEqual(all_alerts.count(), 1)
        alert_record = all_alerts[0]
        self.assert_(alert_record)

        assert_that_record_has_this_data = alert_data_in_form

        # For the logged-in user, also check that the record contains the
        # identity of the user who made the alert request.

        if not anonymous:
            assert_that_record_has_this_data['user'] = (User.objects.get(username='paulproteus'))

        for key, expected_value in assert_that_record_has_this_data.items():
            self.assertEqual(alert_record.__getattribute__(key), expected_value, 'alert.%s = %s not (expected) %s' % (key, alert_record.__getattribute__(key), expected_value))

    # run the above test for our two use cases: logged in and not
    def test_alert_anon(self):
        self.exercise_alert(anonymous=True)

    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_alert_logged_in(self):
        self.exercise_alert(anonymous=False)


class DeleteAnswer(TwillTests):
    fixtures = ['user-paulproteus']

    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_delete_paragraph_answer(self):
        # create a dummy project involvement question
        dummy_project = Project.create_dummy(name='Ubuntu')
        question__pk = 0
        q = ProjectInvolvementQuestion.create_dummy(pk=question__pk, is_bug_style=False)
        # create our dummy answer to the question
        a = Answer.create_dummy(text='i am saying thigns', question=q, project=dummy_project, author=User.objects.get(username='paulproteus'))
        POST_data = {'answer__pk': a.pk}
        POST_handler = reverse(mysite.project.views.delete_paragraph_answer_do)
        print('*** POST_handler ***')
        print(POST_handler)

        response = self.login_with_client().post(POST_handler, POST_data)
        print('*** RESPONSE ***')
        print(response)
        # go back to the project page and make sure that our answer isn't there anymore
        dummy_project_url = dummy_project.get_url()
        print('*** dummy url ***')
        print(dummy_project_url)
        # self.assertRedirects(response, project_url)

        project_page = self.login_with_client().get(dummy_project_url)
        self.assertNotContains(project_page, a.text)
        # and make sure our answer isn't in the db anymore
        self.assertEqual(Answer.objects.filter(pk=a.pk).count(), 0)

    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
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
        a = Answer.create_dummy(title='i want this bug fixed', text='for these reasons', question=q, project=p, author=User.objects.get(username='paulproteus'))
        # delete our answer
        POST_data = {'answer__pk': a.pk, }
        POST_handler = reverse(mysite.project.views.delete_paragraph_answer_do)
        response = self.login_with_client().post(POST_handler, POST_data)
        # go back to the project page and make sure that our answer isn't there
        # anymore
        project_url = p.get_url()
        self.assertRedirects(response, project_url)
        project_page = self.login_with_client().get(project_url)

        self.assertNotContains(project_page, a.title)

        # and make sure our answer isn't in the db anymore
        self.assertEqual(Answer.objects.filter(pk=a.pk).count(), 0)


class CreateBugAnswer(TwillTests):
    fixtures = ['user-paulproteus']

    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_create_bug_answer(self):
        # go to the project page
        project = Project.create_dummy(name='Ubuntu')
        question__pk = 1
        question = ProjectInvolvementQuestion.create_dummy(key_string='non_code_participation', is_bug_style=True)
        question.save()
        title = 'omfg i wish this bug would go away'
        text = 'kthxbai'
        POST_data = {'project__pk': project.pk, 'question__pk': str(question__pk), 'answer__title': title, 'answer__text': text, }
        POST_handler = reverse(mysite.project.views.create_answer_do)
        response = self.login_with_client().post(POST_handler, POST_data)

        # try to get the BugAnswer which we just submitted from the database
        our_bug_answer = Answer.objects.get(title=title)

        # make sure it has the right attributes
        self.assertEqual(our_bug_answer.text, text)
        self.assertEqual(our_bug_answer.question.pk, question__pk)
        self.assertEqual(our_bug_answer.project.pk, project.pk)

        project_url = project.get_url()
        self.assertRedirects(response, project_url)

        project_page = self.login_with_client().get(project_url)

        # make sure that our data shows up on the page
        self.assertContains(project_page, title)
        self.assertContains(project_page, text)


class CreateWebBugAnswer(SearchWebTest):
    fixtures = ['user-paulproteus']

    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_web_create_bug_answer(self):
        p = Project.create_dummy(name='Ubuntu')
        question__pk = 1
        question = ProjectInvolvementQuestion.create_dummy(key_string='non_code_participation', is_bug_style=True)
        question.save()
        title = 'omfg i wish this bug would go away'
        text = 'kthxbai'
        POST_data = {'project__pk': p.pk, 'question__pk': str(question__pk), 'answer__title': title, 'answer__text': text, }
        POST_handler = reverse(mysite.project.views.create_answer_do)

        response = self.app.post('/search/')

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
        mysite.project.view_helpers.note_in_session_we_control_answer_id(session, answer.id)
        self.assertEqual(session['answer_ids_that_are_ours'], [answer.id])

        # If you want to look at those answers, you can this way:
        stored_answers = (mysite.project.view_helpers.get_unsaved_answers_from_session(session))
        self.assertEqual([answer.id for answer in stored_answers], [answer.id])

        # Verify that the Answer object is still not available by .objects()
        self.assertFalse(Answer.objects.all())

        # At login time, take ownership of those Answer IDs
        mysite.project.view_helpers.take_control_of_our_answers(User.objects.get(username='paulproteus'), session)

        # And now we own it!
        self.assertEqual(Answer.objects.all().count(), 1)


class CreateAnonymousAnswer(TwillTests):
    fixtures = ['user-paulproteus']

    # TODO Fix test
    @skipIf(django.db.connection.vendor == 'sqlite', "Skipping because using sqlite database")
    def test_create_answer_anonymously(self):
        # Steps for this test
        # 1. User fills in the form anonymously
        # 2. We test that the Answer is not yet saved
        # 3. User logs in
        # 4. We test that the Answer is saved

        p = Project.create_dummy(name='Myproject')
        q = ProjectInvolvementQuestion.create_dummy(key_string='where_to_start', is_bug_style=False)

        # Do a GET on the project page to prove cookies work.
        self.client.get(p.get_url())

        # POST some text to the answer creation post handler
        answer_text = 'Help produce official documentation, share the solution to a problem, or check, proof and test other documents for accuracy.'
        POST_data = {'project__pk': p.pk, 'question__pk': q.pk, 'answer__text': answer_text, }
        response = self.client.post(reverse(mysite.project.views.create_answer_do), POST_data, follow=True)
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/account/login/?next=%2Fprojects%2FMyproject', 302)])

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

        self.assertFalse(Answer.objects.all())  # it's unowned

        # Now, the session will know about the answer, but the answer will
        # not be published.
        # Visit the login page, assert that the page contains the text of the
        # answer.
        response = self.client.get(reverse('oh_login'))
        self.assertContains(response, POST_data['answer__text'])

        # But when the user is logged in and *then* visits the project page
        login_worked = self.client.login(username='paulproteus', password="paulproteus's unbreakable password")
        self.assert_(login_worked)

        self.client.get(p.get_url())

        # Now, the Answer should have an author whose username is paulproteus
        answer = Answer.objects.get()
        self.assertEqual(answer.text, POST_data['answer__text'])
        self.assertEqual(answer.author.username, 'paulproteus')

        # Finally, go to the project page and make sure that our Answer has
        # appeared
        response = self.client.get(p.get_url())
        self.assertContains(response, answer_text)


class CreateAnswer(TwillTests):
    """ Tests on answers created and entered by user """
    fixtures = ['user-paulproteus']

    def test_create_answer(self):
        """
        Checks if answer created, saved to db, and rendered on project page
        when passed plain text
        """

        # Set up test
        p = Project.create_dummy()
        q = ProjectInvolvementQuestion.create_dummy(key_string='where_to_start', is_bug_style=False)

        # POST some text to the answer creation post handler
        POST_data = {'project__pk': p.pk, 'question__pk': q.pk, 'answer__text': 'Help produce official documentation, share the solution to a problem, or check, proof and test other documents for accuracy.', }
        self.login_with_client().post(reverse(mysite.project.views.create_answer_do), POST_data)
        # If this were an Ajaxy post handler, we might assert something about
        # the response, like self.assertEqual(response.content, '1')

        # Check that the db contains a record with this answer text
        try:
            record = Answer.objects.get(text=POST_data['answer__text'])
        except Answer.DoesNotExist:
            print "All Answers:", Answer.objects.all()
            raise Answer.DoesNotExist
        self.assertEqual(record.author, User.objects.get(username='paulproteus'))
        self.assertEqual(record.project, p)
        self.assertEqual(record.question, q)

        # Check that the project page now includes the answer text
        project_page = self.client.get(p.get_url())
        self.assertContains(project_page, POST_data['answer__text'])
        self.assertContains(project_page, record.author.username)

    def test_multiparagraph_answer(self):
        """
        Checks if answer created, saved to db, and rendered on project page
        when passed text with multiple paragraphs
        """

        # Set up test
        project = Project.create_dummy(name='Ubuntu')
        question = ProjectInvolvementQuestion.create_dummy(key_string='where_to_start', is_bug_style=False)
        question.save()
        entered_text = ['This is a multiparagraph answer.', 'This is the second paragraph.', 'This is the third paragraph.']

        # POST some text to the answer creation post handler
        POST_data = {'project__pk': project.pk, 'question__pk': question.pk, 'answer__text': "\n".join(entered_text), }
        POST_handler = reverse(mysite.project.views.create_answer_do)
        self.login_with_client().post(POST_handler, POST_data)

        # Check that the db contains a record with this answer text
        try:
            record = Answer.objects.get(text=POST_data['answer__text'])
        except Answer.DoesNotExist:
            print "All Answers:", Answer.objects.all()
            raise Answer.DoesNotExist

        # Check that the project page now includes the answer text
        project_page = self.client.get(project.get_url())
        # TODO
        # self.assertContains(project_page, POST_data['answer__text'])
        self.assertContains(project_page, record.author.username)

        # Django documents publicly that linebreaks replaces one "\n" with "<br />".
        # http://docs.djangoproject.com/en/dev/ref/templates/builtins/#linebreaks
        # TODO
        # self.assertContains(project_page, "<br />".join(text))

    def test_answer_with_background_color(self):
        """
        If a user submits HTML with embedded styles, they should be dropped.
        """
        # go to the project page
        p = Project.create_dummy(name='Ubuntu')
        q = ProjectInvolvementQuestion.create_dummy(key_string='where_to_start', is_bug_style=False)
        q.save()
        text = u'<p style="background-color: red;">red</p>'
        POST_data = {'project__pk': p.pk, 'question__pk': q.pk, 'answer__text': text}

        # Submit the data while logged in
        POST_handler = reverse(mysite.project.views.create_answer_do)
        self.login_with_client().post(POST_handler, POST_data)

        # Look at page while logged out (so we see the anonymous rendering)
        project_page = self.client.get(p.get_url())

        # The urlize filter in the template should make sure we get a link
        self.assertNotContains(project_page, '''background-color: red''')


class BugKnowsItsFreshness(TestCase):
    """ Tests for bug freshness from trackers"""

    def test_bug_freshness_one_day(self):
        b = mysite.search.models.Bug.create_dummy_with_project()
        b.last_polled = datetime.datetime.now()
        self.assertTrue(b.data_is_more_fresh_than_one_day())
        b.last_polled -= datetime.timedelta(days=1, hours=1)
        self.assertFalse(b.data_is_more_fresh_than_one_day())


class PollIfProjectIconLoaded(TestCase):
    """ Poll and check if there is a project icon loaded """

    def test_poll_project_icon_loaded(self):
        """ Check loading of project icon """

        p = Project.create_dummy()
        # Make sure its ohloh icon download time is null
        self.assertEqual(p.date_icon_was_fetched_from_ohloh, None)

        # Get the icon from polling
        response = self.client.get(reverse(mysite.search.views.project_has_icon, kwargs={'project_name': p.name}))
        self.assertEqual(response.content, 'keep polling')

        # Polling is finished
        p.date_icon_was_fetched_from_ohloh = datetime.datetime.utcnow()
        p.save()

        response = self.client.get(reverse(mysite.search.views.project_has_icon, kwargs={'project_name': p.name}))
        self.assertEqual(response.content, p.get_url_of_icon_or_generic())
