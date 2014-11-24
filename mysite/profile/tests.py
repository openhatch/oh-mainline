# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 Karen Rustad
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 Mark Freeman
# Copyright (C) 2010 Jessica McKellar
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Jack Grigg
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

from mysite.base.view_helpers import ObjectFromDict
from mysite.base.models import Timestamp
import mysite.account.tests
from mysite.search.models import Project, WannaHelperNote
from mysite.profile.models import (Person, Tag, TagType, Link_Person_Tag,
                                   DataImportAttempt, PortfolioEntry,
                                   Citation, Forwarder)
import mysite.project.views
import mysite.profile.views
import mysite.profile.models
import mysite.profile.view_helpers
import mysite.profile.templatetags.profile_extras
from mysite.profile.management.commands import send_emails
from mysite.profile import views
from mysite.customs.models import WebResponse
import pprint

from django.utils import simplejson
import BeautifulSoup
import datetime
import tasks
import mock
import os
import quopri

from django.core import mail
from django.conf import settings
import django.test
import django.conf
import django.db
from django.core import serializers
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django.utils.unittest import skipIf
from django_webtest import WebTest
from django.test.client import Client


class BasicHelpers(WebTest):
    def login_with_client(self, username='paulproteus', password="paulproteus's unbreakable password"):
        client = Client()
        success = client.login(username=username, password=password)
        self.assertTrue(success)
        return client

    def login_with_client_as_barry(self):
        return self.login_with_client(username='barry', password='parallelism')

class ProfileTests(WebTest):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus',
                'cchost-data-imported-from-ohloh']

    def testSlash(self):
        self.client.get('/people/')

    def test__portfolio_updates_when_citation_added_to_db(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                is_published=True,
                person=paulproteus)[0],
            languages='Python',
        )
        citation.save()

        # Verify that get_publish_portfolio_entries() works
        self.assert_('project name' in [
                     pfe.project.name for pfe in
                     paulproteus.get_published_portfolio_entries()])

    def test_get_full_name_and_username(self):
        # Test case with first name and last name.
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(paulproteus.get_full_name_and_username(),
                         'Asheesh Laroia (paulproteus)')
        # Test case with no last name.
        paulproteus.user.last_name = ''
        self.assertEqual(paulproteus.get_full_name_and_username(),
                         'Asheesh (paulproteus)')
        # Test case with no first name.
        paulproteus.user.first_name = ''
        paulproteus.user.last_name = 'Laroia'
        self.assertEqual(paulproteus.get_full_name_and_username(),
                         'Laroia (paulproteus)')
        # Test case with no first name or last name.
        paulproteus.user.last_name = ''
        self.assertEqual(
            paulproteus.get_full_name_and_username(), 'paulproteus')
        # Retest case with first name and last name.
        # This also returns the Person object to its initial state.
        paulproteus.user.first_name = 'Asheesh'
        paulproteus.user.last_name = 'Laroia'
        self.assertEqual(paulproteus.get_full_name_and_username(),
                         'Asheesh Laroia (paulproteus)')


class DebTagsTests(BasicHelpers):

    def testAddOneDebtag(self):
        views.add_one_debtag_to_project('alpine', 'implemented-in::c')
        self.assertEqual(views.list_debtags_of_project('alpine'),
                         ['implemented-in::c'])

    def testImportDebtags(self):
        views.import_debtags(cooked_string='alpine:works-with::mail, '
                             'protocol::smtp')  # side effects galore!
        self.assertEqual(set(views.list_debtags_of_project('alpine')),
                         set(['works-with::mail', 'protocol::smtp']))


class Info(BasicHelpers):
    # {{{
#TODO
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
                'person-paulproteus', 'cchost-data-imported-from-ohloh']

    tags = {
        'understands': ['ack', 'b', 'c'],
        'understands_not': ['dad', 'e', 'f'],
        'can_pitch_in': ['gone', 'h', 'i'],
        'studying': ['jam', 'k', 'l'],
        'can_mentor': ['mop', 'n', 'o'],
    }
    tags_2 = {
        'understands': ['Ack!', 'B!', 'C!'],
        'understands_not': ['dad', 'e', 'f'],
        'can_pitch_in': ['gone', 'h', 'i'],
        'studying': ['Jam?', 'K?', 'L?'],
        'can_mentor': ['mop', 'n', 'o'],
    }
    # FIXME: Test whitespace, too.

    # FIXME: Write a unit test for this.
    def update_tags(self, tag_dict):
        url = reverse(mysite.profile.views.edit_info)
        # Log in as paulproteus
        username = 'paulproteus'
        edit_info_page = self.app.get(url, user=username)
        edit_info_form = edit_info_page.form

        for tag_type_name in tag_dict:
            edit_info_form['edit-tags-'+tag_type_name] = ', '.join(tag_dict[tag_type_name])
        edit_info_form.submit()

        # Check that at least the first tag made it into the database.
        self.assert_(list(Link_Person_Tag.objects.filter(
            tag__text=tag_dict.values()[0][0],
            person__user__username='paulproteus')))

        # Check that the output is correct.
        edit_info_page = self.app.get(url, user=username)
        soup = BeautifulSoup.BeautifulSoup(edit_info_page.content)
        for tag_type_name in tag_dict:
            text = ''.join(soup(id='id_edit-tags-%s' % tag_type_name)
                           [0].findAll(text=True))
            self.assert_(
                ', '.join(tag_dict[tag_type_name]) in ' '.join(text.split()))

        # Go back to the form and make sure some of these are there
        response = self.app.get(url, user=username)
        self.assertIn(tag_dict.values()[0][0], response.content)

    def test_tag_edit_once(self):
        self.login_with_client()
        self.update_tags(self.tags)

    def test_tag_edit_twice(self):
        self.login_with_client()
        self.update_tags(self.tags)
        self.update_tags(self.tags_2)

# Create a mock Ohloh get_contribution_info_by_username
mock_gcibu = mock.Mock()
# This object will always return:
mock_gcibu.return_value = ([{
    'man_months': 1,
    'project': u'MOCK ccHost',
    u'permalink':
    u'https://www.ohloh.net/p/cchost/contributors/65837553699824',
    'project_homepage_url':
    u'http://wiki.creativecommons.org/CcHost',
    'first_commit_time':
    '2008-04-03T23:51:45Z',
    'primary_language': u'shell script'},
],
    None  # WebResponse
)

# Create a mock Ohloh get_contribution_info_by_ohloh_username
mock_gcibou = mock.Mock()
mock_gcibou.return_value = ([{
    'man_months': 1,
    u'permalink':
    u'https://www.ohloh.net/p/cchost/contributors/65837553699824',
    'project': u'MOCK ccHost',
    'project_homepage_url':
    u'http://wiki.creativecommons.org/CcHost',
    'primary_language': u'Vala'}],
    None  # WebResponse
)

# FIXME: If this is made dynamically, it would be easier!


class MockFetchPersonDataFromOhloh(object):
    real_task_class = tasks.FetchPersonDataFromOhloh

# Mockup of stump's contribution list as given by ohloh, stripped down and
# slightly tweaked for the purposes of testing.
stumps_ohloh_results = mock.Mock()
stumps_ohloh_results.return_value = ([
    {u'contributor_name': u'stump', u'analysis_id': u'1145788',
     u'man_months': u'11', u'primary_language_nice_name': u'C',
     u'contributor_id': u'2008814186590608'},
    {u'contributor_name': u'John Stumpo', u'analysis_id': u'1031175',
     u'man_months': u'12', u'primary_language_nice_name': u'Python',
     u'contributor_id': u'110891760646528'}
], WebResponse())
stumps_project_lookup = mock.Mock()
stumps_project_lookup.return_value = {
    u'name': u'WinKexec',
    u'homepage_url': u'https://www.jstump.com/projects/kexec/'}


class Portfolio(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']
    # Don't include cchost-paulproteus, because we need paulproteus to have
    # zero Citations at the beginning of
    # test_person_gets_data_iff_they_want_it

    form_url = "http://openhatch.org/people/portfolio/import/"

    def _test_get_import_status(self, client, but_first=None,
                                must_find_nothing=False):
        '''Just make sure that the JSON returned by the view is appropriate
        considering what's in the database.'''

        # LOAD DATA ########################
        #
        paulproteus = Person.objects.get(user__username='paulproteus')

        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                person=paulproteus)[0],
            languages='Python',
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=paulproteus)[0]
        )
        citation.save()

        finished_dia = citation.data_import_attempt
        unfinished_dia = DataImportAttempt(source='rs',
                                           query='foo',
                                           completed=False,
                                           person=paulproteus)
        unfinished_dia.save()

        if but_first is not None:
            but_first()

        response = client.get(
            reverse(mysite.profile.views.gimme_json_for_portfolio))

        # Response consists of JSON like:
        # {'dias': ..., 'citations': ..., 'summaries': ...}
        response = simplejson.loads(response.content)

        # Check we got a summary for each Citation.
        for citation_in_response in response['citations']:
            self.assert_(
                str(citation_in_response['pk']
                    ) in response['summaries'].keys(),
                "Expected that this Citation's pk would have a summary.")

        #
        # Are the DIAs and citations in the response
        # exactly what we expected?
        #

        # What we expect:
        expected_list = serializers.serialize(
            'python', [finished_dia, unfinished_dia, citation])

        # What we got:
        dias_and_citations_in_response = response[
            'dias'] + response['citations']

        # We don't care about the "fields" in either, just the pk and model.
        for object in (dias_and_citations_in_response + expected_list):
            del object['fields']

        # Check that each thing we got was expected.
        for object in dias_and_citations_in_response:
            object_is_expected = (object in expected_list)
            if must_find_nothing:
                self.assertFalse(object_is_expected)
            else:
                self.assert_(object_is_expected)

        # Check the reverse: that each thing we expected we got.
        for object in expected_list:
            object_is_expected = (object in dias_and_citations_in_response)
            if must_find_nothing:
                self.assertFalse(object_is_expected)
            else:
                self.assert_(object_is_expected)

    def test_paulproteus_can_get_his_import_status(self):
        self._test_get_import_status(
            client=self.login_with_client(), must_find_nothing=False)

    def test_barry_cannot_get_paulproteuss_import_status(self):
        self._test_get_import_status(
            client=self.login_with_client_as_barry(),
            must_find_nothing=True)

    def test_paulproteus_gets_no_deleted_projects(self):
        #
        # LOAD DATA ########################
        #
        paulproteus = Person.objects.get(user__username='paulproteus')

        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                person=paulproteus)[0],
            languages='Python',
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus',
                completed=True, person=paulproteus)[0]
        )
        citation.save()

        # finished dia
        citation.data_import_attempt
        unfinished_dia = DataImportAttempt(source='rs',
                                           query='foo',
                                           completed=False,
                                           person=paulproteus)
        unfinished_dia.save()

        # Delete the projects
        portfolio_entries = PortfolioEntry.objects.all()
        for portfolio_entry in portfolio_entries:
            portfolio_entry.is_deleted = True
            portfolio_entry.save()

        # Get the JSON

        response = self.login_with_client().get(
            reverse(mysite.profile.views.gimme_json_for_portfolio))
        response_decoded = simplejson.loads(response.content)

        self.assertEqual(len(response_decoded['projects']), 0,
                         "Expected no projects back.")

        self.assertEqual(len(response_decoded['citations']), 0,
                         "Expected no citations back.")
        # Who cares about DIAS.


class ImporterPublishCitation(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def test_publish_citation(self):
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                person=Person.objects.get(
                    user__username='paulproteus'))[0],
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=Person.objects.get(user__username='paulproteus'))[0]
        )
        citation.save()

        self.assertFalse(citation.is_published)

        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client().post(
            reverse(view), {'pk': citation.pk})

        self.assertEqual(response.content, "1")
        self.assert_(Citation.untrashed.get(pk=citation.pk).is_published)

    def test_publish_citation_fails_when_citation_doesnt_exist(self):
        failing_pk = 0
        self.assertEqual(Citation.untrashed.filter(pk=failing_pk).count(), 0)

        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client().post(
            reverse(view), {'pk': failing_pk})
        self.assertEqual(response.content, "0")

    def test_publish_citation_fails_when_citation_not_given(self):
        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client().post(reverse(view))
        self.assertEqual(response.content, "0")

    def test_publish_citation_fails_when_citation_not_yours(self):
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                person=Person.objects.get(
                    user__username='paulproteus'))[0],
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=Person.objects.get(user__username='paulproteus'))[0]
        )
        citation.save()

        self.assertFalse(citation.is_published)
        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client().post(reverse(view))

        self.assertEqual(response.content, "0")


class ImporterDeleteCitation(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def test_delete_citation(self):
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                person=Person.objects.get(
                    user__username='paulproteus'))[0],
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=Person.objects.get(user__username='paulproteus'))[0]
        )
        citation.save()

        self.assertFalse(citation.is_deleted)

        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client().post(
            reverse(view), {'citation__pk': citation.pk})

        self.assertEqual(response.content, "1")
        self.assert_(Citation.objects.get(pk=citation.pk).is_deleted)

    def test_delete_citation_fails_when_citation_doesnt_exist(self):
        failing_pk = 0
        self.assertEqual(Citation.objects.filter(pk=failing_pk).count(), 0)

        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client().post(
            reverse(view), {'pk': failing_pk})
        self.assertEqual(response.content, "0")

    def test_delete_citation_fails_when_citation_not_given(self):
        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client().post(reverse(view))
        self.assertEqual(response.content, "0")

    def test_delete_citation_fails_when_citation_not_yours(self):
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                person=Person.objects.get(
                    user__username='paulproteus'))[0],
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=Person.objects.get(user__username='paulproteus'))[0]
        )
        citation.save()
        self.assertFalse(citation.is_deleted)

        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client_as_barry().post(reverse(view))
        self.assertEqual(response.content, "0")

# Create a mock Launchpad get_info_for_launchpad_username
mock_launchpad_debian_response = mock.Mock()
mock_launchpad_debian_response.return_value = {
    'Debian': {
        # ok this url doesn't really exist
        'url': 'http://launchpad.net/debian',
        'involvement_types': ['Bug Management', 'Bazaar Branches'],
        'citation_url': 'https://launchpad.net/~paulproteus',
        'languages': '',
    }
}


class PersonInfoLinksToSearch(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_whatever(self):
        # FIXME: When there is a reasonable way to do search during test
        # runtime, like us using djapian or whoosh, then let's re-enable the
        # assertion at the end
        # of this.
        '''
        * Have a user, say that he
          understands+wantstolearn+currentlylearns+canmentor something
        * Go to his user page, and click those various links
        * Find yourself on some search page that mentions the user.
        '''
        tags = {
            'understands': ['thing1'],
            'understands_not': ['thing2'],
            'can_pitch_in': ['thing3'],
            'studying': ['thing4'],
            'can_mentor': ['thing5'],
        }

        # Log in as paulproteus
        username = 'paulproteus'
        response = self.login_with_client()

        # Update paulproteus's tags
        edit_info_page = self.app.get('/profile/views/edit_info', user=username)
        edit_info_form = edit_info_page.form
        for tag_type_name in tags:
            edit_info_form['edit-tags-'+tag_type_name] = tags[tag_type_name]
        res = edit_info_form.submit().follow()
        search_results = res.click('thing1')
        self.assertIn('Asheesh', search_results.content)


class Widget(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_widget_display(self):
        widget_url = reverse(
            mysite.profile.views.widget_display,
            kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        client.get(widget_url)

    def test_widget_display_js(self):
        widget_js_url = reverse(
            mysite.profile.views.widget_display_js,
            kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        client.get(widget_js_url)


class PersonalData(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
                'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def test_all_views_that_call_get_personal_data(self):
        # Views where you can look at somebody else.
        stalking_view2args = {
            mysite.profile.views.display_person_web: {
                'user_to_display__username': 'paulproteus'},
        }

        # Views where you look only at yourself.
        navelgazing_view2args = {
            mysite.profile.views.importer: {},
        }

        for view in stalking_view2args:
            self.client.login(username='barry', password='parallelism')
            kwargs = stalking_view2args[view]
            url = reverse(view, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(
                response.context[0]['person'].user.username, 'paulproteus')
            self.client.logout()

        for view in navelgazing_view2args:
            self.client.login(username='paulproteus', password="paulproteus's unbreakable password")
            kwargs = navelgazing_view2args[view]
            url = reverse(view, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(
                response.context[0]['person'].user.username, 'paulproteus')
            self.client.logout()


class DeletePortfolioEntry(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def test_delete_portfolio_entry(self):
        portfolio_entry = PortfolioEntry.objects.get_or_create(
            project=Project.objects.get_or_create(
                name='project name')[0],
            person=Person.objects.get(user__username='paulproteus'))[0]

        citation = Citation(
            portfolio_entry=portfolio_entry,
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=Person.objects.get(user__username='paulproteus'))[0]
        )
        citation.save()

        self.assertFalse(portfolio_entry.is_deleted)

        view = mysite.profile.views.delete_portfolio_entry_do
        response = self.login_with_client().post(
            reverse(view),
            {'portfolio_entry__pk': portfolio_entry.pk})

        response_decoded = simplejson.loads(response.content)

        expected_output = {
            'success': True,
            'portfolio_entry__pk': portfolio_entry.pk
        }

        self.assertEqual(response_decoded, expected_output)
        self.assert_(PortfolioEntry.objects.get(pk=portfolio_entry.pk)
                     .is_deleted)

    def test_delete_portfolio_entry_fails_when_portfolio_entry_doesnt_exist(
            self):
        failing_pk = 0
        self.assertEqual(
            PortfolioEntry.objects.filter(pk=failing_pk).count(), 0)

        view = mysite.profile.views.delete_portfolio_entry_do
        response = self.login_with_client().post(
            reverse(view), {'portfolio_entry__pk': failing_pk})
        self.assertEqual(simplejson.loads(response.content),
                         {'success': False})

    def test_delete_portfolio_entry_fails_when_portfolio_entry_not_given(self):
        view = mysite.profile.views.delete_portfolio_entry_do
        response = self.login_with_client().post(reverse(view))
        self.assertEqual(simplejson.loads(response.content),
                         {'success': False})

    def test_delete_portfolio_entry_fails_when_portfolio_entry_not_yours(self):
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                person=Person.objects.get(
                    user__username='paulproteus'))[0],
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=Person.objects.get(user__username='paulproteus'))[0]
        )
        citation.save()

        portfolio_entry_not_mine = citation.portfolio_entry

        self.assertFalse(portfolio_entry_not_mine.is_deleted)
        view = mysite.profile.views.delete_portfolio_entry_do
        response = self.login_with_client().post(reverse(view))

        self.assertEqual(simplejson.loads(response.content), {'success': False})

        # Still there
        self.assertFalse(portfolio_entry_not_mine.is_deleted)


class AddCitationManually(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def test_add_citation_manually(self):
        proj = Project.create_dummy(name='project name')
        portfolio_entry, _ = PortfolioEntry.objects.get_or_create(
            project=proj,
            person=Person.objects.get(user__username='paulproteus'))

        input_data = {
            'portfolio_entry': portfolio_entry.pk,
            'form_container_element_id': 'form_container_%d' % 0,
            # Needs this trailing slash to work.
            'url': 'http://google.com/'
        }

        # Send this data to the appropriate view.
        url = reverse(mysite.profile.views.add_citation_manually_do)
        self.login_with_client().post(url, input_data)

        # Check that a citation was created.
        c = Citation.untrashed.get(url=input_data['url'])
        self.assertEqual(c.portfolio_entry, portfolio_entry,
                         "The portfolio entry for the new citation is the "
                         "exactly the one whose id we POST'd to "
                         "profile.views.add_citation_manually.")

        self.assert_(c.is_published,
                     "Manually added citations are published by default.")

    def test_add_citation_manually_with_bad_portfolio_entry(self):
        not_your_portfolio_entry, _ = PortfolioEntry.objects.get_or_create(
            project=Project.objects.get_or_create(name='project name')[0],
            person=Person.objects.get(user__username='barry'))

        input_data = {
            'portfolio_entry': not_your_portfolio_entry.pk,
            'form_container_element_id': 'form_container_%d' % 0,
            'url': 'http://google.ca/'  # Needs this trailing slash to work.
        }

        # Send this data to the appropriate view.
        url = reverse(mysite.profile.views.add_citation_manually_do)
        response = self.login_with_client().post(url, input_data)

        # Check that no citation was created.
        self.assertEqual(
            Citation.untrashed.filter(url=input_data['url']).count(), 0,
            "Expected no citation to be created when you try "
            "to add one for someone else.")

        # Check that an error is reported in the response.
        self.assert_(
            len(simplejson.loads(response.content)['error_msgs']) == 1)


class SavePortfolioEntry(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def setUp(self):
        WebTest.setUp(self)
        self.user = "paulproteus"
        self.project = Project.objects.get_or_create(name='project name')[0]

        self.portfolio_entry = PortfolioEntry.objects.get_or_create(
            project=self.project,
            person=Person.objects.get(user__username=self.user))[0]
        citation = Citation(
            portfolio_entry=self.portfolio_entry,
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query=self.user, completed=True,
                person=Person.objects.get(user__username=self.user))[0]
        )
        citation.is_published = False
        citation.save()

        self.experience_description = [
            'This is a multiparagraph experience description.',
            'This is the second paragraph.',
            'This is the third paragraph.']

        self.project_description = [
            'This is a multiparagraph project description.',
            'This is the second paragraph.',
            'This is the third paragraph.']

        self.POST_data = {
            'portfolio_entry__pk': self.portfolio_entry.pk,
            'pf_entry_element_id': 'blargle',  # this can be whatever
            'project_description': "\n".join(self.project_description),
            'experience_description': "\n".join(self.experience_description),
            'receive_maintainer_updates': 'false',
        }

        POST_handler = reverse(mysite.profile.views.save_portfolio_entry_do)
        self.post_result = self.login_with_client().post(
            POST_handler, self.POST_data)
        self.contribution_page = self.login_with_client().get('/people/%s/' % (self.user,))

    def test_save_portfolio_entry(self):
        expected_output = {
            'success': True,
            'pf_entry_element_id': 'blargle',
            'portfolio_entry__pk': self.portfolio_entry.pk,
            'project__pk': self.project.id,
        }

        # check output
        self.assertEqual(
            simplejson.loads(self.post_result.content), expected_output)

        # postcondition
        portfolio_entry = PortfolioEntry.objects.get(
            pk=self.portfolio_entry.pk)
        self.assertEqual(portfolio_entry.project_description,
                         self.POST_data['project_description'])
        self.assertEqual(portfolio_entry.experience_description,
                         self.POST_data['experience_description'])
        self.assert_(portfolio_entry.is_published, "pf entry is published.")
        self.assertFalse(portfolio_entry.receive_maintainer_updates)

        citations = Citation.untrashed.filter(portfolio_entry=portfolio_entry)
        for c in citations:
            self.assert_(c.is_published)

    def test_multiparagraph_contribution_description(self):
        """
        If a multi-paragraph project contribution description is submitted,
        display it as a multi-paragraph description.
        """
        self.assertContains(
            self.contribution_page,
            "<br />".join(self.experience_description))

    def test_multiparagraph_project_description(self):
        """
        If a multi-paragraph project description is submitted, display it as a
        multi-paragraph description.
        """
        self.assertContains(
            self.contribution_page, "<br />".join(self.project_description))


class GimmeJsonTellsAboutImport(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def gimme_json(self):
        url = reverse(mysite.profile.views.gimme_json_for_portfolio)
        response = self.login_with_client().get(url)
        return simplejson.loads(response.content)

    def get_paulproteus(self):
        return mysite.profile.models.Person.objects.get(
            user__username='paulproteus')

    def get_barry(self):
        return mysite.profile.models.Person.objects.get(user__username='barry')

    def get_n_min_ago(self, n):
        return datetime.datetime.utcnow() - datetime.timedelta(minutes=n)

    def test_import_running_false(self):
        "When there are no DIAs for past five minutes, import.running = False"
        # Create a DIA for paulproteus that is from ten minutes ago (but
        # curiously is still in progress)
        my_dia_but_not_recent = DataImportAttempt(
            date_created=self.get_n_min_ago(10),
            query="bananas", person=self.get_paulproteus())
        my_dia_but_not_recent.save()

        # Create a DIA for Barry that is in progress, but ought not be
        # included in the calculation by gimme_json_for_portfolio
        not_my_dia = DataImportAttempt(date_created=self.get_n_min_ago(1),
                                       query="banans",
                                       person=self.get_barry())
        not_my_dia.save()

        # Verify that the JSON reports import running is False
        self.assertFalse(self.gimme_json()['import']['running'])

    def test_for_running_import(self):
        '''When there are dias for the past five minutes, import.running =
        True and progress percentage is accurate'''
        # Create a DIA for paulproteus that is from one minutes ago (but
        # curiously is still in progress)
        my_incomplete_recent_dia = DataImportAttempt(
            date_created=self.get_n_min_ago(1),
            query="bananas", person=self.get_paulproteus(), completed=False)
        my_incomplete_recent_dia.save()

        my_completed_recent_dia = DataImportAttempt(
            date_created=self.get_n_min_ago(1),
            query="bananas", person=self.get_paulproteus(), completed=True)
        my_completed_recent_dia.save()

        # Create a DIA that is in progress, but ought not be
        # included in the calculation by gimme_json_for_portfolio
        # because it doesn't belong to the logged-in user
        not_my_dia = DataImportAttempt(
            date_created=self.get_n_min_ago(1), person=self.get_barry(),
            query="bananas")
        not_my_dia.save()

        self.assert_(
            self.gimme_json()['import']['running'],
            "JSON reflects that an import is running")
        self.assertEqual(
            self.gimme_json()['import']['progress_percentage'], 50,
            "JSON reflects that import is at 50% progress")

        # Now let's make them all completed
        my_incomplete_recent_dia.completed = True
        my_incomplete_recent_dia.save()

        self.assertFalse(
            self.gimme_json()['import']['running'],
            "After all DIAs are completed, JSON reflects that no import is "
            "running.")


class PortfolioEntryAdd(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_portfolio_entry_add(self):
        # preconditions
        self.assertEqual(
            Project.objects.filter(name='new project name').count(), 0,
            ("expected precondition: there's no project "
             "named 'new project name'")
        )
        self.assertEqual(PortfolioEntry.objects.filter(
            project__name='new project name').count(), 0, (
            "expected precondition: there's no portfolio entry for a project "
            "named 'new project name'")
        )

        # Here is what the JavaScript seems to POST.
        post_data = {
            'portfolio_entry__pk': 'undefined',
            'project_name': 'new project name',
            'project_description': 'new project description',
            'experience_description': 'new experience description',
            'receive_maintainer_updates': 'false',
            'pf_entry_element_id': 'element_18',
        }
        url = reverse(mysite.profile.views.save_portfolio_entry_do)
        response = self.login_with_client().post(url, post_data)
        # Check side-effects

        self.assertEqual(Project.objects.filter(
            name='new project name').count(), 1, (
            "expected: after POSTing to view, there's a project named 'new "
            "project name'")
        )
        self.assertEqual(PortfolioEntry.objects.filter(
            person__user__username='paulproteus',
            project__name='new project name').count(), 1, (
            "expected: after POSTing to view, there's a portfolio entry for "
            "paulproteus for a project named 'new project name'")
        )

        new_pk = PortfolioEntry.objects.get(
            person__user__username='paulproteus',
            project__name='new project name').pk
        new_project_id = PortfolioEntry.objects.get(
            person__user__username='paulproteus',
            project__name='new project name').project.id

        # Check response

        expected_response_obj = {
            'success': True,
            'pf_entry_element_id': 'element_18',
            'project__pk': new_project_id,
            'portfolio_entry__pk': new_pk,
        }
        self.assertEqual(simplejson.loads(response.content),
                         expected_response_obj)


class OtherContributors(WebTest):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def test_list_other_contributors(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        barry = Person.objects.get(user__username='barry')
        project = Project(name='project',
                          icon_raw="static/no-project-icon-w=40.png")
        project.save()
        PortfolioEntry(project=project, person=paulproteus,
                       is_published=True).save()
        PortfolioEntry(project=project, person=barry, is_published=True).save()
        self.assertEqual(
            project.get_n_other_contributors_than(5, paulproteus),
            [barry]
        )
        self.assertEqual(
            project.get_n_other_contributors_than(5, barry),
            [paulproteus]
        )


class IgnoreNewDuplicateCitations(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_old_citations_supersede_their_new_duplicates(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        project1 = Project.create_dummy(name='1')
        project2 = Project.create_dummy(name='2')
        repo_search = DataImportAttempt.objects.get_or_create(
            source='rs', query='paulproteus', completed=True,
            person=paulproteus)[0]
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=project1,
                is_published=True,
                person=paulproteus)[0],
            languages='Python',
            data_import_attempt=repo_search
        )
        citation.save_and_check_for_duplicates()

        citation_of_different_project = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=project2,
                is_published=True,
                person=paulproteus)[0],
            languages='Python',
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=paulproteus)[0]
        )
        citation_of_different_project.save_and_check_for_duplicates()

        # This is the normal case: citations of different projects
        # do not supersede one another.
        self.assertEqual(
            list(Citation.untrashed.all().order_by('pk')),
            [citation, citation_of_different_project])

        # Create a second citation with all the same attributes as the first.
        # We will test that this one is superseded by its predecessor.
        username_search = DataImportAttempt.objects.get_or_create(
            source='ou', query='paulproteus', completed=True,
            person=paulproteus)[0]
        # As is realistic, this citation comes from an
        # Ohloh username search with the same results.
        citation2 = Citation(
            portfolio_entry=citation.portfolio_entry,
            languages=citation.languages,
            data_import_attempt=username_search
        )
        citation2.save_and_check_for_duplicates()

        # The second citation is ignored.
        self.assert_(citation2.ignored_due_to_duplicate)

        # The 'untrashed' manager picks up only first two distinct citations,
        # not the third (duplicate) citation
        self.assertEqual(
            list(Citation.untrashed.all().order_by('pk')),
            [citation, citation_of_different_project])


class PersonGetTagsForRecommendations(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_get_tags(self):
        pp = Person.objects.get(user__username='paulproteus')

        understands_not = TagType(name='understands_not')
        understands_not.save()
        understands = TagType(name='understands')
        understands.save()

        tag_i_understand = Tag(
            tag_type=understands, text='something I understand')
        tag_i_understand.save()
        tag_i_dont = Tag(tag_type=understands_not,
                         text='something I dont get')
        tag_i_dont.save()
        link_one = Link_Person_Tag(person=pp, tag=tag_i_understand)
        link_one.save()
        link_two = Link_Person_Tag(person=pp, tag=tag_i_dont)
        link_two.save()

        # This is the functionality we're testing
        self.assertEqual([tag_i_understand],
                         pp.get_tags_for_recommendations())


class MapTagsRemoveDuplicates(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        pp = Person.objects.get(user__username='paulproteus')

        understands_not = TagType(name='understands_not')
        understands_not.save()
        understands = TagType(name='understands')
        understands.save()
        can_pitch_in = TagType(name='can_pitch_in')
        can_pitch_in.save()

        tag_i_understand = Tag(
            tag_type=understands, text='something I understand')
        tag_i_understand.save()
        tag_i_dont = Tag(tag_type=understands_not,
                         text='something I dont get')
        tag_i_dont.save()
        tag_can_pitch_in = Tag(
            tag_type=can_pitch_in, text='something I UNDERSTAND')
        tag_can_pitch_in.save()
        link_one = Link_Person_Tag(person=pp, tag=tag_i_understand)
        link_one.save()
        link_two = Link_Person_Tag(person=pp, tag=tag_i_dont)
        link_two.save()
        link_three = Link_Person_Tag(person=pp, tag=tag_can_pitch_in)
        link_three.save()

        self.assertEqual(map(lambda x: x.lower(), pp.get_tag_texts_for_map()),
                         map(lambda x: x.lower(), ['something I understand']))


class ProjectGetMentors(WebTest):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    def test(self):
        '''This test creates:
        * one person who is listed as able to mentor in Banshee
        * one person who is not
        and asks the Banshee project to list its available mentors.'''
        Project.create_dummy(name='Banshee')
        can_mentor, _ = TagType.objects.get_or_create(name='can_mentor')

        willing_to_mentor_banshee, _ = Tag.objects.get_or_create(
            tag_type=can_mentor,
            text='Banshee')
        link = Link_Person_Tag(
            person=Person.objects.get(user__username='paulproteus'),
            tag=willing_to_mentor_banshee)
        link.save()


class SuggestLocation(WebTest):
    fixtures = ['user-paulproteus', 'user-barry',
                'person-barry', 'person-paulproteus']

    @skipIf(not mysite.profile.view_helpers.geoip_city_database_available(),
            "Skipping because high-resolution GeoIP data not available.")
    def test(self):
        data = {}
        data['geoip_has_suggestion'], data['geoip_guess'] = (
            mysite.profile.view_helpers.get_geoip_guess_for_ip("128.151.2.1"))
        self.assertEqual(data['geoip_has_suggestion'], True)
        self.assertEqual(data['geoip_guess'], "Rochester, NY, United States")

    @skipIf(not mysite.profile.view_helpers.geoip_city_database_available(),
            "Skipping because high-resolution GeoIP data not available.")
    def test_iceland(self):
        """We wrote this test because MaxMind gives us back a city in Iceland.
         That city has a name not in ASCII. MaxMind's database seems to store
         those values in Latin-1, so we verify here that we properly decode
         that to pure beautiful Python Unicode."""
        data = {}
        data['geoip_has_suggestion'], data['geoip_guess'] = (
            mysite.profile.view_helpers.get_geoip_guess_for_ip(
                "89.160.147.41"))
        self.assertEqual(data['geoip_has_suggestion'], True)
        self.assertEqual(type(data['geoip_guess']), unicode)

        # This test originally used this line of code:
        # correct_decoding = u'Reykjav\xedk, 10, Iceland'

        # But now we use this line of code, which doesn't include the rather
        # confusing numerals for region names:
        correct_decoding = u'Reykjav\xedk, Iceland'

        self.assertEqual(data['geoip_guess'], correct_decoding)


class EditBio(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus's profile
        * checks that they don't already have a bio that says "lookatme!"
        * clicks edit on the Info area
        * enters a string as bio
        * checks that his bio now contains string
        '''
        username = 'paulproteus'
        paulproteus_page = self.app.get('/people/paulproteus/', user=username)
        self.assertNotIn('lookatme!', paulproteus_page.content)

        edit_info_page = self.app.get('/profile/views/edit_info',  user=username)
        self.assertNotIn('lookatme!', edit_info_page.content)
        edit_info_form = edit_info_page.form
        edit_info_form['edit-tags-bio'] = 'lookatme!'
        response = edit_info_form.submit().follow()
        # Find the string we just submitted as our bio
        self.assertIn('lookatme!', response.content)
        self.assertEqual(Person.get_by_username('paulproteus').bio, "lookatme!")
        
        # now we should see our bio in the edit form
        edit_info_page = self.app.get('/profile/views/edit_info')
        self.assertIn('lookatme!', edit_info_page.content)


class EditHomepage(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus's profile
        * checks that there is no link to asheesh.org
        * clicks edit on the Info area
        * enters a link as Info
        * checks that his bio now contains "asheesh.org"
        '''
        username = 'paulproteus'
        paulproteus_page = self.app.get('/people/paulproteus/', user=username)
        # not so vain.. yet
        self.assertNotIn('asheesh.org', paulproteus_page.content)
        edit_info_page = self.app.get('/profile/views/edit_info', user=username)
        # make sure our bio is not already on the form
        self.assertNotIn('asheesh.org', edit_info_page.content)
        edit_info_form = edit_info_page.form
        # set the bio in the form
        edit_info_form['edit-tags-homepage_url'] = 'http://www.asheesh.org/'
        response = edit_info_form.submit()

        # find the string we just submitted as our bio
        self.assertEqual(Person.get_by_username('paulproteus').homepage_url,
                         "http://www.asheesh.org/")
        # now we should see our bio in the edit form
        edit_info_page = self.app.get('/profile/views/edit_info', user=username)
        self.assertIn('asheesh.org', edit_info_page.content)

        # try an invalid url
        edit_info_form = edit_info_page.form
        edit_info_form['edit-tags-homepage_url'] = 'atttp://www.asheesh.org/'
        response = edit_info_form.submit()
        self.assertIn('has_errors', response.content)
        # ensure it didn't get saved
        paulproteus_page = self.app.get('/people/paulproteus/', user=username)
        self.assertNotIn('atttp', paulproteus_page.content)


class EditIRCNick(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus's profile
        * checks that they don't already have a ircnick that says
          "paulproteusnick"
        * clicks edit on the Info area
        * enters a string as irc nick
        * checks that his irc nick now contains string
        '''
        username = 'paulproteus'
        paulproteus_page = self.app.get('/people/paulproteus/', user=username)
        self.assertNotIn('paulproteusnick', paulproteus_page.content)

        edit_info_page = self.app.get('/profile/views/edit_info',  user=username)
        # make sure our irc nick is not already on the form
        self.assertNotIn('paulproteusnick', edit_info_page.content)
        # set the irc nick in the form
        edit_info_form = edit_info_page.form
        edit_info_form['edit-tags-irc_nick'] = 'paulproteusnick'
        response = edit_info_form.submit().follow()
        # find the string we just submitted as our irc nick
        self.assertIn('paulproteusnick', response.content)

        # Confirm that the irc nick has been saved in db
        self.assertEqual(Person.get_by_username('paulproteus')
                         .irc_nick, "paulproteusnick")

        # now we should see our irc nick in the edit form
        edit_info_page = self.app.get('/profile/views/edit_info',  user=username)
        self.assertIn('paulproteusnick', edit_info_page.content)


class EditContactBlurbForwarderification(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * a controller called put_forwarder_in_contact_blurb_if_they_want()
          takes a string which is what someone inputs as their contact info
          blurb
        * it also takes said person's username or person object or something
        * we're testing this:
            - the controller returns a string which is the same as the one
              that it received, except $fwd is replaced with the output of
              generate_forwarder
            - the Forwarder db table contains a row for our new forwarder
              (which we created with the generate_forwarder controller)
        '''
        # grab asheesh by the horns
        sheesh = mysite.profile.models.Person.get_by_username('paulproteus')
        # make them a forwarder
        mysite.base.view_helpers.generate_forwarder(sheesh.user)
        # we have a string that contains the substr $fwd
        mystr = "email me here: $fwd.  it'll be great"
        user_to_forward_to = User.objects.get(username='paulproteus')
        # we run this string through a controller called forwarderify
        mystr_forwarderified = (
            mysite.base.view_helpers.
            put_forwarder_in_contact_blurb_if_they_want(
                mystr, user_to_forward_to)
        )
        our_forwarder = mysite.profile.models.Forwarder.objects.get(
            user=user_to_forward_to)
        output = "email me here: %s@%s .  it'll be great" % (
            our_forwarder.address, settings.FORWARDER_DOMAIN)
        # ^note that we throw in a zero-width string after the forwarder to
        # make sure it that the urlizetrunc filter, in the template,
        # linkifies it correctly.

        # make sure our forwarder that we just made hasn't expired
        self.assert_(our_forwarder.expires_on > datetime.datetime.utcnow())
        # we test that the result contains, as a substr, the output of a call
        # to generate_forwarder
        self.assertEqual(mystr_forwarderified, output)


class EditContactBlurb(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus' profile
        * checks that it doesn't say "bananas"
        * clicks edit in the info area
        * checks that the input field for "how to contact me" doesn't say
          bananas
        * enters bananas under the "how to contact me" section
        * submits
        * checks that his profile now says "bananas"
        * clicks edit in the info area again
        * checks that the input field for "how to contact me" now says bananas
        * removes email address from user
        * enters contact blurb containing $fwd
        * makes sure that the user gets an error message
        '''
        username = 'paulproteus'
        paulproteus_page = self.app.get('/people/paulproteus/', user=username)
        self.assertNotIn('bananas', paulproteus_page.content)

        edit_info_page = self.app.get('/profile/views/edit_info', user=username)
        # make sure our contact info is not already on the form
        self.assertNotIn('bananas', edit_info_page.content)

        edit_info_form = edit_info_page.form
        # set the contact info in the form
        edit_info_form['edit-tags-contact_blurb'] = 'bananas'
        response = edit_info_form.submit().follow()
        # find the string we just submitted as our contact info
        self.assertIn('bananas', response.content)

        # Confirm that the person object's attribute has been saved properly in db
        asheesh = Person.get_by_username('paulproteus')
        self.assertEqual(asheesh.contact_blurb, "bananas")

        # now we should see our contact info in the edit form
        edit_info_page = self.app.get('/profile/views/edit_info', user=username)
        # make sure our contact info is not already on the form
        self.assertIn('bananas', edit_info_page.content)

        # delete asheesh's email
        asheesh_user = asheesh.user
        asheesh_user.email = ''
        asheesh_user.save()
        contact_blurb = 'email me here: $fwd'
        contact_blurb_escaped = 'email me here: $fwd'
        homepage_url = 'http://mysite.com/'

        # also enter a homepage so that we can make sure that this gets saved
        # despite our error with the forwarder stuff
        edit_info_form = edit_info_page.form
        edit_info_form['edit-tags-contact_blurb'] = contact_blurb
        edit_info_form['edit-tags-homepage_url']= homepage_url
        response = edit_info_form.submit() 
        # make sure that they got an error message
        self.assertIn('contact_blurb_error', response.content)
        # make sure the form remembered the contact blurb that the user posted
        self.assertIn(contact_blurb_escaped, response.content)

        # make sure that their homepage was saved to the database
        asheesh = Person.get_by_username('paulproteus')
        self.assertEqual(asheesh.homepage_url, homepage_url)

    def test_blurb_with_irc_info(self):
        '''
        * Goes to paulproteus' profile
        * clicks edit in the info area
        * enters irc url under the "how to contact me" section
        * submits
        * checks that his profile now has irc url
        '''
        username = 'paulproteus'
        irc_url = 'irc://irc.freenode.net/openhatch'
        edit_info_page = self.app.get('/profile/views/edit_info', user=username)

        # set the contact info in the form
        edit_info_form = edit_info_page.form
        edit_info_form['edit-tags-contact_blurb'] = irc_url
        response = edit_info_form.submit().follow()
        # verify that the irc url is there
        self.assertIn(irc_url, response.content)

        # verify that contact_blurb is saved
        asheesh = Person.get_by_username('paulproteus')
        self.assertEqual(asheesh.contact_blurb, irc_url)

        # verify that irc url is not a link on view profile page
        paulproteus_page = self.app.get('/people/paulproteus/', user=username)
        self.assertNotIn('<a[^>]*>[^<]*irc[^<]*<\/a>', paulproteus_page.content)


class PeopleSearchProperlyIdentifiesQueriesThatFindProjects(WebTest):

    def test_one_valid_project(self):
        # make a project called Banana
        # query for that, but spelled bANANA
        # look in the template and see that projects_that_match_q_exactly ==
        # ['Banana']
        mysite.search.models.Project.create_dummy(
            name='Banana',
            cached_contributor_count=1)
        url = reverse(mysite.profile.views.people)
        response = self.client.get(url, {'q': 'bANANA'})
        self.assertEqual(response.context[0]['projects_that_match_q_exactly'],
                         [Project.objects.get(name='Banana')])

    def test_one_empty_project(self):
        # make a project called Banana
        # query for that, but spelled bANANA
        # look in the template and see that projects_that_match_q_exactly ==
        # ['Banana']
        mysite.search.models.Project.create_dummy(
            name='Banana',
            cached_contributor_count=0)
        url = reverse(mysite.profile.views.people)
        response = self.client.get(url, {'q': 'bANANA'})
        self.assertEqual(response.context[0]['projects_that_match_q_exactly'],
                         [])


class PeopleFinderClasses(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self, *args, **kwargs):
        super(PeopleFinderClasses, self).setUp(*args, **kwargs)
        self.person = mysite.profile.models.Person.objects.get(
            user__username='paulproteus')
        self.project = Project.create_dummy(name='Banshee')

    def test_wannahelp_query_with_zero_hits(self):
        whq = mysite.profile.view_helpers.WannaHelpQuery('banshee')
        self.assertEqual([], list(whq.people))

    def test_wannahelp_query_with_one_hit(self):
        # This time, set Asheesh up as a Banshee wannahelper.
        self.project.people_who_wanna_help.add(self.person)
        note = WannaHelperNote.add_person_project(self.person, self.project)
        note.save()
        self.project.save()

        whq = mysite.profile.view_helpers.WannaHelpQuery('banshee')
        self.assertEqual(1, len(whq.people))
        self.assertEqual(self.person, whq.people[0])

    def test_project_query_with_zero_hits(self):
        pq = mysite.profile.view_helpers.ProjectQuery('banshee')
        self.assertEqual([], list(pq.people))

    def test_project_query_with_one_hit(self):
        # This time, set Asheesh up as a Banshee contributor.
        PortfolioEntry(project=self.project, person=self.person,
                       is_published=True).save()

        pq = mysite.profile.view_helpers.ProjectQuery('banshee')
        self.assertEqual(1, len(pq.people))
        self.assertEqual(self.person, pq.people[0])


class PeopleFinderTagQueryTests(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus',
                'user-barry', 'person-barry']

    def setUp(self, *args, **kwargs):
        super(PeopleFinderTagQueryTests, self).setUp(*args, **kwargs)
        self.person = mysite.profile.models.Person.objects.get(
            user__username='paulproteus')

    def test_tag_type_query_with_zero_hits(self):
        tq = mysite.profile.view_helpers.TagQuery('can_mentor', 'python')
        self.assertEqual([], list(tq.people))

    def test_tag_type_query_with_zero_hits_and_busted_tag(self):
        tq = mysite.profile.view_helpers.TagQuery('lol_no_such_tag', 'python')
        self.assertEqual([], list(tq.people))

    def test_tag_type_query_with_one_hit_case_insensitive(self):
        # This time, set up Asheesh as a python mentor
        can_mentor, _ = TagType.objects.get_or_create(name='can_mentor')
        willing_to_mentor_python, _ = Tag.objects.get_or_create(
            tag_type=can_mentor,
            text='Python')
        link = Link_Person_Tag(person=self.person,
                               tag=willing_to_mentor_python)
        link.save()

        tq = mysite.profile.view_helpers.TagQuery('can_mentor', 'python')
        self.assertEqual([self.person], list(tq.people))

    def test_tag_type_query_with_one_hit_with_distraction_tags(self):
        # This time, set up Asheesh as a python mentor
        can_mentor, _ = TagType.objects.get_or_create(name='can_mentor')
        understands, _ = TagType.objects.get_or_create(name='understands')
        willing_to_mentor_python, _ = Tag.objects.get_or_create(
            tag_type=can_mentor,
            text='Python')
        willing_to_mentor_banshee, _ = Tag.objects.get_or_create(
            tag_type=can_mentor,
            text='Banshee')
        understands_unit_testing, _ = Tag.objects.get_or_create(
            tag_type=can_mentor,
            text='unit testing')
        link = Link_Person_Tag(person=self.person,
                               tag=willing_to_mentor_python)
        link.save()
        link = Link_Person_Tag(person=self.person,
                               tag=willing_to_mentor_banshee)
        link.save()
        link = Link_Person_Tag(person=self.person,
                               tag=understands_unit_testing)
        link.save()

        tq = mysite.profile.view_helpers.TagQuery('can_mentor', 'python')
        self.assertEqual([self.person], list(tq.people))

    def test_all_tags_query_with_zero_hits(self):
        atq = mysite.profile.view_helpers.AllTagsQuery('python')
        self.assertEqual([], list(atq.people))

    def test_all_tags_query_with_one_hit(self):
        # This time, set up Asheesh as a python mentor
        can_mentor, _ = TagType.objects.get_or_create(name='can_mentor')
        willing_to_mentor_python, _ = Tag.objects.get_or_create(
            tag_type=can_mentor,
            text='Python')
        link = Link_Person_Tag(person=self.person,
                               tag=willing_to_mentor_python)
        link.save()

        atq = mysite.profile.view_helpers.AllTagsQuery('python')
        self.assertEqual([self.person], list(atq.people))

    def test_all_tags_insenstive_case_search_a_name(self):
        # query with person named 'Asheesh', case insenstive, will
        # return the same person (also AllTagsQuery will find a person named
        # Asheesh, even if a tag wasn't used)
        atq1 = mysite.profile.view_helpers.AllTagsQuery('ASHEESH')
        atq2 = mysite.profile.view_helpers.AllTagsQuery('asheesh')
        self.assertEqual(list(atq1.people), list(atq2.people))

    def test_all_tags_insensitive_case_search_multiple_names(self):
        # get Barry and Asheesh out of the model
        person_last_name_spinoza = mysite.profile.models.Person.objects.get(
            user__last_name__iexact='spinoza')
        person_first_name_asheesh = mysite.profile.models.Person.objects.get(
            user__first_name__iexact='asheesh')

        # send query to AllTagsQuery
        atq = mysite.profile.view_helpers.AllTagsQuery('asheesh spinoza')
        atq_filter_spinoza = atq.people.filter(
            user__last_name__iexact="spinoza")[0]
        atq_filter_asheesh = atq.people.filter(
            user__first_name__iexact="asheesh")[0]

        # make sure we have people
        self.assertNotEqual(0, len(atq.people))

        # check that both Aseesh and Barry are in the AllTagsQuery result
        self.assertEqual(atq_filter_spinoza, person_last_name_spinoza)
        self.assertEqual(atq_filter_asheesh, person_first_name_asheesh)


class PeopleSearch(WebTest):

    def test_project_queries_are_distinct_from_tag_queries(self):
        # input "project:Exaile" into the search controller, check it outputs
        # {'q': 'Exaile', 'query_type': 'project'}
        data = mysite.profile.view_helpers.parse_string_query(
            "project:a_project_name")
        self.assertEqual(data['q'], 'a_project_name')
        self.assertEqual(data['query_type'], 'project')

        data = mysite.profile.view_helpers.parse_string_query(
            "a_tag_name_or_whatever")
        self.assertEqual(data['q'], 'a_tag_name_or_whatever')
        self.assertEqual(data['query_type'], 'all_tags')

    def test_tokenizer_parses_quotation_marks_correctly_but_if_they_are_missing_greedily_assumes_they_were_there(self):
        data = mysite.profile.view_helpers.parse_string_query(
            'project:"Debian GNU/Linux"')
        self.assertEqual(data['q'], 'Debian GNU/Linux')
        self.assertEqual(data['query_type'], 'project')

        data = mysite.profile.view_helpers.parse_string_query(
            'project:Debian GNU/Linux')
        self.assertEqual(data['q'], 'Debian GNU/Linux')
        self.assertEqual(data['query_type'], 'project')

    def test_tokenizer_picks_up_on_tag_type_queries(self):
        for tag_type_short_name in (mysite.profile.models.
                                    TagType.short_name2long_name):
            query = "%s:yourmom" % tag_type_short_name
            data = mysite.profile.view_helpers.parse_string_query(query)
            self.assertEqual(data['q'], 'yourmom')
            self.assertEqual(data['query_type'], tag_type_short_name)

    def test_tokenizer_ignores_most_colon_things(self):
        query = "barbie://queue"
        data = mysite.profile.view_helpers.parse_string_query(query)
        self.assertEqual(data['q'], query)
        self.assertEqual(data['query_type'], 'all_tags')


class PostfixForwardersOnlyGeneratedWhenEnabledInSettings(WebTest):

    def setUp(self):
        self.original_value = django.conf.settings.POSTFIX_FORWARDER_TABLE_PATH
        django.conf.settings.POSTFIX_FORWARDER_TABLE_PATH = None

    @mock.patch('mysite.profile.tasks.RegeneratePostfixAliasesForForwarder.'
                'update_table')
    def test(self, mock_update_table):
        task = mysite.profile.tasks.RegeneratePostfixAliasesForForwarder()
        task.run()
        self.assertFalse(mock_update_table.called)

    def tearDown(self):
        django.conf.settings.POSTFIX_FORWARDER_TABLE_PATH = self.original_value


class PostmapBinaryCalledIfExists(WebTest):

    @mock.patch('os.system')
    def test(self, mock_update_table):
        with mock.patch('mysite.base.depends.postmap_available') as a:
            task = mysite.profile.tasks.RegeneratePostfixAliasesForForwarder()
            a.return_value = True
            task.run()
            self.assertTrue(os.system.called)


class PostmapBinaryNotCalledIfDoesNotExist(WebTest):

    @mock.patch('os.system')
    def test(self, mock_update_table):
        with mock.patch('mysite.base.depends.postmap_available') as a:
            task = mysite.profile.tasks.RegeneratePostfixAliasesForForwarder()
            a.return_value = False
            task.run()
            self.assertFalse(os.system.called)


class PostFixGeneratorList(WebTest):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
                'person-paulproteus']

    def test(self):
        # create two people
        #  one who has an email address list in our database
        asheesh = User.objects.get(username='paulproteus')
        #  one who does not
        barry = User.objects.get(username='barry')
        barry.email = ''
        barry.save()
        # make a row in the forwarder table for each of these people
        mysite.base.view_helpers.generate_forwarder(barry)
        mysite.base.view_helpers.generate_forwarder(asheesh)
        # run the function in Forwarder which creates/updates the list of
        # user/forwarder pairs for postfix to generate forwarders for
        what_we_get = (mysite.profile.models.Forwarder.
                       generate_list_of_lines_for_postfix_table())

        what_we_want = [mysite.profile.models.Forwarder.objects.filter(
            user__username='paulproteus')[0].generate_table_line()]
        # make sure that the list of strings that we get back contains an item
        # for the user with an email address and no item for the user without
        self.assertEqual(what_we_get, what_we_want)


class EmailForwarderGarbageCollection(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    # create a bunch of forwarders for all possibilities given the options:
    #     "expired," "should no longer be displayed"
    # (except if it's expired it definitely should no longer be displayed)
    # run garbage collection
    # make sure that whatever should have happened has happened

    def test(self):
        # args:
        # valid = True if we want a forwarder with expires_on in the future
        # new_enough_for_dispay = True iff we want a forwarder whose
        # stops_being_listed_on date is in the future
        def create_forwarder(address, valid, new_enough_for_display):
            expires_on_future_number = valid and 1 or -1
            stops_being_listed_on_future_number = (new_enough_for_display
                                                   and 1 or -1)
            expires_on = (datetime.datetime.utcnow() +
                          expires_on_future_number *
                          datetime.timedelta(minutes=10))
            stops_being_listed_on = (datetime.datetime.utcnow() +
                                     stops_being_listed_on_future_number *
                                     datetime.timedelta(minutes=10))
            user = User.objects.get(username="paulproteus")
            new_mapping = mysite.profile.models.Forwarder(
                address=address, expires_on=expires_on, user=user,
                stops_being_listed_on=stops_being_listed_on)
            new_mapping.save()
            return new_mapping
        # asheesh wants a forwarder in his profile.  oh yes he does.
        sheesh = mysite.profile.models.Person.get_by_username('paulproteus')
        sheesh.contact_blurb = u'$fwd'
        sheesh.save()

        # Create a distraction user who does not want a forwarder
        mysite.profile.models.Person.create_dummy()

        valid_new = create_forwarder('orange@domain.com', 1, 1)
        valid_old = create_forwarder('red@domain.com', 1, 0)
        invalid = create_forwarder('purple@domain.com', 0, 0)
        # with any luck, the below will call this:
        # mysite.profile.models.Forwarder.garbage_collect()
        mysite.profile.tasks.GarbageCollectForwarders().run()
        # valid_new should still be in the database
        # there should be no other forwarders for the address that valid_new
        # has
        self.assertEqual(1, mysite.profile.models.Forwarder.objects.filter(
            pk=valid_new.pk).count())
        self.assertEqual(1, mysite.profile.models.Forwarder.objects.filter(
            address=valid_new.address).count())
        # valid_old should still be in the database
        self.assertEqual(1, mysite.profile.models.Forwarder.objects.filter(
            pk=valid_old.pk).count())
        # invalid should not be in the database
        self.assertEqual(0, mysite.profile.models.Forwarder.objects.filter(
            pk=invalid.pk).count())
        # there should be 2 forwarders in total: we lost one
        forwarders = mysite.profile.models.Forwarder.objects.all()
        self.assertEqual(2, forwarders.count())

        # Now if we delete both those forwarders, and re-generate, we get one
        # in the DB.
        mysite.profile.models.Forwarder.objects.all().delete()
        mysite.profile.tasks.GarbageCollectForwarders().run()
        forwarders = mysite.profile.models.Forwarder.objects.all()
        self.assertEqual(1, forwarders.count())


class EmailForwarderResolver(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    '''
    * put some mappings of forwarder addresses to dates and user objects in
      the Forwarder table
    * one of these will be expired
    * one of these will not
    * try
        * email forwarder address that's not in the database at all
        * email forwarder that's in the db but is expired
        * email forwarder that's in the db and is not expired
    '''
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        # this function was only being used by this test--so i moved it here.
        # it was in base/view_helpers --parker
        def get_email_address_from_forwarder_address(forwarder_address):
            Forwarder = mysite.profile.models.Forwarder
            # look in Forwarder model
            # see if the forwarder address that they gave us is expired
            # if it isn't return the user's real email address
            # if it is expired, or if it's not in the table at all, return None
            try:
                return Forwarder.objects.get(
                    address=forwarder_address,
                    expires_on__gt=datetime.datetime.utcnow()).user.email
            except Forwarder.DoesNotExist:
                return None

        def test_possible_forwarder_address(address, future,
                                            actually_create, should_work):
            future_number = future and 1 or -1
            if actually_create:
                expiry_date = datetime.datetime.utcnow(
                ) + future_number * datetime.timedelta(minutes=10)
                user = User.objects.get(username="paulproteus")
                new_mapping = mysite.profile.models.Forwarder(
                    address=address, expires_on=expiry_date, user=user)
                new_mapping.save()

            output = get_email_address_from_forwarder_address(address)
            if should_work:
                self.assertEqual(output, user.email)
            else:
                self.assertEqual(output, None)

        # this one hasn't expired yet
        test_possible_forwarder_address("apples", True, True, True)

        # this one has already expired
        test_possible_forwarder_address("bananas", False, True, False)

        # this one isn't in the table at all
        test_possible_forwarder_address("oranges", True, False, False)


class ForwarderGetsCreated(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        # paulproteus has $fwd in his contact blurb
        p = Person.get_by_username('paulproteus')
        p.contact_blurb = "hi, $fwd!"
        p.save()

        # no forwarder in the db
        self.assertFalse(Forwarder.objects.all())

        # now we GET the profile...
        response = self.client.get(p.profile_url)

        new_fwd = Forwarder.objects.all()[0]
        self.assert_(new_fwd)

        # the page will contain the whole string because it's in the mailto:
        self.assertContains(response, new_fwd.address)


class PersonCanSetHisExpandNextStepsOption(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_set_to_true(self):
        # Starts as false
        p = Person.objects.get(user__username='paulproteus')
        p.expand_next_steps = False
        p.save()

        # Now, set to True...
        url = mysite.profile.views.set_expand_next_steps_do
        response = self.login_with_client().post(reverse(url), {'value': 'True'})
        p = Person.objects.get(user__username='paulproteus')
        self.assert_(p.expand_next_steps)
        # FIXME test response

    def test_set_to_false(self):
        # Starts as True
        p = Person.objects.get(user__username='paulproteus')
        p.expand_next_steps = True
        p.save()

        # Now, set to False...
        url = mysite.profile.views.set_expand_next_steps_do
        response = self.login_with_client().post(reverse(url), {'value': 'False'})
        p = Person.objects.get(user__username='paulproteus')
        self.assertFalse(p.expand_next_steps)


class PeopleMapForNonexistentProject(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        mock_request = ObjectFromDict(
            {u'GET': {u'q': u'project:Phorum'},
             u'user': User.objects.get(username='paulproteus')})
        mysite.profile.views.people(mock_request)
        # Yay, no exception.

    def test_icanhelp(self):
        mock_request = ObjectFromDict(
            {u'GET': {u'q': u'icanhelp:Phorum'},
             u'user': User.objects.get(username='paulproteus')})
        mysite.profile.views.people(mock_request)
        # Yay, no exception.


class SaveReordering(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        # Log in
        client = self.login_with_client()

        paul = Person.get_by_username('paulproteus')

        pfes = [
            PortfolioEntry.create_dummy_with_project(
                person=paul, sort_order=-1),
            PortfolioEntry.create_dummy_with_project(
                person=paul, sort_order=-2),
        ]

        def get_ordering():
            response = client.get(
                reverse(mysite.profile.views.gimme_json_for_portfolio))
            obj = simplejson.loads(response.content)
            return [pfe['pk'] for pfe in obj['portfolio_entries']]

        ordering_beforehand = get_ordering()

        self.assertEqual(ordering_beforehand, [pfes[0].pk, pfes[1].pk])

        # POST to a view with a list of ids
        view = reverse(mysite.base.views.save_portfolio_entry_ordering_do)
        client.post(view, {'sortable_portfolio_entry[]': [str(pfes[1].pk),
                                                          str(pfes[0].pk)]})

        # Get the list of projects
        ordering_afterwards = get_ordering()

        # Verify that these projects have the right sort order
        self.assertEqual(ordering_afterwards, [pfes[1].pk, pfes[0].pk])


class ArchiveProjects(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        # Log in
        client = self.login_with_client()

        paul = Person.get_by_username('paulproteus')

        pfes = [
            PortfolioEntry.create_dummy_with_project(
                person=paul, sort_order=-1),
            PortfolioEntry.create_dummy_with_project(
                person=paul, sort_order=-2),
        ]

        # POST to a view with a list of ids
        view = reverse(mysite.base.views.save_portfolio_entry_ordering_do)
        client.post(view, {
            'sortable_portfolio_entry[]':
            [str(pfes[0].pk), "FOLD", str(pfes[1].pk)]})

        this_should_be_archived = PortfolioEntry.objects.get(pk=pfes[1].pk)
        self.assert_(this_should_be_archived.is_archived)


class Notifications(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @staticmethod
    def get_email_context(recipient):
        """ This helper method retrieves the context of the email we're
        currently planning to send to the recipient. """

        # First move the timestamp back
        Timestamp.update_timestamp_for_string(
            send_emails.Command.TIMESTAMP_KEY,
            override_time=Timestamp.ZERO_O_CLOCK)
        command = mysite.profile.management.commands.send_emails.Command()
        context = command.get_context_for_email_to(recipient)
        return context

    @staticmethod
    def send_email_and_get_outbox():
        command = mysite.profile.management.commands.send_emails.Command()
        command.handle()
        return mail.outbox

    def assert_only_these_people_were_emailed(self, contributors, outbox):
        """Assert that the ONLY email recipients are the contributors who are
        news to each other"""

        recipient_emails = []
        for email in outbox:
            # By the way, there should be only one recipient per email
            self.assertEqual(len(email.to), 1)
            recipient_emails.append(email.to[0])

        contributor_emails = [c.user.email for c in contributors]

        self.assertEqual(sorted(recipient_emails), sorted(contributor_emails))

    def add_two_people_to_a_project_and_send_emails(
            self, people_want_emails=True, how_to_add_people=None,
            outbox_or_context=None, emails_should_actually_be_sent=True):

        self.assert_(outbox_or_context in ['outbox', 'context'])

        time_range_endpoint_at_func_top = (
            send_emails.Command.get_time_range_endpoint_of_last_email())

        project_with_two_participants = Project.create_dummy()

        participants_who_are_news_to_each_other = []  # initial value

        if not how_to_add_people:
            how_to_add_people = [Notifications.add_contributor,
                                 Notifications.add_contributor]

        for index, add_person_function in enumerate(how_to_add_people):
            participant = Person.create_dummy(
                first_name=str(index),
                email_me_re_projects=people_want_emails)
            add_person_function(participant, project_with_two_participants)
            participants_who_are_news_to_each_other.append(participant)

        self.assertEqual(len(participants_who_are_news_to_each_other), 2)

        output = None

        if outbox_or_context == 'outbox':
            outbox = Notifications.send_email_and_get_outbox()
            output = outbox
            if emails_should_actually_be_sent:
                # The timestamp log should have been modified since the top of
                # the function.
                self.assert_(
                    send_emails.Command.get_time_range_endpoint_of_last_email(
                    )
                    > time_range_endpoint_at_func_top)

        if outbox_or_context == 'context':
            command = mysite.profile.management.commands.send_emails.Command()
            email_contexts = {}  # initial value
            for participant in participants_who_are_news_to_each_other:
                email_context = command.get_context_for_email_to(participant)
                email_contexts[participant.pk] = email_context
            output = email_contexts

        return (participants_who_are_news_to_each_other, output)

    @staticmethod
    def add_contributor(person, project):
        PortfolioEntry.create_dummy(
            person=person, project=project, is_published=True)

    @staticmethod
    def add_contributor_with_maintainer_status(person, project, is_maintainer):
        PortfolioEntry.create_dummy(
            person=person, project=project, is_published=True,
            receive_maintainer_updates=is_maintainer)

    @staticmethod
    def add_wannahelper(person, project, created_date=None):
        project.people_who_wanna_help.add(person)
        note = WannaHelperNote.add_person_project(person, project)
        if created_date:
            note.created_date = created_date
            note.save()
        project.save()

    def test_email_the_people_with_checkboxes_checked(self):
        contributors, outbox = (
            self.add_two_people_to_a_project_and_send_emails(
                people_want_emails=True, outbox_or_context='outbox'))

        self.assertEqual(len(outbox), 2)

        self.assert_only_these_people_were_emailed(contributors, outbox)

    def test_dont_email_the_people_with_checkboxes_cleared(self):

        contributors, outbox = (
            self.add_two_people_to_a_project_and_send_emails(
                people_want_emails=False, outbox_or_context='outbox'))

        self.assertEqual(len(outbox), 0)

    # Test the content of the email (test the rendered template, and/or
    # test the context passed to that template)
    def test_email_context_contains_contributors(self):

        paul = Person.get_by_username('paulproteus')

        # To set up this test, let's create a project
        project = Project.create_dummy()

        # Paul will be the recipient of the email, and he's a contributor to
        # the project created above, so he'll be getting information about that
        # project's recent activity in his periodic email
        PortfolioEntry.create_dummy(
            person=paul, project=project, is_published=True)

        NUMBER_OF_NEW_CONTRIBUTORS_OTHER_THAN_PAUL = 5

        # 5 people have joined this project today
        for i in range(NUMBER_OF_NEW_CONTRIBUTORS_OTHER_THAN_PAUL):
            p = Person.create_dummy()
            PortfolioEntry.create_dummy(
                person=p, project=project, is_published=True)

        # 1 person joined this project two weeks ago (too long ago to mention
        # in this email)
        now = datetime.datetime.utcnow()
        yesterday = now - datetime.timedelta(hours=24)
        eight_days_ago = now - datetime.timedelta(days=8)

        Timestamp.update_timestamp_for_string(
            send_emails.Command.TIMESTAMP_KEY,
            override_time=yesterday)

        veteran = Person.create_dummy()
        veteran.user.first_name = 'VETERAN'
        veteran.user.save()
        PortfolioEntry.create_dummy(person=veteran,
                                    project=project,
                                    is_published=True,
                                    date_created=eight_days_ago)

        # Psst, notice that we have sent out a round of emails since the
        # veteran added the project to her profile. So the veteran should not
        # appear in the next round of periodic emails.

        # Let's assert that the email context contains enough information to
        # say that such and such a project received 6 contributors recently
        # and that here are the person objects for 3 of them

        new_contributors = list(project.get_contributors())
        new_contributors.remove(paul)
        new_contributors.remove(veteran)

        command = mysite.profile.management.commands.send_emails.Command()
        context = command.get_context_for_email_to(paul)

        project, actual_people = context['project2people'][0]

        # Assert that the truncated list of contributors that will appear in
        # the email is a subset of the people we added above
        for c in actual_people['display_these_contributors']:
            self.assert_(c in new_contributors)

        self.assertEqual(
            actual_people['contributor_count'],
            NUMBER_OF_NEW_CONTRIBUTORS_OTHER_THAN_PAUL + 1)

        self.assertEqual(actual_people['wannahelper_count'], 0)

        self.assertEqual(actual_people['display_these_wannahelpers'], [])

        command.handle()

        email_to_paul = None
        for email in mail.outbox:
            if email.to[0] == paul.user.email:
                email_to_paul = email
                break

        self.assert_(email_to_paul)
        text_msg, html_msg = email_to_paul.message().get_payload()

        for msg_encoded in [text_msg, html_msg]:
            msg = quopri.decodestring(msg_encoded.get_payload())
            for project, people_data in context['project2people']:
                contribs_count = str(people_data['contributor_count'])
                self.assert_(project.display_name in msg)
                self.assert_(contribs_count in msg)
                for p in people_data['display_these_contributors']:
                    self.assert_(p.user.username in msg)

        # context['new_wannahelpers']
        # context['recent_chatter_answers'],

    def test_you_appear_in_summary_sometimes(self):
        # If you're a newly marked contributor to project P, and there are
        # fewer than 3 other newly marked contributors to P, then you appear in
        # the shortlist of newly marked contributors to P.

        paul = Person.get_by_username('paulproteus')

        def get_contributors_data():
            context = Notifications.get_email_context(paul)
            project, contributors_data = context['project2people'][0]
            return contributors_data

        # To set up this test, let's create a project
        project = Project.create_dummy()

        # Paul will be the recipient of the email, and he's a contributor to
        # the project created above, so he'll be getting information about that
        # project's recent activity in his periodic email
        PortfolioEntry.create_dummy(
            person=paul, project=project, is_published=True)

        # Since paul is the only newly marked contributor to this project,
        # there will be no news to report, and by stipulation the context of
        # the email will simply be None
        self.assertEqual(Notifications.get_email_context(paul), None)

        number_of_new_contributors_other_than_paul = 2

        # 2 people have joined this project recently
        for i in range(number_of_new_contributors_other_than_paul):
            p = Person.create_dummy()
            PortfolioEntry.create_dummy(
                person=p, project=project, is_published=True)

        data = get_contributors_data()
        self.assertEqual(len(data['display_these_contributors']), 3)
        self.assert_(paul in data['display_these_contributors'])

        # Now add one more person
        p = Person.create_dummy()
        PortfolioEntry.create_dummy(
            person=p, project=project, is_published=True)

        data = get_contributors_data()
        self.assertEqual(len(data['display_these_contributors']), 3)
        self.assert_(paul not in data['display_these_contributors'])

        # Now let's test that when there's a project containing just paul, that
        # project doesn't show up in the summary (even when there are other
        # projects to speak of)
        solo_project = Project.create_dummy(name='solo project')
        PortfolioEntry.create_dummy(
            person=paul, project=solo_project, is_published=True)
        context = Notifications.get_email_context(paul)
        project2people = context['project2people']
        first_project, contributors_data = project2people[0]

        # The first project appears in the email
        self.assertEqual(first_project.name, project.name)

        # The second project doesn't appear
        self.assertEqual(len(project2people), 1)

    def test_dont_send_email_when_recipient_has_no_recent_fellow_contributors(
            self):
        # This recipient is the only recent member of her projects
        no_news_for_me = Person.create_dummy(email='dont_email_me@example.com')
        PortfolioEntry.create_dummy_with_project(
            person=no_news_for_me, is_published=True)

        # The person above should NOT get an email

        # We could now simply run the email sender and make sure that NO email
        # was sent. But this is consistent with a failure case, in which NO
        # email gets sent ever (for some reason). Because sending email to our
        # users is a pretty sensitive piece of functionality, I want to be
        # extra careful to test for failure cases. So I'll set up the database
        # so that some OTHER folks will get an email. Then we'll check to see
        # that no email was ever sent to the person named "no_news_for_me."

        project_with_two_contributors = Project.create_dummy()

        contributors_who_are_news_to_each_other = []  # initial value

        for i in range(2):
            contributor = Person.create_dummy(
                email='contributor.%d@example.com' % i)
            PortfolioEntry.create_dummy(
                person=contributor,
                project=project_with_two_contributors,
                is_published=True)
            contributors_who_are_news_to_each_other.append(contributor)

        outbox = Notifications.send_email_and_get_outbox()

        self.assertEqual(len(outbox), 2)

        self.assert_only_these_people_were_emailed(
            contributors_who_are_news_to_each_other,
            outbox)

    def test_dont_send_email_when_recipient_has_no_projects(self):
        # The recipient has no projects
        Person.create_dummy()

        # Assert that no emails were sent
        self.assertEqual(len(Notifications.send_email_and_get_outbox()), 0)

    # We need these functions a few times during this test
    @staticmethod
    def set_when_emails_were_last_sent(when):
        Timestamp.update_timestamp_for_string(
            send_emails.Command.TIMESTAMP_KEY,
            override_time=when)

    def try_to_send_some_emails(self, expect_success):
        add_and_send = self.add_two_people_to_a_project_and_send_emails
        people, outbox = add_and_send(
            how_to_add_people=[
                Notifications.add_contributor,
                Notifications.add_wannahelper],
            outbox_or_context='outbox',
            emails_should_actually_be_sent=expect_success)
        were_emails_sent = bool(outbox)
        self.assertEqual(expect_success, were_emails_sent)

    def test_we_dont_send_emails_more_than_we_should(self):
        # Test that, no matter what, we never send out emails more than once
        # every 24 hours.

        # Here we test two scenarios.

        # First, what if we (accidentally) run the send_emails command this
        # afternoon, when we sent the emails this morning?
        # We want to make sure that we can't accidentally send people two
        # emails in a single day...

        # Calculate some datetime objects we'll need during this test
        now = datetime.datetime.utcnow()

        just_under_24_hours = datetime.timedelta(hours=23, minutes=55)
        just_under_24_hours_ago = now - just_under_24_hours

        # Let's record that emails were sent within 24 hours
        Notifications.set_when_emails_were_last_sent(just_under_24_hours_ago)

        # Try to send emails, but expect no emails to be sent, because we've
        # recorded that we sent emails within 24 hours.
        self.try_to_send_some_emails(expect_success=False)

    def test_that_we_do_email_you_if_the_last_email_was_sent_long_enough_ago(
            self):

        # Now let's make sure that the converse scenario works as expected. We
        # sent the emails over 24 hours ago, and somebody runs the
        # send_emails command. In this scenario, emails SHOULD be sent.

        now = datetime.datetime.utcnow()
        just_over_24_hours = datetime.timedelta(hours=25)
        just_over_24_hours_ago = now - just_over_24_hours

        # Let's record that emails were sent just OVER 24 hours ago
        Notifications.set_when_emails_were_last_sent(just_over_24_hours_ago)

        # Try to send emails, but expect some emails to YES be sent, because
        # we've recorded that we sent emails over 24 hours ago.
        self.try_to_send_some_emails(expect_success=True)

    def test_get_maintainer_projects(self):
        """
        get_maintainer_projects returns only the projects for which the user
        has indicated that they want to receive maintainer updates.
        """
        person = Person.create_dummy()

        # three projects
        project_i_contributed_to = Project.create_dummy()
        project_i_wanna_help = Project.create_dummy()
        project_i_maintain = Project.create_dummy()

        # first project
        Notifications.add_contributor_with_maintainer_status(
            person, project_i_contributed_to, False)

        # second project
        Notifications.add_wannahelper(person, project_i_wanna_help)

        # third project
        Notifications.add_contributor_with_maintainer_status(
            person, project_i_maintain, True)

        maintainer_projects = (mysite.profile.management.commands.
                                   send_emails.Command.
                                   get_maintainer_projects(person))
        self.assertEqual(maintainer_projects, [project_i_maintain])

    def test_dont_tell_me_about_projects_where_i_am_the_only_participant(self):
        # FIXME: This will cease to make sense when we add project answers to
        # the email
        person = Person.create_dummy()
        project_i_wanna_help_and_contributed_to = Project.create_dummy()
        Notifications.add_contributor(
            person, project_i_wanna_help_and_contributed_to)
        Notifications.add_wannahelper(
            person, project_i_wanna_help_and_contributed_to)
        command = mysite.profile.management.commands.send_emails.Command()
        email_context = command.get_context_for_email_to(person)
        self.assertEqual(None, email_context)

    def test_dont_show_previously_mentioned_wannahelpers(self):
        # Don't email somebody about a wanna-helper who we've already emailed
        # them about

        # Here's the person we're going to email
        email_recipient = Person.create_dummy(email='recipient@example.com')
        # Here's a project they care about
        a_project = Project.create_dummy()
        # because they are a contributor
        Notifications.add_contributor(email_recipient, a_project)

        # Create two wannahelpers, one of them is new and the other is old
        new_wh = Person.create_dummy('new_wh@example.com')
        old_wh = Person.create_dummy('old_wh@example.com')

        now = datetime.datetime.utcnow()
        yesterday = now - datetime.timedelta(hours=24)
        a_few_days_ago = now - datetime.timedelta(days=3)

        # The timespan for this email is the last 24 hours
        Timestamp.update_timestamp_for_string(
            send_emails.Command.TIMESTAMP_KEY,
            override_time=yesterday)

        # This dude signs up to be a helper
        Notifications.add_wannahelper(new_wh, a_project)

        # This dude signed up too long ago to appear in this email
        Notifications.add_wannahelper(old_wh, a_project, a_few_days_ago)

        # Assert that the new w.h. was included in the email and the old was
        # not.
        command = mysite.profile.management.commands.send_emails.Command()
        email_context = command.get_context_for_email_to(email_recipient)
        self.assert_(email_context)
        project2people = email_context['project2people']
        self.assertEqual(len(project2people), 1)
        project, people = project2people[0]
        self.assertEqual(
            [new_wh],
            people['display_these_wannahelpers'],
        )


class PeopleMapSummariesAreCheap(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self, *args, **kwargs):
        # Call the parent setUp() method
        super(PeopleMapSummariesAreCheap, self).setUp(*args, **kwargs)

        # Give paulproteus some tag values
        self.paulproteus = Person.objects.get(user__username='paulproteus')

        understands = TagType(name='understands')
        understands.save()

        # Create 3 Tag objects
        Tag.objects.create(tag_type=understands, text='thing1')
        Tag.objects.create(tag_type=understands, text='thing2')
        Tag.objects.create(tag_type=understands, text='thing3')

        # Link them to the Person
        for tag in Tag.objects.all():
            Link_Person_Tag.objects.create(person=self.paulproteus, tag=tag)
        n = self.paulproteus.link_person_tag_set.all().count()
        self.assertEquals(3, n)

        # Give paulproteus some projects
        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name')[0],
                is_published=True,
                person=self.paulproteus)[0],
            languages='Python',
        )
        citation.save()

        citation = Citation(
            portfolio_entry=PortfolioEntry.objects.get_or_create(
                project=Project.objects.get_or_create(
                    name='project name2')[0],
                is_published=True,
                person=self.paulproteus)[0],
            languages='Python',
        )
        citation.save()

        # Now, start counting queries.
        self.old_settings_debug = getattr(settings, 'DEBUG', None)
        settings.DEBUG = True
        self.query_count = len(django.db.connection.queries)

    def tearDown(self, *args, **kwargs):
        super(PeopleMapSummariesAreCheap, self).tearDown(*args, **kwargs)
        now_query_count = len(django.db.connection.queries)
        settings.DEBUG = self.old_settings_debug

        # If we did 1 or fewer queries, then stop here.
        if now_query_count - self.query_count <= 1:
            return

        # Otherwise, let us examine all queries against OpenHatch models
        all_queries = django.db.connection.queries[self.query_count:]

        def is_openhatchy(query):
            if 'raw_sql' in query:
                sql = query['raw_sql']
            elif 'sql' in query:
                sql = query['sql']
            else:
                return False  # Odd, no SQL data here.

            if (sql.startswith('SELECT "django_') or
                    sql.startswith('SELECT `django_')):
                return False
            return True
        openhatchy_queries = filter(is_openhatchy, all_queries)
        if len(openhatchy_queries) > 1:
            pprint.pprint(openhatchy_queries)
            self.assertEqual(1, len(openhatchy_queries))

    def test_map_tag_texts(self):
        self.paulproteus.get_tag_texts_for_map()

    def test_project_list(self):
        self.paulproteus.get_list_of_all_published_projects()


class PeopleLocationData(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus',
                'user-barry', 'person-barry']

    def setUp(self, *args, **kwargs):
        super(PeopleLocationData, self).setUp(*args, **kwargs)
        self.old_settings_debug = getattr(settings, 'DEBUG', None)
        settings.DEBUG = True
        self.query_count = len(django.db.connection.queries)

    def tearDown(self, *args, **kwargs):
        super(PeopleLocationData, self).tearDown(*args, **kwargs)
        now_query_count = len(django.db.connection.queries)
        settings.DEBUG = self.old_settings_debug

        # If we did 1 or fewer queries, then stop here.
        if now_query_count - self.query_count <= 1:
            return

        # Otherwise, let us examine all queries against OpenHatch models
        all_queries = django.db.connection.queries[self.query_count:]

        def is_openhatchy(query):
            if 'raw_sql' not in query:
                return False
            if (query['raw_sql'].startswith('SELECT "django_') or
                    query['raw_sql'].startswith('SELECT `django_')):
                return False
            return True
        openhatchy_queries = filter(is_openhatchy, all_queries)
        if len(openhatchy_queries) > 1:
            pprint.pprint(openhatchy_queries)
            self.assertEqual(1, len(openhatchy_queries))


class ProfileApiTest(BasicHelpers):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(ProfileApiTest, self).setUp()
        portfolio_entry = PortfolioEntry.objects.get_or_create(
            project=Project.objects.get_or_create(
                name='project name')[0],
            person=Person.objects.get(user__username='paulproteus'),
            is_published=True)[0]

        citation = Citation(
            contributor_role='Did stuff',
            url='http://example.com/',
            portfolio_entry=portfolio_entry,
            data_import_attempt=DataImportAttempt.objects.get_or_create(
                source='rs', query='paulproteus', completed=True,
                person=Person.objects.get(user__username='paulproteus'))[0]
        )
        citation.save()

    def test_api_view_when_logged_in(self):
        self.client = self.login_with_client()
        response = self.client.get(
            '/+api/v1/profile/portfolio_entry/?format=json')
        parsed = simplejson.loads(response.content)
        self.assertEqual(1, parsed['meta']['total_count'])

    def test_api_view_when_logged_out(self):
        self.client.logout()
        # Test that user is logged out
        response = self.client.get('/+api/v1/delete_user_for_being_spammy/')
        self.assertEqual(302, response.status_code)

        response = self.client.get(
            '/+api/v1/profile/portfolio_entry/?format=json')
        parsed = simplejson.loads(response.content)
        self.assertEqual(0, parsed['meta']['total_count'])


class TestUserDeletion(BasicHelpers):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
                'person-paulproteus']

    def test_view_unauthenticated(self):
        response = self.client.get('/+api/v1/delete_user_for_being_spammy/')
        self.assertEqual(302, response.status_code)

    def test_view_as_barry(self):
        self.client = self.login_with_client_as_barry()
        response = self.client.get('/+api/v1/delete_user_for_being_spammy/')
        self.assertEqual(200, response.status_code)

    def test_actual_deletion_as_barry(self):
        self.client = self.login_with_client_as_barry()
        response = self.client.post('/+api/v1/delete_user_for_being_spammy/',
                                    {'username': 'paulproteus'})
        self.assertEqual(400, response.status_code)
        self.assert_(django.contrib.auth.models.User.objects.filter(
            username='paulproteus'))

    def test_actual_deletion_as_paulproteus(self):
        self.client = self.login_with_client()
        response = self.client.post('/+api/v1/delete_user_for_being_spammy/',
                                    {'username': 'barry'})
        self.assertEqual(302, response.status_code)
        self.assertFalse(django.contrib.auth.models.User.objects.filter(
            username='barry'))
        self.assertEqual(2, len(django.core.mail.outbox))

class TestBreakLongWordsFilter(WebTest):
    def test_too_shirt_to_break(self):
        eight_chars = 'abcdefgh'
        output = mysite.profile.templatetags.profile_extras.break_long_words(
            eight_chars)
        self.assertEqual(output, eight_chars)

    def test_simple_break(self):
        nine_chars = 'abcdefghi'
        nine_chars_plus_wbr = u'abcdefgh\u200bi'
        output = mysite.profile.templatetags.profile_extras.break_long_words(
            nine_chars)
        self.assertEqual(output, nine_chars_plus_wbr)

    def test_break_across_tag_boundaries(self):
        nine_chars = 'abc<i>defghi</i>'
        nine_chars_plus_wbr = u'abcdefgh\u200bi'
        output = mysite.profile.templatetags.profile_extras.break_long_words(
            nine_chars)
        self.assertEqual(output, nine_chars_plus_wbr)
