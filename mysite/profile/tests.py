# Imports {{{
from mysite.base.tests import make_twill_url, TwillTests
import mysite.account.tests

from mysite.search.models import Project
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_Person_Tag, Link_ProjectExp_Tag, DataImportAttempt, PortfolioEntry, Citation

import mysite.profile.views
import mysite.profile.models
import mysite.profile.controllers

from mysite.profile import views

from django.conf import settings

from mysite.customs import ohloh 

import re
from StringIO import StringIO
import urllib
import simplejson
import BeautifulSoup
import time
import datetime
import tasks 
import mock

import django.test
from django.test.client import Client
from django.core import management, serializers
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
# }}}

class ProfileTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus',
            'cchost-data-imported-from-ohloh']

    def testSlash(self):
        response = self.client.get('/people/')

    def test__portfolio_updates_when_citation_added_to_db(self):
        # {{{
        username = 'paulproteus'

        project_name = 'seeseehost'
        #description = 'did some work'
        #url = 'http://example.com/'
        paulproteus = Person.objects.get(user__username='paulproteus')
        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    is_published=True,
                    person=paulproteus)[0],
                distinct_months=1,
                languages='Python',
                )
        citation.save()

        # Verify that get_publish_portfolio_entries() works
        self.assert_('project name' in [pfe.project.name for pfe in paulproteus.get_published_portfolio_entries()])

        # }}}

    def test_change_my_name(self):
        """Test that user can change his/her first and last name, and that it appears in the logged-in user's profile page."""
        # {{{
        self.login_with_twill()

        tc.go(make_twill_url('http://openhatch.org/people/paulproteus'))

        # No named entered yet
        tc.notfind('Newfirst Newlast')

        # Let's go enter a name
        tc.go(make_twill_url('http://openhatch.org/edit/name'))
        tc.fv('edit_name', 'first_name', 'Newfirst')
        tc.fv('edit_name', 'last_name', 'Newlast')
        tc.submit()

        tc.url('/people/paulproteus')

        # Has name been entered correctly? Hope so!
        tc.find('Newfirst')
        tc.find('Newlast')
        # }}}

    # }}}

class DebTagsTests(TwillTests):
    # {{{

    def testAddOneDebtag(self):
        tag = views.add_one_debtag_to_project('alpine', 'implemented-in::c')
        self.assertEqual(views.list_debtags_of_project('alpine'),
                         ['implemented-in::c'])

    def testImportDebtags(self):
        views.import_debtags(cooked_string=
                                     'alpine: works-with::mail, protocol::smtp') # side effects galore!
        self.assertEqual(set(views.list_debtags_of_project('alpine')),
                         set(['works-with::mail', 'protocol::smtp']))
    # }}}

#class ExpTag(TwillTests):

# If you're looking for SourceForge and FLOSSMole stuff, look in the repository history.

class Info(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
            'person-paulproteus', 'cchost-data-imported-from-ohloh']

    tags = {
            'understands': ['ack', 'b', 'c'],
            'understands_not': ['dad', 'e', 'f'],
            'seeking': ['gone', 'h', 'i'],
            'studying': ['jam', 'k', 'l'],
            'can_mentor': ['mop', 'n', 'o'],
            }
    tags_2 = {
            'understands': ['Ack!', 'B!', 'C!'],
            'understands_not': ['dad', 'e', 'f'],
            'seeking': ['gone', 'h', 'i'],
            'studying': ['Jam?', 'K?', 'L?'],
            'can_mentor': ['mop', 'n', 'o'],
            }
    # FIXME: Test whitespace, too.

    # FIXME: Write a unit test for this.
    def update_tags(self, tag_dict):
        # {{{
        url = reverse(mysite.profile.views.edit_info)
        tc.go(make_twill_url(url))
        for tag_type_name in tag_dict:
            tc.fv('edit-tags', 'edit-tags-' + tag_type_name, ", ".join(tag_dict[tag_type_name]))
        tc.submit()

        # Check that at least the first tag made it into the database.
        self.assert_(list(Link_Person_Tag.objects.filter(
            tag__text=tag_dict.values()[0][0], person__user__username='paulproteus')))

        # Check that the output is correct.
        soup = BeautifulSoup.BeautifulSoup(tc.show())
        for tag_type_name in tag_dict:
            text = ''.join(soup(id='tags-%s' % tag_type_name)[0].findAll(text=True))
            self.assert_(', '.join(tag_dict[tag_type_name]) in ' '.join(text.split()))

        # Go back to the form and make sure some of these are there
        tc.go(make_twill_url(url))
        tc.find(tag_dict.values()[0][0])
        # }}}

    def test_tag_edit_once(self):
        # {{{
        self.login_with_twill()
        self.update_tags(self.tags)
        # }}}

    def test_tag_edit_twice(self):
        # {{{
        self.login_with_twill()
        self.update_tags(self.tags)
        self.update_tags(self.tags_2)
        # }}}

    # }}}

# Create a mock Ohloh get_contribution_info_by_username
mock_gcibu = mock.Mock()
# This object will always return:
mock_gcibu.return_value = ([{
        'man_months': 1,
        'project': u'MOCK ccHost',
        'project_homepage_url':
            u'http://wiki.creativecommons.org/CcHost',
        'first_commit_time':
            '2008-04-03T23:51:45Z',
        'primary_language': u'shell script'},
        ],
        None # WebResponse
        )

# Create a mock Ohloh get_contribution_info_by_ohloh_username
mock_gcibou = mock.Mock()
mock_gcibou.return_value = ([{
        'man_months': 1,
        'project': u'MOCK ccHost',
        'project_homepage_url':
            u'http://wiki.creativecommons.org/CcHost',
        'primary_language': u'Vala'}],
        None #WebResponse
        )

# Create a mock Launchpad get_info_for_launchpad_username
mock_giflu = mock.Mock()
mock_giflu.return_value = {
        'MOCK ccHost': {
            'url': 'http://launchpad.net/ccHost', # ok this url doesn't really exist
            'involvement_types': ['Bug Management', 'Bazaar Branches'],
            'languages': ['python', 'ruby'],
            }
        }

# FIXME: If this is made dynamically, it would be easier!
class MockFetchPersonDataFromOhloh(object):
    real_task_class = tasks.FetchPersonDataFromOhloh
    @classmethod
    def delay(*args, **kwargs):
        "Don't enqueue a background task. Just run the task."
        args = args[1:] # FIXME: Wonder why I need this
        task = MockFetchPersonDataFromOhloh.real_task_class()
        task.debugging = True # See FetchPersonDataFromOhloh
        task.run(*args, **kwargs)

class CeleryTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    # FIXME: One day, test that after self.test_slow_loading_via_emulated_bgtask
    # getting the data does not go out to Ohloh.

    def _test_data_source_via_emulated_bgtask(self, source, data_we_expect, summaries_we_expect):
        "1. Go to the page that has paulproteus' data. "
        "2. Verify that the page doesn't yet know about ccHost. "
        "3. Prepare an object that will import data from ccHost. "
        "The object is a DataImportAttempt. The DataImportAttempt has a method "
        "that will create a background task using the celery package. The method "
        "is called do_what_it_says_on_the_tin, because it will attempt to "
        "import data. "
        "3. Run the celery task ourselves, but instead of going to Ohloh, "
        "we hand-prepare data for it."""

        # Let's run this test using a sample user, paulproteus.
        username = 'paulproteus'
        person = Person.objects.get(user__username=username)

        # Store a note in the DB that we're about to run a background task
        dia = DataImportAttempt(query=username, source=source, person=person)
        dia.save()

        gimme_json_url = reverse(mysite.profile.views.gimme_json_for_portfolio)
        
        client = self.login_with_client()

        # Ask if background task has been completed.
        # We haven't even created the background task, so 
        # the answer should be no.
        response_before_task_is_run = client.get(gimme_json_url)
        response_json = simplejson.loads(response_before_task_is_run.content)
        self.assertEqual(response_json['dias'][0]['pk'], dia.id)
        self.assertFalse(response_json['dias'][0]['fields']['completed'])
        
        # Are there any PortfolioEntries for ccHost
        # before we import data? Expected: no.
        portfolio_entries = PortfolioEntry.objects.filter(project__name='MOCK ccHost')
        self.assertEqual(portfolio_entries.count(), 0)

        dia.do_what_it_says_on_the_tin()
        # NB: The task is being run, but the communication with the external data source
        # is mocked out.

        # Now that we have synchronously run the task, it should be
        # marked as completed.
        self.assert_(DataImportAttempt.objects.get(id=dia.id).completed)

        #######################################################
        # Let's see if the browser's method of checking agrees. 
        #######################################################

        # First, request the JSON again.
        response_after = client.get(gimme_json_url)

        # Ask if background task has been completed. (Hoping for yes.)
        response_json = simplejson.loads(response_after.content)
        self.assertEquals(response_json['dias'][0]['pk'], dia.id)
        self.assert_(response_json['dias'][0]['fields']['completed'])

        # There ought now to be a PortfolioEntry for ccHost...
        portfolio_entry = PortfolioEntry.objects.get(person=person, project__name='MOCK ccHost')

        # ...and the expected number of citations.
        citations = Citation.untrashed.filter(portfolio_entry=portfolio_entry)

        self.assert_(citations.count() > 0)

        # Let's make sure we got the data we expected.
        partial_citation_dicts = list(citations.values(*data_we_expect[0].keys()))
        self.assertEqual(partial_citation_dicts, data_we_expect)

        # Let's make sure that these citations are linked with the
        # DataImportAttempt we used to import them.
        for n, citation in enumerate(citations):
            self.assertEqual(citation.data_import_attempt, dia)
            self.assertEqual(citation.summary, summaries_we_expect[n])

    @mock.patch('mysite.customs.ohloh.Ohloh.get_contribution_info_by_username', mock_gcibu)
    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_ohloh_import_via_emulated_bgtask(self):
        "Test that we can import data from Ohloh, except don't test "
        "that Ohloh actually gives data. Instead, create a mock object, a little "
        "placeholder that acts like Ohloh, and make sure we respond "
        "to it correctly."
        # {{{
        data_we_expect = [{
                'languages': mock_gcibu.return_value[0][0]['primary_language'],
                'distinct_months': mock_gcibu.return_value[0][0]['man_months'],
                'is_published': False,
                'is_deleted': False,
                }]

        summaries_we_expect = [
                "Coded for 1 month in shell script (Ohloh)",
                ]

        return self._test_data_source_via_emulated_bgtask(
                source='rs', data_we_expect=data_we_expect,
                summaries_we_expect=summaries_we_expect)
        # }}}

    @mock.patch('mysite.customs.ohloh.Ohloh.get_contribution_info_by_ohloh_username', mock_gcibou)
    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_ohloh_import_via_emulated_ohloh_username_bg_search(self):
        "Test that we can import data from Ohloh via Ohloh username, except don't test "
        "that Ohloh actually gives data. Instead, create a mock object, a little "
        "placeholder that acts like Ohloh, and make sure we respond "
        "to it correctly."
        # {{{
        data_we_expect = [{
                'languages': mock_gcibou.return_value[0][0]['primary_language'],
                'distinct_months': mock_gcibou.return_value[0][0]['man_months'],
                'is_published': False,
                'is_deleted': False,
                }]

        summaries_we_expect = [
                "Coded for 1 month in Vala (Ohloh)",
                ]

        return self._test_data_source_via_emulated_bgtask(
                source='ou', data_we_expect=data_we_expect,
                summaries_we_expect=summaries_we_expect)
        # }}}

    @mock.patch('mysite.customs.lp_grabber.get_info_for_launchpad_username', mock_giflu)
    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_launchpad_import_via_emulated_bgtask(self):
        "Test that we can import data from Ohloh, except don't test "
        "that Ohloh actually gives data. Instead, create a little "
        "placeholder that acts like Ohloh, and make sure we respond "
        "to it correctly."
        # {{{
        lp_result = mock_giflu.return_value.values()[0]
        data_we_expect = [
                {
                    'contributor_role': lp_result['involvement_types'][0],
                    'languages': ", ".join(lp_result['languages']),
                    'is_published': False,
                    'is_deleted': False,
                    },
                {
                    'contributor_role': lp_result['involvement_types'][1],
                    'languages': ", ".join(lp_result['languages']),
                    'is_published': False,
                    'is_deleted': False,
                    }
                ]

        # FIXME: Write these properly.
        summaries_we_expect = [
                'Participated in Bug Management (Launchpad)',
                'Participated in Bazaar Branches (Launchpad)',
                ]

        return self._test_data_source_via_emulated_bgtask(
                source='lp', data_we_expect=data_we_expect,
                summaries_we_expect=summaries_we_expect)
        # }}}

    # }}}

class UserListTests(TwillTests):
    # {{{
    fixtures = [ 'user-paulproteus', 'person-paulproteus',
            'user-barry', 'person-barry']

    def test_display_list_of_users_web(self):
        # {{{
        self.login_with_twill()
        url = 'http://openhatch.org/people/'
        url = make_twill_url(url)
        tc.go(url)
        tc.find(r'paulproteus')
        tc.find(r'Barry Spinoza \(barry\)')

        tc.follow('paulproteus')
        tc.url('people/paulproteus') 
        tc.find('paulproteus')
        # }}}

    # }}}

class Portfolio(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']
    # Don't include cchost-paulproteus, because we need paulproteus to have
    # zero Citations at the beginning of test_person_gets_data_iff_they_want_it

    form_url = "http://openhatch.org/people/portfolio/import/"

    @mock.patch('mysite.profile.models.DataImportAttempt.do_what_it_says_on_the_tin')
    def test_create_data_import_attempts(self, mock_do_what_it_says_on_the_tin):
        """Test profile.views.start_importing_do."""

        paulproteus = Person.objects.get(user__username='paulproteus')
        input = {
                'identifier_0': 'paulproteus',
                'identifier_1': 'asheesh@asheesh.org',
                }

        self.assertEqual(
                DataImportAttempt.objects.filter(person=paulproteus).count(),
                0,
                "Pre-condition: "
                "No tasks for paulproteus.")
        client = self.login_with_client()
        response = client.post(
                reverse(mysite.profile.views.prepare_data_import_attempts_do),\
                        input)
        # FIXME: We should also check that we call this function
        # once for each data source.
        self.assert_(mock_do_what_it_says_on_the_tin.called)

        self.assertEqual(response.content, "1",
                "Post-condition: "
                "profile.views.start_importing sent a success message via JSON.")

        for identifier in input.values():
            for (source_key, _) in DataImportAttempt.SOURCE_CHOICES:
                self.assertEqual(
                        DataImportAttempt.objects.filter(
                            person=paulproteus, source=source_key, query=identifier).count(),
                        1,
                        "Post-condition: "
                        "paulproteus has a task recorded in the DB "
                        "for source %s." % source_key)

    def _test_get_import_status(self, client, but_first=None, must_find_nothing=False):
        "Just make sure that the JSON returned by the view is "
        "appropriate considering what's in the database."
        ####################################################
        ################# LOAD DATA ########################
        ####################################################
        paulproteus = Person.objects.get(user__username='paulproteus')

        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=paulproteus)[0],
                distinct_months=1,
                languages='Python',
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True, person=paulproteus)[0]
                )
        citation.save()

        finished_dia = citation.data_import_attempt
        unfinished_dia = DataImportAttempt(source='rs', query='foo',
                completed=False, person=paulproteus)
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
            self.assert_(str(citation_in_response['pk']) in response['summaries'].keys(),
                    "Expected that this Citation's pk would have a summary.")
         
        ###########################################################
        # Are the DIAs and citations in the response
        # exactly what we expected?
        ###########################################################

        # What we expect:
        expected_list = serializers.serialize('python', [finished_dia, unfinished_dia, citation])

        # What we got:
        dias_and_citations_in_response = response['dias'] + response['citations']

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
        self._test_get_import_status(client=self.login_with_client(), must_find_nothing=False)

    def test_barry_cannot_get_paulproteuss_import_status(self):
        self._test_get_import_status(
                client=self.login_with_client_as_barry(),
                must_find_nothing=True)

    def test_paulproteus_gets_no_deleted_projects(self):
        ####################################################
        ################# LOAD DATA ########################
        ####################################################
        paulproteus = Person.objects.get(user__username='paulproteus')

        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=paulproteus)[0],
                distinct_months=1,
                languages='Python',
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True, person=paulproteus)[0]
                )
        citation.save()

        finished_dia = citation.data_import_attempt
        unfinished_dia = DataImportAttempt(source='rs', query='foo',
                completed=False, person=paulproteus)
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

    # }}}

class ImporterPublishCitation(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test_publish_citation(self):
        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=Person.objects.get(user__username='paulproteus'))[0],
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True,
                    person=Person.objects.get(user__username='paulproteus'))[0]
                )
        citation.save()

        self.assertFalse(citation.is_published)

        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client().post(reverse(view), {'pk': citation.pk})

        self.assertEqual(response.content, "1")
        self.assert_(Citation.untrashed.get(pk=citation.pk).is_published)

    def test_publish_citation_fails_when_citation_doesnt_exist(self):
        failing_pk = 0
        self.assertEqual(Citation.untrashed.filter(pk=failing_pk).count(), 0)

        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client().post(reverse(view), {'pk': failing_pk})
        self.assertEqual(response.content, "0")

    def test_publish_citation_fails_when_citation_not_given(self):
        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client().post(reverse(view))
        self.assertEqual(response.content, "0")

    def test_publish_citation_fails_when_citation_not_yours(self):
        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=Person.objects.get(user__username='paulproteus'))[0],
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True,
                    person=Person.objects.get(user__username='paulproteus'))[0]
                )
        citation.save()

        self.assertFalse(citation.is_published)
        view = mysite.profile.views.publish_citation_do
        response = self.login_with_client_as_barry().post(reverse(view))

        self.assertEqual(response.content, "0")

class ImporterDeleteCitation(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test_delete_citation(self):
        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=Person.objects.get(user__username='paulproteus'))[0],
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True,
                    person=Person.objects.get(user__username='paulproteus'))[0]
                )
        citation.save()

        self.assertFalse(citation.is_deleted)

        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client().post(reverse(view), {'citation__pk': citation.pk})

        self.assertEqual(response.content, "1")
        self.assert_(Citation.objects.get(pk=citation.pk).is_deleted)

    def test_delete_citation_fails_when_citation_doesnt_exist(self):
        failing_pk = 0
        self.assertEqual(Citation.objects.filter(pk=failing_pk).count(), 0)

        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client().post(reverse(view), {'pk': failing_pk})
        self.assertEqual(response.content, "0")

    def test_delete_citation_fails_when_citation_not_given(self):
        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client().post(reverse(view))
        self.assertEqual(response.content, "0")

    def test_delete_citation_fails_when_citation_not_yours(self):
        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=Person.objects.get(user__username='paulproteus'))[0],
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True,
                    person=Person.objects.get(user__username='paulproteus'))[0]
                )
        citation.save()

        self.assertFalse(citation.is_deleted)
        view = mysite.profile.views.delete_citation_do
        response = self.login_with_client_as_barry().post(reverse(view))

        self.assertEqual(response.content, "0")

class UserCanShowEmailAddress(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    # {{{
    def test_show_email(self):
        """This test: (a) verifies my@ema.il does not appear on paulproteus's profile page, then goes to his account settings and opts in to showing it, and then verifies it does appear."""
        # {{{
        self.login_with_twill()

        tc.go('/people/paulproteus/')
        tc.notfind('my@ema.il')

        tc.follow('settings')
        tc.follow('contact info')
        tc.fv(1, 'show_email', '1')
        tc.submit()

        tc.go('/people/paulproteus/')
        tc.find('my@ema.il')
        # }}}
    # }}}

class BugsAreRecommended(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus',
               'bugs-for-two-projects.json']

    def test_recommendations_found(self):
        # Recommendations defined like this:
        # the first N bugs matching the various "recommended searches" (N=5?)

        # It's round-robin across the searches.
        # So if we create two Python bugs and one C# bug, and we set N to 2,
        # and paulproteus ought to get hits from Python and C#, we should see
        # only one Python bug.
        recommended = list(mysite.profile.controllers.recommend_bugs(['Python', 'C#'], n=2))
        python_bugs = [ bug for bug in recommended if bug.project.language == 'Python']
        self.assertEqual(len(python_bugs), 1)
        csharp_bugs = [ bug for bug in recommended if bug.project.language == 'C#']
        self.assertEqual(len(csharp_bugs), 1)
        
    def test_recommendations_not_duplicated(self):
        """ Run two equivalent searches in parallel, and discover that they weed out duplicates."""
        recommended = list(mysite.profile.controllers.recommend_bugs(['Python', 'Python'], n=2))
        self.assertNotEqual(recommended[0], recommended[1])

class PersonInfoLinksToSearch(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    
    def test_whatever(self):
        '''
        * Have a user, say that he understands+wantstolearn+currentlylearns+canmentor something
        * Go to his user page, and click those various links
        * Find yourself on some search page that mentions the user.
        '''
        tags = {
            'understands': ['thing1'],
            'understands_not': ['thing2'],
            'seeking': ['thing3'],
            'studying': ['thing4'],
            'can_mentor': ['thing5'],
            }

        # Log in as paulproteus
        
        self.login_with_twill()

        # Update paulproteus's tags
        tc.go(reverse(mysite.profile.views.edit_info))
        for tag_type_name in tags:
            tc.fv('edit-tags', 'edit-tags-' + tag_type_name, ", ".join(tags[tag_type_name]))
        tc.submit()

        # Now, click on "thing1"
        tc.follow("thing1")

        # Now find ourself there
        tc.find('Asheesh Laroia')

class Widget(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_widget_display(self):
        widget_url = reverse(mysite.profile.views.widget_display,
                kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        response = client.get(widget_url)

    def test_widget_display_js(self):
        widget_js_url = reverse(mysite.profile.views.widget_display_js,
                kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        response = client.get(widget_js_url)

class PersonalData(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
            'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def test_all_views_that_call_get_personal_data(self):
        # Views where you can look at somebody else.
        stalking_view2args = {
                mysite.profile.views.display_person_web: {'user_to_display__username': 'paulproteus'},
                }

        # Views where you look only at yourself.
        navelgazing_view2args = {
                mysite.profile.views.projectexp_add_form: {},
                mysite.profile.views.projectexp_edit: {'project__name': 'ccHost'},
                mysite.profile.views.importer: {},
                mysite.profile.views.display_person_edit_name: {},
                }

        for view in stalking_view2args:
            self.client.login(username='barry', password='parallelism')
            kwargs = stalking_view2args[view]
            url = reverse(view, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(response.context[0]['person'].user.username, 'paulproteus')
            self.client.logout()

        for view in navelgazing_view2args:
            client = self.login_with_client()
            kwargs = navelgazing_view2args[view]
            url = reverse(view, kwargs=kwargs)
            response = client.get(url)
            self.assertEqual(response.context[0]['person'].user.username, 'paulproteus')
            client.logout()

class DeletePortfolioEntry(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test_delete_portfolio_entry(self):
        portfolio_entry = PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
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
        response = self.login_with_client().post(reverse(view),
                {'portfolio_entry__pk': portfolio_entry.pk})

        response_decoded = simplejson.loads(response.content)

        expected_output = {
            'success': True,
            'portfolio_entry__pk': portfolio_entry.pk
        }

        self.assertEqual(response_decoded, expected_output)
        self.assert_(PortfolioEntry.objects.get(pk=portfolio_entry.pk).is_deleted)

    def test_delete_portfolio_entry_fails_when_portfolio_entry_doesnt_exist(self):
        failing_pk = 0
        self.assertEqual(PortfolioEntry.objects.filter(pk=failing_pk).count(), 0)

        view = mysite.profile.views.delete_portfolio_entry_do
        response = self.login_with_client().post(reverse(view), {'portfolio_entry__pk': failing_pk})
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
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=Person.objects.get(user__username='paulproteus'))[0],
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True,
                    person=Person.objects.get(user__username='paulproteus'))[0]
                )
        citation.save()

        portfolio_entry_not_mine = citation.portfolio_entry;

        self.assertFalse(portfolio_entry_not_mine.is_deleted)
        view = mysite.profile.views.delete_portfolio_entry_do
        response = self.login_with_client_as_barry().post(reverse(view))

        self.assertEqual(simplejson.loads(response.content), 
                         {'success': False})

        # Still there betch.
        self.assertFalse(portfolio_entry_not_mine.is_deleted)

class AddCitationManually(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test_add_citation_manually(self):
        portfolio_entry, _ = PortfolioEntry.objects.get_or_create(
            project=Project.objects.get_or_create(name='project name')[0],
            person=Person.objects.get(user__username='paulproteus'))

        input_data = {
                'portfolio_entry': portfolio_entry.pk,
                'form_container_element_id': 'form_container_%d' % 0,
                'url': 'http://google.ca/' # Needs this trailing slash to work.
                }

        # Send this data to the appropriate view.
        url = reverse(mysite.profile.views.add_citation_manually_do)
        response = self.login_with_client().post(url, input_data)

        # Check that a citation was created.
        c = Citation.untrashed.get(url=input_data['url'])
        self.assertEqual(c.portfolio_entry, portfolio_entry,
                "The portfolio entry for the new citation is the exactly "
                "the one whose id we POST'd to "
                "profile.views.add_citation_manually.")

        self.assert_(c.is_published, "Manually added citations are published by default.")

    def test_add_citation_manually_with_bad_portfolio_entry(self):
        not_your_portfolio_entry, _ = PortfolioEntry.objects.get_or_create(
            project=Project.objects.get_or_create(name='project name')[0],
            person=Person.objects.get(user__username='barry'))

        input_data = {
                'portfolio_entry': not_your_portfolio_entry.pk,
                'form_container_element_id': 'form_container_%d' % 0,
                'url': 'http://google.ca/' # Needs this trailing slash to work.
                }

        # Send this data to the appropriate view.
        url = reverse(mysite.profile.views.add_citation_manually_do)
        response = self.login_with_client().post(url, input_data)

        # Check that no citation was created.
        self.assertEqual(Citation.untrashed.filter(url=input_data['url']).count(), 0,
                "Expected no citation to be created when you try "
                "to add one for someone else.")
        
        # Check that an error is reported in the response.
        self.assert_(len(simplejson.loads(response.content)['error_msgs']) == 1)

class ReplaceIconWithDefault(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test_view(self):
        portfolio_entry = PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=Person.objects.get(user__username='paulproteus'))[0]
        url = reverse(mysite.profile.views.replace_icon_with_default)
        data = {
                'portfolio_entry__pk': portfolio_entry.pk
                };

        image_data = open(mysite.account.tests.photo('static/sample-photo.png')).read()
        portfolio_entry.project.icon_raw.save('', ContentFile(image_data))
        self.assert_(portfolio_entry.project.icon_raw,
                "Expected precondition: project has a nongeneric icon.")

        response = self.login_with_client().post(url, data)

        # Check output
        response_obj = simplejson.loads(response.content)
        """response obj will look something like this:
        {
            'success': true,
                'portfolio_entry__pk': 0,
            }
                """
        self.assert_(response_obj['success'])
        self.assertEqual(response_obj['portfolio_entry__pk'], portfolio_entry.pk)

        # Check side-effect
        portfolio_entry = PortfolioEntry.objects.get(pk=portfolio_entry.pk)
        self.assertFalse(portfolio_entry.project.icon_raw,
                "Expected postcondition: portfolio entry's icon evaluates to False "
                "because it is generic.")

class SavePortfolioEntry(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test_save_portfolio_entry(self):
        url = reverse(mysite.profile.views.save_portfolio_entry_do)

        # setup
        portfolio_entry = PortfolioEntry.objects.get_or_create(
                    project=Project.objects.get_or_create(name='project name')[0],
                    person=Person.objects.get(user__username='paulproteus'))[0]
        citation = Citation(
                portfolio_entry=portfolio_entry,
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True,
                    person=Person.objects.get(user__username='paulproteus'))[0]
                )
        citation.is_published = False
        citation.save()

        input = {
            'portfolio_entry__pk': portfolio_entry.pk,
            'pf_entry_element_id': 'blargle', # this can be whatever
            'project_description': "project description",
            'experience_description': "experience description",
        }

        expected_output = {
            'success': True,
            'pf_entry_element_id': 'blargle', 
            'portfolio_entry__pk': portfolio_entry.pk
        }

        # call view and check output
        self.assertEqual(
                simplejson.loads(self.login_with_client().post(url, input).content),
                expected_output)

        # postcondition
        portfolio_entry = PortfolioEntry.objects.get(pk=portfolio_entry.pk)
        self.assertEqual(portfolio_entry.project_description,
                input['project_description'])
        self.assertEqual(portfolio_entry.experience_description,
                input['experience_description'])
        self.assert_(portfolio_entry.is_published, "pf entry is published.")

        citations = Citation.untrashed.filter(portfolio_entry=portfolio_entry)
        for c in citations:
            self.assert_(c.is_published)

class GimmeJsonTellsAboutImport(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def gimme_json(self):
        url = reverse(mysite.profile.views.gimme_json_for_portfolio)
        response = self.login_with_client().get(url)
        return simplejson.loads(response.content)

    def get_paulproteus(self):
        return mysite.profile.models.Person.objects.get(user__username='paulproteus')

    def get_barry(self):
        return mysite.profile.models.Person.objects.get(user__username='barry')

    def get_n_min_ago(self, n):
        return datetime.datetime.utcnow() - datetime.timedelta(minutes=n)

    def test_import_running_false(self):
        "When there are no dias from the past five minutes, import.running = False"
        # Create a DIA for paulproteus that is from ten minutes ago (but curiously is still in progress)
        my_dia_but_not_recent = DataImportAttempt(date_created=self.get_n_min_ago(10),
                query="bananas", person=self.get_paulproteus())
        my_dia_but_not_recent.save()

        # Create a DIA for Barry that is in progress, but ought not be
        # included in the calculation by gimme_json_for_portfolio
        not_my_dia = DataImportAttempt(date_created=self.get_n_min_ago(1),
                                query="banans", person=self.get_barry())
        not_my_dia.save()
        
        # Verify that the JSON reports import running is False
        self.assertFalse(self.gimme_json()['import']['running'])
                                                      
    def test_for_running_import(self):
        "When there are dias from the past five minutes, import.running = True "
        "and progress percentage is accurate"
        # Create a DIA for paulproteus that is from one minutes ago (but curiously is still in progress)
        my_incomplete_recent_dia = DataImportAttempt(date_created=self.get_n_min_ago(1),
                query="bananas", person=self.get_paulproteus(), completed=False)
        my_incomplete_recent_dia.save()

        my_completed_recent_dia = DataImportAttempt(date_created=self.get_n_min_ago(1),
                query="bananas", person=self.get_paulproteus(), completed=True)
        my_completed_recent_dia.save()

        # Create a DIA that is in progress, but ought not be
        # included in the calculation by gimme_json_for_portfolio
        # because it doesn't belong to the logged-in user
        not_my_dia = DataImportAttempt(date_created=self.get_n_min_ago(1), person=self.get_barry(),
                query="bananas")
        not_my_dia.save()
        
        self.assert_(self.gimme_json()['import']['running'],
                "Expected that the JSON reports that an import is running")
        self.assertEqual(self.gimme_json()['import']['progress_percentage'], 50,
                "Expected that the JSON reports that the import is at 50% progress")

        # Now let's make them all completed
        my_incomplete_recent_dia.completed = True
        my_incomplete_recent_dia.save()

        self.assertFalse(self.gimme_json()['import']['running'],
                "After all DIAs are completed, expected that the JSON reports that no import is running.")

class PortfolioEntryAdd(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_portfolio_entry_add(self):
        # preconditions
        self.assertEqual(
                Project.objects.filter(name='new project name').count(),
                0, "expected precondition: there's no project named 'new project name'")
        self.assertEqual(
                PortfolioEntry.objects.filter(project__name='new project name').count(),
                0, "expected precondition: there's no portfolio entry for a project "
                "named 'new project name'")

        # Here is what the JavaScript seems to POST.
        post_data = {
                'portfolio_entry__pk': 'undefined',
                'project_name': 'new project name',
                'project_description': 'new project description',
                'experience_description': 'new experience description',
                'pf_entry_element_id': 'element_18', 
                }
        url = reverse(mysite.profile.views.save_portfolio_entry_do)
        response = self.login_with_client().post(url, post_data)
        # Check side-effects

        self.assertEqual(
                Project.objects.filter(name='new project name').count(),
                1, "expected: after POSTing to view, there's a project named 'new project name'")
        self.assertEqual(
                PortfolioEntry.objects.filter(person__user__username='paulproteus',
                    project__name='new project name').count(),
                1, "expected: after POSTing to view, there's a portfolio entry for paulproteus"
                "for a project named 'new project name'")

        new_pk = PortfolioEntry.objects.get(person__user__username='paulproteus',
                project__name='new project name').pk

        # Check response

        expected_response_obj = {
            'success': True,
            'pf_entry_element_id': 'element_18',
            'portfolio_entry__pk': new_pk, 
        }
        self.assertEqual(simplejson.loads(response.content), expected_response_obj)

class OtherContributors(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test_list_other_contributors(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        barry = Person.objects.get(user__username='barry')
        project = Project(name='project', icon_raw="static/no-project-icon-w=40.png")
        project.save()
        PortfolioEntry(project=project, person=paulproteus, is_published=True).save()
        PortfolioEntry(project=project, person=barry, is_published=True).save()
        self.assertEqual(
                project.get_n_other_contributors_than(5, paulproteus),
                [barry]
                )
        self.assertEqual(
                project.get_n_other_contributors_than(5, barry),
                [paulproteus]
                )

class UserGetsHisQueuedMessages(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    
    def gimme_json(self):
        url = reverse(mysite.profile.views.gimme_json_for_portfolio)
        response = self.login_with_client().get(url)
        return simplejson.loads(response.content)

    def test_user_gets_his_queued_messages(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        # Verify the first time, the gimme_json has no messages
        self.assertEqual(self.gimme_json()['messages'], [])

        # Queue a message for paulproteus
        paulproteus.user.message_set.create(message="MSG'd!")

        # Verify that the gimme_json now has that message
        self.assertEqual(self.gimme_json()['messages'], ["MSG'd!"])

class IgnoreNewDuplicateCitations(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_old_citations_supersede_their_new_duplicates(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        project1 = Project.create_dummy(name='1')
        project2 = Project.create_dummy(name='2') 
        repo_search = DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True, person=paulproteus)[0]
        citation = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=project1,
                    is_published=True,
                    person=paulproteus)[0],
                distinct_months=1,
                languages='Python',
                data_import_attempt=repo_search
                )
        citation.save_and_check_for_duplicates()

        citation_of_different_project = Citation(
                portfolio_entry=PortfolioEntry.objects.get_or_create(
                    project=project2,
                    is_published=True,
                    person=paulproteus)[0],
                distinct_months=1,
                languages='Python',
                data_import_attempt=DataImportAttempt.objects.get_or_create(
                    source='rs', query='paulproteus', completed=True, person=paulproteus)[0]
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
                    source='ou', query='paulproteus', completed=True, person=paulproteus)[0]
        # As is realistic, this citation comes from an
        # Ohloh username search with the same results.
        citation2 = Citation(
                portfolio_entry=citation.portfolio_entry,
                distinct_months=citation.distinct_months,
                languages=citation.languages,
                data_import_attempt=username_search
                )
        citation2.save_and_check_for_duplicates()

        # The second citation is ignored.
        self.assert_(citation2.ignored_due_to_duplicate)

        # The 'untrashed' manager picks up only the first two distinct citations,
        # not the third (duplicate) citation
        self.assertEqual(
                list(Citation.untrashed.all().order_by('pk')),
                [citation, citation_of_different_project])

class PersonGetTagsForRecommendations(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_get_tags(self):
        pp = Person.objects.get(user__username='paulproteus')

        understands_not = TagType(name='understands_not')
        understands_not.save()
        understands = TagType(name='understands')
        understands.save()

        tag_i_understand = Tag(tag_type=understands, text='something I understand')
        tag_i_understand.save()
        tag_i_dont = Tag(tag_type=understands_not, text='something I dont get')
        tag_i_dont.save()
        link_one = Link_Person_Tag(person=pp, tag=tag_i_understand)
        link_one.save()
        link_two = Link_Person_Tag(person=pp, tag=tag_i_dont)
        link_two.save()

        # This is the functionality we're testing
        self.assertEqual([tag_i_understand], pp.get_tags_for_recommendations())

# vim: set ai et ts=4 sw=4 nu:
