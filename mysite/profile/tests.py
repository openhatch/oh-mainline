from mysite.base.tests import make_twill_url, better_make_twill_url, TwillTests
from mysite.base.helpers import ObjectFromDict
from mysite.base.models import Timestamp
import mysite.account.tests
from mysite.search.models import Project, WannaHelperNote
from mysite.profile.models import Person, Tag, TagType, Link_Person_Tag, DataImportAttempt, PortfolioEntry, Citation, Forwarder
import mysite.project.views
import mysite.profile.views
import mysite.profile.models
import mysite.profile.controllers
from mysite.profile.management.commands import send_weekly_emails
from mysite.profile import views
from mysite.customs import ohloh
from mysite.customs.models import WebResponse

import simplejson
import BeautifulSoup
import datetime
import tasks 
import mock
import UserList
from twill import commands as tc
import quopri

from django.core import mail
from django.conf import settings
import django.test
from django.core import serializers
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

def do_nothing(*args, **kwargs):
    return ''
    
class StarlingTests(TwillTests):
	def test_page(self):
		url = 'http://openhatch.org/starlings'
		place = make_twill_url(url)
		tc.go(place)

class ProfileTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus',
            'cchost-data-imported-from-ohloh']

    def testSlash(self):
        self.client.get('/people/')

    def test__portfolio_updates_when_citation_added_to_db(self):
       # {{{
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

    # }}}

class DebTagsTests(TwillTests):
    # {{{

    def testAddOneDebtag(self):
        views.add_one_debtag_to_project('alpine', 'implemented-in::c')
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
        u'permalink':
            u'https://www.ohloh.net/p/cchost/contributors/65837553699824',
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
        u'permalink':
            u'https://www.ohloh.net/p/cchost/contributors/65837553699824',
        'project': u'MOCK ccHost',
        'project_homepage_url':
            u'http://wiki.creativecommons.org/CcHost',
        'primary_language': u'Vala'}],
        None #WebResponse
        )

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

class BaseCeleryTest(TwillTests):
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

# Mockup of stump's contribution list as given by ohloh, stripped down and slightly tweaked for the purposes of testing.
stumps_ohloh_results = mock.Mock()
stumps_ohloh_results.return_value = ([
  {u'contributor_name': u'stump', u'analysis_id': u'1145788', u'man_months': u'11', u'primary_language_nice_name': u'C',u'contributor_id': u'2008814186590608'},
  {u'contributor_name': u'John Stumpo', u'analysis_id': u'1031175', u'man_months': u'12', u'primary_language_nice_name': u'Python', u'contributor_id': u'110891760646528'}
], WebResponse())
stumps_project_lookup = mock.Mock()
stumps_project_lookup.return_value = {u'name': u'WinKexec', u'homepage_url': u'https://www.jstump.com/projects/kexec/'}

class OhlohTests(TwillTests):

    @mock.patch('mysite.customs.ohloh.ohloh_url2data', stumps_ohloh_results)
    @mock.patch('mysite.customs.ohloh.Ohloh.analysis2projectdata', stumps_project_lookup)
    def test_ohloh_doesnt_match_just_substring(self):
        expected = [{'man_months': 11,
          'permalink': u'https://www.ohloh.net/p/winkexec/contributors/2008814186590608',
          'primary_language': u'C',
          'project': u'WinKexec',
          'project_homepage_url': u'https://www.jstump.com/projects/kexec/'}]

        received = ohloh.get_ohloh().get_contribution_info_by_username('stump')[0]
        self.assertEqual(received, expected)

class CeleryTests(BaseCeleryTest):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    # FIXME: One day, test that after self.test_slow_loading_via_emulated_bgtask
    # getting the data does not go out to Ohloh.

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
                'url': mock_gcibu.return_value[0][0]['permalink'],
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
                'url': mock_gcibou.return_value[0][0]['permalink'],
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

    # }}}

class UserListTests(TwillTests):
    # {{{
    fixtures = [ 'user-paulproteus', 'person-paulproteus',
            'user-barry', 'person-barry']

    def test_display_list_of_users_web(self):
        # {{{
        self.login_with_twill()
        url = 'http://openhatch.org/%2Bpeople/list/'
        url = make_twill_url(url)
        tc.go(url)
        tc.find(r'paulproteus')
        tc.find(r'Barry Spinoza')

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

        # finished dia
        citation.data_import_attempt
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
        tc.follow('Email')
        tc.fv("a_settings_tab_form", 'show_email', '1')
        tc.submit()

        tc.go('/people/paulproteus/')
        tc.find('my@ema.il')
        # }}}
    # }}}


# Create a mock Launchpad get_info_for_launchpad_username
mock_launchpad_debian_response = mock.Mock()
mock_launchpad_debian_response.return_value = {
        'Debian': {
            'url': 'http://launchpad.net/debian', # ok this url doesn't really exist
            'involvement_types': ['Bug Management', 'Bazaar Branches'],
            'citation_url': 'https://launchpad.net/~paulproteus',
            'languages': '',
            }
        }

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
        recommender = mysite.profile.controllers.RecommendBugs(['Python', 'C#'], n=2)
        recommended = list(recommender.recommend())
        python_bugs = [ bug for bug in recommended if bug.project.language == 'Python']
        self.assertEqual(len(python_bugs), 1)
        csharp_bugs = [ bug for bug in recommended if bug.project.language == 'C#']
        self.assertEqual(len(csharp_bugs), 1)
        
    def test_recommendations_not_duplicated(self):
        """ Run two equivalent searches in parallel, and discover that they weed out duplicates."""
        recommender = mysite.profile.controllers.RecommendBugs(['Python', 'Python'], n=2)
        recommended = list(recommender.recommend())
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
            'can_pitch_in': ['thing3'],
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

        # The following assertion will succeed if we remove Haystack.

        # Now find ourself there
        tc.find('Asheesh Laroia')

class Widget(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_widget_display(self):
        widget_url = reverse(mysite.profile.views.widget_display,
                kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        client.get(widget_url)

    def test_widget_display_js(self):
        widget_js_url = reverse(mysite.profile.views.widget_display_js,
                kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        client.get(widget_js_url)

class PersonalData(TwillTests):
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
        proj = Project.create_dummy(name='project name')
        portfolio_entry, _ = PortfolioEntry.objects.get_or_create(
            project=proj,
            person=Person.objects.get(user__username='paulproteus'))

        input_data = {
                'portfolio_entry': portfolio_entry.pk,
                'form_container_element_id': 'form_container_%d' % 0,
                'url': 'http://google.com/' # Needs this trailing slash to work.
                }

        # Send this data to the appropriate view.
        url = reverse(mysite.profile.views.add_citation_manually_do)
        self.login_with_client().post(url, input_data)

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

    # mock out the django email function
    @mock.patch("mysite.project.tasks.send_email_to_all_because_project_icon_was_marked_as_wrong.delay")
    def test_view(self, send_mail_mock):
        project = Project.objects.get_or_create(name='project name')[0]
        portfolio_entry = PortfolioEntry.objects.get_or_create(project=project,
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

        # Make sure that all@ was emailed
        # first check that the task itself was run with the args that we expect
        self.assert_(send_mail_mock.called)

        expected_call_args = {
            'project__pk': project.pk,
            'project__name': project.name,
            'project_icon_url': "icon_url",
        }
        # we have to take [1] here because call_args puts an empty tuple at 0. this is the empty list of non-kw-args
        self.assertEqual(send_mail_mock.call_args[1], expected_call_args)

        # TODO: next, make sure that the task itself actually sends an email
        mysite.project.tasks.send_email_to_all_because_project_icon_was_marked_as_wrong(**expected_call_args)
        outbox = django.core.mail.outbox
        self.assertEqual(len(outbox), 1)
        sent_msg = outbox[0]
        subject = '[OH]- ' + project.name + ' icon was marked as incorrect'
        self.assertEqual(sent_msg.subject, subject)

        # Check that we correctly created our WrongIcon object
        # note that 'project' still contains the old project data (before the icon was marked as wrong)
        wrong_icon = mysite.search.models.WrongIcon.objects.get(project=project)
        self.assertEqual(wrong_icon.icon_url, project.icon_url)
        self.assertEqual(wrong_icon.icon_raw, project.icon_raw)

        # Check side-effect
        portfolio_entry = PortfolioEntry.objects.get(pk=portfolio_entry.pk)
        self.assertFalse(portfolio_entry.project.icon_raw,
            "Expected postcondition: portfolio entry's icon evaluates to False "
            "because it is generic.")

class SavePortfolioEntry(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.user = "paulproteus"
        self.portfolio_entry = PortfolioEntry.objects.get_or_create(
            project=Project.objects.get_or_create(name='project name')[0],
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
            'pf_entry_element_id': 'blargle', # this can be whatever
            'project_description': "\n".join(self.project_description),
            'experience_description': "\n".join(self.experience_description)
        }

        POST_handler = reverse(mysite.profile.views.save_portfolio_entry_do)
        self.post_result = self.login_with_client().post(POST_handler, self.POST_data)
        self.contribution_page = self.login_with_client().get(
            make_twill_url("http://openhatch.org/people/%s/" % (self.user,)))

    def test_save_portfolio_entry(self):
        expected_output = {
            'success': True,
            'pf_entry_element_id': 'blargle', 
            'portfolio_entry__pk': self.portfolio_entry.pk
        }

        # check output
        self.assertEqual(simplejson.loads(self.post_result.content), expected_output)

        # postcondition
        portfolio_entry = PortfolioEntry.objects.get(pk=self.portfolio_entry.pk)
        self.assertEqual(portfolio_entry.project_description,
                         self.POST_data['project_description'])
        self.assertEqual(portfolio_entry.experience_description,
                         self.POST_data['experience_description'])
        self.assert_(portfolio_entry.is_published, "pf entry is published.")

        citations = Citation.untrashed.filter(portfolio_entry=portfolio_entry)
        for c in citations:
            self.assert_(c.is_published)

    def test_multiparagraph_contribution_description(self):
        """
        If a multi-paragraph project contribution description is submitted,
        display it as a multi-paragraph description.
        """
        self.assertContains(
            self.contribution_page, "<br />".join(self.experience_description))

    def test_multiparagraph_project_description(self):
        """
        If a multi-paragraph project description is submitted, display it as a
        multi-paragraph description.
        """
        self.assertContains(
            self.contribution_page, "<br />".join(self.project_description))

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

class MapTagsRemoveDuplicates(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        pp = Person.objects.get(user__username='paulproteus')

        understands_not = TagType(name='understands_not')
        understands_not.save()
        understands = TagType(name='understands')
        understands.save()
        can_pitch_in = TagType(name='can_pitch_in')
        can_pitch_in.save()

        tag_i_understand = Tag(tag_type=understands, text='something I understand')
        tag_i_understand.save()
        tag_i_dont = Tag(tag_type=understands_not, text='something I dont get')
        tag_i_dont.save()
        tag_can_pitch_in = Tag(tag_type=can_pitch_in, text='something I UNDERSTAND')
        tag_can_pitch_in.save()
        link_one = Link_Person_Tag(person=pp, tag=tag_i_understand)
        link_one.save()
        link_two = Link_Person_Tag(person=pp, tag=tag_i_dont)
        link_two.save()
        link_three = Link_Person_Tag(person=pp, tag=tag_can_pitch_in)
        link_three.save()

        self.assertEqual(map(lambda x: x.lower(), pp.get_tag_texts_for_map()),
                         map(lambda x: x.lower(), ['something I understand']))

class ProjectGetMentors(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

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
        link = Link_Person_Tag(person=Person.objects.get(user__username='paulproteus'),
                               tag=willing_to_mentor_banshee)
        link.save()


class SuggestLocation(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test(self):
        data = {}
        data['geoip_has_suggestion'], data['geoip_guess'] = mysite.profile.controllers.get_geoip_guess_for_ip("128.151.2.1")
        self.assertEqual(data['geoip_has_suggestion'], True)
        self.assertEqual(data['geoip_guess'], "Rochester, NY, United States")

    def test_iceland(self):
        """We wrote this test because MaxMind gives us back a city in Iceland. That city
        has a name not in ASCII. MaxMind's database seems to store those values in Latin-1,
        so we verify here that we properly decode that to pure beautiful Python Unicode."""
        data = {}
        data['geoip_has_suggestion'], data['geoip_guess'] = mysite.profile.controllers.get_geoip_guess_for_ip("89.160.147.41")
        self.assertEqual(data['geoip_has_suggestion'], True)
        self.assertEqual(type(data['geoip_guess']), unicode)

        # This test originally used this line of code:
        # correct_decoding = u'Reykjav\xedk, 10, Iceland'

        # But now we use this line of code, which doesn't include the rather
        # confusing numerals for region names:
        correct_decoding = u'Reykjav\xedk, Iceland'

        self.assertEqual(data['geoip_guess'], correct_decoding)
    
class EditLocation(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus's profile
        * checks that he is not in Timbuktu
        * clicks "edit or hide"
        * sets the location to Timbuktu
        * saves
        * checks his location is Timbuktu'''
        self.login_with_twill()
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        # not in Timbuktu!
        tc.notfind('Timbuktu')

        # Now go edit my "contact info"
        tc.go(make_twill_url('http://openhatch.org/account/settings/location/'))
        # set the location in ze form
        tc.fv("a_settings_tab_form", 'location_display_name', 'Timbuktu')
        tc.submit()
        # Timbuktu!
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        tc.find('Timbuktu')

class EditBio(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus's profile
        * checks that they don't already have a bio that says "lookatme!"
        * clicks edit on the Info area
        * enters a string as bio
        * checks that his bio now contains string
        '''
        self.login_with_twill()
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        #not so vain.. yet
        tc.notfind('lookatme!')
        tc.go(make_twill_url('http://openhatch.org/profile/views/edit_info'))
        #make sure our bio is not already on the form
        tc.notfind('lookatme!')
        # set the bio in ze form
        tc.fv("edit-tags", 'edit-tags-bio', 'lookatme!')
        tc.submit()
        #find the string we just submitted as our bio
        tc.find('lookatme!')
        self.assertEqual(Person.get_by_username('paulproteus').bio, "lookatme!")
        #now we should see our bio in the edit form
        tc.go(make_twill_url('http://openhatch.org/profile/views/edit_info'))
        tc.find('lookatme!')

class EditHomepage(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus's profile
        * checks that there is no link to asheesh.org
        * clicks edit on the Info area
        * enters a link as Info
        * checks that his bio now contains "asheesh.org"
        '''
        self.login_with_twill()
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        #not so vain.. yet
        tc.notfind('asheesh.org')
        tc.go(make_twill_url('http://openhatch.org/profile/views/edit_info'))
        #make sure our bio is not already on the form
        tc.notfind('asheesh.org')
        # set the bio in ze form
        tc.fv("edit-tags", 'edit-tags-homepage_url', 'http://www.asheesh.org/')
        tc.submit()
        #find the string we just submitted as our bio
        tc.find('asheesh.org')
        self.assertEqual(Person.get_by_username('paulproteus').homepage_url,
        "http://www.asheesh.org/")
        #now we should see our bio in the edit form
        tc.go(make_twill_url('http://openhatch.org/profile/views/edit_info'))
        tc.find('asheesh.org')
        #try an invalid url
        tc.fv('edit-tags', 'edit-tags-homepage_url', 'htttp://www.asheesh.org/')
        tc.submit()
        # check that the form came back with an error
        tc.find('has_errors')
        # ensure it didn't get saved
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        tc.notfind('htttp')


class EditContactBlurbForwarderification(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def test(self):
        '''
        a controller called put_forwarder_in_contact_blurb_if_they_want() takes a string which is what someone inputs as their contact info blurb
        it also takes said person's username or person object or something
        we're testing this:
            the controller returns a string which is the same as the one that it received, except $fwd is replaced with the output of generate_forwarder
            the Forwarder db table contains a row for our new forwarder 
                (which we created with the generate_forwarder controller)
        '''
        # grab asheesh by the horns
        sheesh = mysite.profile.models.Person.get_by_username('paulproteus')
        # make them a forwarder
        mysite.base.controllers.generate_forwarder(sheesh.user)
        # we have a string that contains the substr $fwd
        mystr = "email me here: $fwd.  it'll be great"
        user_to_forward_to = User.objects.get(username='paulproteus')
        # we run this string through a controller called forwarderify
        mystr_forwarderified = (mysite.base.controllers.
                put_forwarder_in_contact_blurb_if_they_want(mystr, user_to_forward_to))
        our_forwarder = mysite.profile.models.Forwarder.objects.get(user=user_to_forward_to)
        output = "email me here: %s@%s .  it'll be great" % (
                our_forwarder.address, settings.FORWARDER_DOMAIN)
        # ^note that we throw in a zero-width string after the forwarder to make
        # sure it that the urlizetrunc filter, in the template, linkifies it correctly.

        # make sure our forwarder that we just made hasn't expired
        self.assert_(our_forwarder.expires_on > datetime.datetime.utcnow())
        # we test that the result contains, as a substr, the output of a call to generate_forwarder
        self.assertEqual(mystr_forwarderified, output);


class EditContactBlurb(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        '''
        * Goes to paulproteus' profile
        * checks that it doesn't say "bananas"
        * clicks edit in the info area
        * checks that the input field for "how to contact me" doesn't say bananas
        * enters bananas under the "how to contact me" section
        * submits
        * checks that his profile now says "bananas"
        * clicks edit in the info area again
        * checks that the input field for "how to contact me" now says bananas
        * removes email address from user
        * enters contact blurb containing $fwd
        * makes sure that the user gets an error message
        '''
        self.login_with_twill()
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        # make sure our contact info isn't already on the profile page
        tc.notfind('bananas')
        tc.go(make_twill_url('http://openhatch.org/profile/views/edit_info'))
        #make sure our contact info is not already on the form
        tc.notfind('bananas')
        # set the contact info in ze form
        tc.fv("edit-tags", 'edit-tags-contact_blurb', 'bananas')
        tc.submit()
        #find the string we just submitted as our contact info
        tc.find('bananas')
        asheesh = Person.get_by_username('paulproteus')
        self.assertEqual(asheesh.contact_blurb, "bananas")
        #now we should see our contact info in the edit form
        tc.go(make_twill_url('http://openhatch.org/profile/views/edit_info'))
        tc.find('bananas')
        #delete asheesh's email
        asheesh_user = asheesh.user
        asheesh_user.email = ''
        asheesh_user.save()
        contact_blurb = 'email me here: $fwd'
        contact_blurb_escaped = 'email me here: \$fwd'
        homepage_url = 'http://mysite.com/'
        tc.fv("edit-tags", 'edit-tags-contact_blurb', contact_blurb)
        # also enter a homepage so that we can make sure that this gets saved despite our error with the forwarder stuff
        tc.fv("edit-tags", 'edit-tags-homepage_url', homepage_url)
        tc.submit()
        # make sure that they got an error message
        tc.find('contact_blurb_error')
        # make sure that the form remembered the contact blurb that they posted
        tc.find(contact_blurb_escaped)
        # make sure that their homepage was saved to the database
        asheesh = Person.get_by_username('paulproteus')
        self.assertEqual(asheesh.homepage_url, homepage_url)

class PeopleSearchProperlyIdentifiesQueriesThatFindProjects(TwillTests):
    def test_one_valid_project(self):
        # make a project called Banana
        # query for that, but spelled bANANA
        # look in the template and see that projects_that_match_q_exactly == ['Banana']
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
        # look in the template and see that projects_that_match_q_exactly == ['Banana']
        mysite.search.models.Project.create_dummy(
            name='Banana',
            cached_contributor_count=0)
        url = reverse(mysite.profile.views.people)
        response = self.client.get(url, {'q': 'bANANA'})
        self.assertEqual(response.context[0]['projects_that_match_q_exactly'],
                         [])

class PeopleSearch(TwillTests):
    def test_project_queries_are_distinct_from_tag_queries(self):
        # input "project:Exaile" into the search controller, ensure that it outputs
        # {'q': 'Exaile', 'query_type': 'project'}
        data = mysite.profile.controllers.parse_string_query("project:a_project_name")
        self.assertEqual(data['q'], 'a_project_name')
        self.assertEqual(data['query_type'], 'project')

        data = mysite.profile.controllers.parse_string_query("a_tag_name_or_whatever")
        self.assertEqual(data['q'], 'a_tag_name_or_whatever')
        self.assertEqual(data['query_type'], 'all_tags')

    def test_tokenizer_parses_quotation_marks_correctly_but_if_they_are_missing_greedily_assumes_they_were_there(self):
        data = mysite.profile.controllers.parse_string_query('project:"Debian GNU/Linux"')
        self.assertEqual(data['q'], 'Debian GNU/Linux')
        self.assertEqual(data['query_type'], 'project')

        data = mysite.profile.controllers.parse_string_query('project:Debian GNU/Linux')
        self.assertEqual(data['q'], 'Debian GNU/Linux')
        self.assertEqual(data['query_type'], 'project')

    def test_tokenizer_picks_up_on_tag_type_queries(self):
        for tag_type_short_name in mysite.profile.models.TagType.short_name2long_name:
            query = "%s:yourmom" % tag_type_short_name
            data = mysite.profile.controllers.parse_string_query(query)
            self.assertEqual(data['q'], 'yourmom')
            self.assertEqual(data['query_type'], tag_type_short_name)

    def test_tokenizer_ignores_most_colon_things(self):
        query = "barbie://queue"
        data = mysite.profile.controllers.parse_string_query(query)
        self.assertEqual(data['q'], query)
        self.assertEqual(data['query_type'], 'all_tags')


class PostFixGeneratorList(TwillTests):
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
        mysite.base.controllers.generate_forwarder(barry)
        mysite.base.controllers.generate_forwarder(asheesh)
        # run the function in Forwarder which creates/updates the list of user/forwarder pairs for postfix to generate forwarders for
        what_we_get = mysite.profile.models.Forwarder.generate_list_of_lines_for_postfix_table()

        what_we_want = [mysite.profile.models.Forwarder.objects.filter(user__username='paulproteus')[0].generate_table_line()]
        # make sure that the list of strings that we get back contains an item for the user with an email address and no item for the user without
        self.assertEqual(what_we_get, what_we_want)
        
        
class EmailForwarderGarbageCollection(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    # create a bunch of forwarders
        # all possibilitied given the options: "expired," "should no longer be displayed"
            # except if it's expired we it definitely should no longer be displayed
    # run garbage collection
    # make sure that whatever should have happened has happened

    def test(self):
        # args:
            # valid = True iff we want a forwarder whose expires_on is in the future
            # new_enough_for_dispay = True iff we want a forwarder whose stops_being_listed_on date is in the future
        def create_forwarder(address, valid, new_enough_for_display):
            expires_on_future_number = valid and 1 or -1
            stops_being_listed_on_future_number = new_enough_for_display and 1 or -1
            expires_on = datetime.datetime.utcnow() + expires_on_future_number*datetime.timedelta(minutes=10)
            stops_being_listed_on = datetime.datetime.utcnow() + stops_being_listed_on_future_number*datetime.timedelta(minutes=10)
            user = User.objects.get(username="paulproteus")
            new_mapping = mysite.profile.models.Forwarder(address=address,
                    expires_on=expires_on, user=user, stops_being_listed_on=stops_being_listed_on)
            new_mapping.save()
            return new_mapping
        # asheesh wants a forwarder in his profile.  oh yes he does.
        sheesh = mysite.profile.models.Person.get_by_username('paulproteus')
        sheesh.contact_blurb = u'$fwd'
        sheesh.save()
        valid_new = create_forwarder('orange@domain.com', 1, 1)
        valid_old = create_forwarder('red@domain.com', 1, 0)
        invalid = create_forwarder('purple@domain.com', 0, 0)
        # with any luck, the below will call this: mysite.profile.models.Forwarder.garbage_collect()
        mysite.profile.tasks.GarbageCollectForwarders.apply()
# valid_new should still be in the database
# there should be no other forwarders for the address that valid_new has
        self.assertEqual(1, mysite.profile.models.Forwarder.objects.filter(pk=valid_new.pk).count())
        self.assertEqual(1, mysite.profile.models.Forwarder.objects.filter(address=valid_new.address).count())
# valid_old should still be in the database
        self.assertEqual(1, mysite.profile.models.Forwarder.objects.filter(pk=valid_old.pk).count())
# invalid should not be in the database
        self.assertEqual(0, mysite.profile.models.Forwarder.objects.filter(pk=invalid.pk).count())
# there should be 3 forwarders in total: we gained one and we lost one
        forwarders = mysite.profile.models.Forwarder.objects.all()
        self.assertEqual(3, forwarders.count())

class EmailForwarderResolver(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    '''
    * put some mappings of forwarder addresses to dates and user objects in the Forwarder table
    * one of these will be expired
    * one of these will not
    * try 
        * email forwarder address that's not in the database at all
        * email forwarder that's in the db but is expired
        * email forwarder that's in the db and is not expired
    '''


    def test(self):
        # this function was only being used by this test--so i moved it here. it was in base/controllers --parker
        def get_email_address_from_forwarder_address(forwarder_address):
            Forwarder = mysite.profile.models.Forwarder
            # look in Forwarder model
            # see if the forwarder address that they gave us is expired
            # if it isn't return the user's real email address
            # if it is expired, or if it's not in the table at all, return None
            try:
                return Forwarder.objects.get(address=forwarder_address, expires_on__gt=datetime.datetime.utcnow()).user.email
            except Forwarder.DoesNotExist:
                return None
        def test_possible_forwarder_address(address, future, actually_create, should_work):
            future_number = future and 1 or -1
            if actually_create:
                expiry_date = datetime.datetime.utcnow() + future_number*datetime.timedelta(minutes=10)
                user = User.objects.get(username="paulproteus")
                new_mapping = mysite.profile.models.Forwarder(address=address,
                        expires_on=expiry_date, user=user)
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

class PersonTagCache(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('django.core.cache.cache')
    def test(self, mock_cache):
        '''This test:
        * Creates one person whose tag_texts say he can mentor in Banshee
        * Ensures that get_tag_texts_for_map() caches that
        * Deletes the Link_Person_Tag object
        * Ensures the celery task re-fills the cache entry as being empty.'''

        # 0. Our fake cache is empty always
        mock_cache.get.return_value = None

        # 1. Set link
        paulproteus = Person.objects.get(user__username='paulproteus')
        Project.create_dummy(name='Banshee')
        can_mentor, _ = TagType.objects.get_or_create(name='can_mentor')
        
        willing_to_mentor_banshee, _ = Tag.objects.get_or_create(
            tag_type=can_mentor,
            text='Banshee')
        link = Link_Person_Tag(person=paulproteus,
                               tag=willing_to_mentor_banshee)
        link.save()

        # 2. Call get_tag_texts_for_map() and make sure we cached it
        paulproteus.get_tag_texts_for_map()
        mock_cache.set.assert_called_with(paulproteus.get_tag_texts_cache_key(),
                                          simplejson.dumps({'value': ['Banshee']}),
                                          86400 * 10)
        mock_cache.set.reset_mock()

        # 3. Delete the link() and make sure the cache has the right value
        link.delete() # should enqueue a task to update the cache (post-delete)
        mock_cache.delete.assert_called_with(paulproteus.get_tag_texts_cache_key())

        mock_cache.set.assert_called_with(paulproteus.get_tag_texts_cache_key(),
                                          simplejson.dumps({'value': []}),
                                          86400 * 10)
        mock_cache.set.reset_mock()

        # 4. Create a new Link and make sure it's cached properly again
        link = Link_Person_Tag(person=paulproteus,
                               tag=willing_to_mentor_banshee)
        link.save() # should fire bgtask to update the cache (post-save signal)
        mock_cache.set.assert_called_with(paulproteus.get_tag_texts_cache_key(),
                                          simplejson.dumps({'value': ['Banshee']}),
                                          86400 * 10)

class PersonProjectCache(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('django.core.cache.cache')
    def test(self, mock_cache):
        '''This test:
        * Creates one person who has contributed to a certain project
        * Ensures that when the PFE is saved, we cache the person's list of projects
        * Remove the person from that project
        * Ensures that when the PFE is deleted, we cache the person's list of projects
        '''

        # 0. Our fake cache is empty always
        mock_cache.get.return_value = None

        project = Project.create_dummy(name='project name')

        # 1. Give the person a PFE
        paulproteus = Person.objects.get(user__username='paulproteus')
        portfolio_entry, pfe_was_created = PortfolioEntry.objects.get_or_create(
            project=project, is_published=True, person=paulproteus)
        self.assert_(pfe_was_created)

        # 2. Make sure we cached it
        mock_cache.set.assert_called_with(
                paulproteus.get_cache_key_for_projects(),
                simplejson.dumps({'value': [ 'project name']}), 86400 * 10)
        mock_cache.set.reset_mock()

        # 3. Delete the PFE, and make sure the cache got deleted
        portfolio_entry.delete()
        mock_cache.delete.assert_called_with(
            paulproteus.get_cache_key_for_projects())
        mock_cache.set.assert_called_with(
            paulproteus.get_cache_key_for_projects(),
            simplejson.dumps({'value': []}),
            86400 * 10)
        mock_cache.set.reset_mock()

        # 4. Add a new one, and make sure it's up to date
        portfolio_entry, _ =PortfolioEntry.objects.get_or_create(
            project=Project.create_dummy(name='other name'),
            is_published=True,
            person=paulproteus)
        mock_cache.set.assert_called_with(
            paulproteus.get_cache_key_for_projects(),
            simplejson.dumps({'value': [
                'other name']}),
            86400 * 10)
        mock_cache.set.reset_mock()

class ForwarderGetsCreated(TwillTests):
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

class EditYourName(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_settings_page_form(self):
        # visit generic settings page
        self.login_with_twill()
        tc.go(make_twill_url('http://openhatch.org/'))
        tc.follow('settings')
        tc.follow('Name')
        tc.fv(1, 'first_name', 'Gottfried')
        tc.fv(1, 'last_name', 'Leibniz')
        tc.submit()
        tc.go(make_twill_url('http://openhatch.org' + Person.objects.get().profile_url))
        tc.find('Gottfried Leibniz')
        tc.notfind('Asheesh Laroia')

class FixAllTagsQueryWhenHaystackReturnsHalfPeople(TwillTests):

    def test(self):
        things = UserList.UserList([
            ObjectFromDict({'object': None}),
            ObjectFromDict({'object': 'a real thing'})])
        things.load_all = mock.Mock()
        just_real_thing = mysite.base.controllers.haystack_results2db_objects(things)
        self.assertEqual(just_real_thing, ['a real thing'])
        self.assert_(things.load_all.called)

class PersonCanReindexHimself(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.profile.tasks.ReindexPerson.delay')
    def test(self, mock_delay):
        p = Person.objects.get(user__username='paulproteus')
        p.reindex_for_person_search()
        self.assertEqual(mock_delay.call_args,
                         ( (), {'person_id': p.id}))

class PersonCanSetHisExpandNextStepsOption(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_set_to_true(self):
        # Starts as false
        p = Person.objects.get(user__username='paulproteus')
        p.expand_next_steps = False
        p.save()

        # Now, set to True...
        client = self.login_with_client()
        url = reverse(mysite.profile.views.set_expand_next_steps_do)
        client.post(url, {'value': 'True'})
        p = Person.objects.get(user__username='paulproteus')
        self.assert_(p.expand_next_steps)
        # FIXME test response

    def test_set_to_false(self):
        # Starts as True
        p = Person.objects.get(user__username='paulproteus')
        p.expand_next_steps = True
        p.save()

        # Now, set to False...
        client = self.login_with_client()
        url = reverse(mysite.profile.views.set_expand_next_steps_do)
        client.post(url, {'value': 'False'})
        p = Person.objects.get(user__username='paulproteus')
        self.assertFalse(p.expand_next_steps)

class PeopleMapForNonexistentProject(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.profile.views.project_query2mappable_orm_people')
    def test(self, make_empty_list):
        make_empty_list.return_value = ([], {})
        mock_request = ObjectFromDict(
            {u'GET': {u'q': u'project:Phorum'},
             u'user': User.objects.get(username='paulproteus')})
        mysite.profile.views.people(mock_request)
        # Yay, no exception.

    @mock.patch('mysite.profile.views.project_query2mappable_orm_people')
    def test_icanhelp(self, make_empty_list):
        make_empty_list.return_value = ([], {})
        mock_request = ObjectFromDict(
            {u'GET': {u'q': u'icanhelp:Phorum'},
             u'user': User.objects.get(username='paulproteus')})
        mysite.profile.views.people(mock_request)
        # Yay, no exception.

class BugModificationTimeVersusEpoch(TwillTests):
    @mock.patch('mysite.profile.tasks.fill_recommended_bugs_cache')
    def test(self, mock_thing):
        # Read the comments in the Epoch model if you haven't yet
        epoch_at_start = mysite.search.models.Epoch.get_for_model(
            mysite.search.models.Bug)
        # This is a new bug, so we might want to invalidate the cache for
        # recommended-bug lists, or people won't see this bug in their list of
        # "Recommended bugs"
        mysite.search.models.Bug.create_dummy_with_project()
        # Let's the invalidate the cache
        mysite.profile.tasks.sync_bug_epoch_from_model_then_fill_recommended_bugs_cache()
        # Make sure that the cache timestamp has been updated
        new_epoch = mysite.search.models.Epoch.get_for_model(
            mysite.search.models.Bug)
        self.assert_(new_epoch > epoch_at_start)
        self.assert_(mock_thing.called)

class SaveReordering(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        # Log in 
        client = self.login_with_client()

        paul = Person.get_by_username('paulproteus')

        pfes = [
                PortfolioEntry.create_dummy_with_project(person=paul, sort_order=-1),
                PortfolioEntry.create_dummy_with_project(person=paul, sort_order=-2),
                ]

        def get_ordering():
            response = client.get(reverse(mysite.profile.views.gimme_json_for_portfolio))
            obj = simplejson.loads(response.content)
            return [pfe['pk'] for pfe in obj['portfolio_entries']]

        ordering_beforehand = get_ordering()

        self.assertEqual(ordering_beforehand, [pfes[0].pk, pfes[1].pk])

        # POST to a view with a list of ids
        view = reverse(mysite.base.views.save_portfolio_entry_ordering_do)
        client.post(view, {'sortable_portfolio_entry[]': [str(pfes[1].pk), str(pfes[0].pk)]})

        # Get the list of projects
        ordering_afterwards = get_ordering()

        # Verify that these projects have the right sort order
        self.assertEqual(ordering_afterwards, [pfes[1].pk, pfes[0].pk])

class ArchiveProjects(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        # Log in 
        client = self.login_with_client()

        paul = Person.get_by_username('paulproteus')

        pfes = [
                PortfolioEntry.create_dummy_with_project(person=paul, sort_order=-1),
                PortfolioEntry.create_dummy_with_project(person=paul, sort_order=-2),
                ]

        # POST to a view with a list of ids
        view = reverse(mysite.base.views.save_portfolio_entry_ordering_do)
        client.post(view, {'sortable_portfolio_entry[]': [str(pfes[0].pk), "FOLD", str(pfes[1].pk)]})

        this_should_be_archived = PortfolioEntry.objects.get(pk=pfes[1].pk)
        self.assert_(this_should_be_archived.is_archived)


class MockBitbucketImport(BaseCeleryTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    
    @mock.patch('mysite.customs.bitbucket.get_user_repos')
    @mock.patch('mysite.customs.github.find_primary_language_of_repo', do_nothing)
    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_bitbucket_profile_import(self, mock_bitbucket_projects):
        """Test that we can get projects from Bitbucket"""
        description = 'A project designed to test imports from Bitbucket'
        mock_bitbucket_projects.return_value = [{
            "website": "", 
            "slug": "MOCK_ccHost", 
            "name": "MOCK ccHost", 
            "followers_count": 1, 
            "description": description
            }]
        data_we_expect = [{
            'contributor_role': u'Created a repository on Bitbucket.',
            'languages': u''}] #Bitbucket doesn't show languages via non-authenticated api.
        summaries_we_expect = [u'Created a repository on Bitbucket.']
        
        self._test_data_source_via_emulated_bgtask(
            source='bb', data_we_expect=data_we_expect,
            summaries_we_expect=summaries_we_expect)

        self.assertEqual(PortfolioEntry.objects.all().count(),1)
        self.assertEqual(PortfolioEntry.objects.get().project_description,
                         description)

class Notifications(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @staticmethod 
    def get_email_context(recipient):
        """ This helper method retrieves the context of the email we're
        currently planning to send to the recipient. """

        # First move the timestamp back
        Timestamp.update_timestamp_for_string(
                send_weekly_emails.Command.TIMESTAMP_KEY,
                override_time=Timestamp.ZERO_O_CLOCK)
        command = mysite.profile.management.commands.send_weekly_emails.Command()
        context = command.get_context_for_weekly_email_to(recipient)
        return context

    @staticmethod
    def send_email_and_get_outbox():
        command = mysite.profile.management.commands.send_weekly_emails.Command()
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

    def test_checkbox_manipulates_db(self):
        self.login_with_twill()

        # By default, paulproteus has the column email_me_weekly_re_projects set to True
        paul = Person.get_by_username('paulproteus')
        self.assert_(paul.email_me_weekly_re_projects)

        # Now let's set it to false

        # Visit the homepage
        tc.go(better_make_twill_url('http://openhatch.org/'))

        # Visit the settings page
        tc.follow('settings')

        # Follow the link that says "Email"
        tc.follow('Email')

        # Click it and you find a form for changing your notification settings
        # In the form, there's a checkbox labeled "Email me weekly about
        # activity on my projects" (or something like that)

        # Uncheck the checkbox, and submit the form

        tc.fv(1, 'email_me_weekly_re_projects', '0')
        tc.submit()

        # Now you no longer receive emails. For the purposes of this test,
        # let's just inspect the database to see whether we've written down the
        # fact that you don't want to receive emails about recent activity on
        # your projects.

        paul = Person.get_by_username('paulproteus')

        self.assertFalse(paul.email_me_weekly_re_projects)

    def add_two_people_to_a_project_and_send_weekly_emails(self,
            people_want_emails=True, how_to_add_people=None, outbox_or_context=None,
            emails_should_actually_be_sent=True):

        self.assert_(outbox_or_context in ['outbox', 'context'])

        time_range_endpoint_at_func_top = send_weekly_emails.Command.get_time_range_endpoint_of_last_email()

        project_with_two_participants = Project.create_dummy()

        participants_who_are_news_to_each_other = [] # initial value
        
        if not how_to_add_people:
            how_to_add_people = [Notifications.add_contributor,
                    Notifications.add_contributor]

        for add_person in how_to_add_people:
            participant = Person.create_dummy(
                    first_name=str(add_person),
                    email_me_weekly_re_projects=people_want_emails)
            add_person(participant, project_with_two_participants)
            participants_who_are_news_to_each_other.append(participant)

        self.assertEqual(len(participants_who_are_news_to_each_other), 2)

        output = None

        if outbox_or_context == 'outbox':
            outbox = Notifications.send_email_and_get_outbox()
            output = outbox
            if emails_should_actually_be_sent:
                # The timestamp log should have been modified since the top of the function.
                self.assert_(
                        send_weekly_emails.Command.get_time_range_endpoint_of_last_email()
                        > time_range_endpoint_at_func_top)

        if outbox_or_context == 'context':
            command = mysite.profile.management.commands.send_weekly_emails.Command()
            email_contexts = {} # initial value
            for participant in participants_who_are_news_to_each_other:
                email_context = command.get_context_for_weekly_email_to(participant)
                email_contexts[participant.pk] = email_context
            output = email_contexts

        return ( participants_who_are_news_to_each_other, output )

    @staticmethod
    def add_contributor(person, project):
        PortfolioEntry.create_dummy( person=person, project=project, is_published=True)

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
                self.add_two_people_to_a_project_and_send_weekly_emails(
                    people_want_emails=True, outbox_or_context='outbox') )

        self.assertEqual(len(outbox), 2)

        self.assert_only_these_people_were_emailed(contributors, outbox)
    
    def test_dont_email_the_people_with_checkboxes_cleared(self):

        contributors, outbox = (
                self.add_two_people_to_a_project_and_send_weekly_emails(
                    people_want_emails=False, outbox_or_context='outbox') )

        self.assertEqual(len(outbox), 0)

    # Test the content of the email (test the rendered template, and/or
    # test the context passed to that template)
    def test_email_context_contains_contributors(self):

        paul = Person.get_by_username('paulproteus')

        # To set up this test, let's create a project
        project = Project.create_dummy()

        # Paul will be the recipient of the email, and he's a contributor to
        # the project created above, so he'll be getting information about that
        # project's recent activity in his weekly email
        PortfolioEntry.create_dummy(person=paul, project=project, is_published=True)

        NUMBER_OF_NEW_CONTRIBUTORS_OTHER_THAN_PAUL = 5

        # 5 people have joined this project in the last week
        for i in range(NUMBER_OF_NEW_CONTRIBUTORS_OTHER_THAN_PAUL):
            p = Person.create_dummy()
            PortfolioEntry.create_dummy(person=p, project=project, is_published=True)

        # 1 person joined this project two weeks ago (too long ago to mention
        # in this email)
        now = datetime.datetime.utcnow()
        seven_days_ago = now - datetime.timedelta(days=7)
        eight_days_ago = now - datetime.timedelta(days=8)

        Timestamp.update_timestamp_for_string(
                send_weekly_emails.Command.TIMESTAMP_KEY,
                override_time=seven_days_ago)

        veteran = Person.create_dummy()
        veteran.user.first_name = 'VETERAN'
        veteran.user.save()
        PortfolioEntry.create_dummy(person=veteran, project=project,
                is_published=True, date_created=eight_days_ago)

        # Psst, notice that we have sent out a round of weekly emails since the
        # veteran added the project to her profile. So the veteran should not
        # appear in the next round of weekly emails.
        
        # Let's assert that the email context contains enough information to
        # say that such and such a project received 6 contributors in the
        # last week, here are the person objects for 3 of them

        new_contributors = list(project.get_contributors())
        new_contributors.remove(paul)
        new_contributors.remove(veteran)

        command = mysite.profile.management.commands.send_weekly_emails.Command()
        context = command.get_context_for_weekly_email_to(paul)

        project_name, actual_people = context['project_name2people'][0]

        # Assert that the truncated list of contributors that will appear in
        # the email is a subset of the people we added above
        for c in actual_people['display_these_contributors'] :
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
            for project_name, people_data in context['project_name2people']:
                contribs_count = str(people_data['contributor_count'])
                self.assert_(project_name in msg)
                self.assert_(contribs_count in msg)
                for p in people_data['display_these_contributors']:
                    self.assert_(p.user.username in msg)

        #context['new_wannahelpers']
        #context['recent_chatter_answers'],

    def test_you_appear_in_summary_sometimes(self):
        # If you're a newly marked contributor to project P, and there are
        # fewer than 3 other newly marked contributors to P, then you appear in
        # the shortlist of newly marked contributors to P.

        paul = Person.get_by_username('paulproteus')

        def get_contributors_data():
            context = Notifications.get_email_context(paul)
            project_name, contributors_data = context['project_name2people'][0]
            return contributors_data

        # To set up this test, let's create a project
        project = Project.create_dummy()

        # Paul will be the recipient of the email, and he's a contributor to
        # the project created above, so he'll be getting information about that
        # project's recent activity in his weekly email
        PortfolioEntry.create_dummy(person=paul, project=project, is_published=True)

        # Since paul is the only newly marked contributor to this project,
        # there will be no news to report, and by stipulation the context of
        # the email will simply be None
        self.assertEqual(Notifications.get_email_context(paul), None)

        number_of_new_contributors_other_than_paul = 2

        # 2 people have joined this project in the last week
        for i in range(number_of_new_contributors_other_than_paul):
            p = Person.create_dummy()
            PortfolioEntry.create_dummy(person=p, project=project, is_published=True)

        data = get_contributors_data()
        self.assertEqual(len(data['display_these_contributors']), 3)
        self.assert_(paul in data['display_these_contributors'])

        # Now add one more person 
        p = Person.create_dummy()
        PortfolioEntry.create_dummy(person=p, project=project, is_published=True)

        data = get_contributors_data()
        self.assertEqual(len(data['display_these_contributors']), 3)
        self.assert_(paul not in data['display_these_contributors'])

        # Now let's test that when there's a project containing just paul, that
        # project doesn't show up in the summary (even when there are other
        # projects to speak of)
        solo_project = Project.create_dummy(name='solo project')
        PortfolioEntry.create_dummy(person=paul, project=solo_project, is_published=True)
        context = Notifications.get_email_context(paul)
        project_name2people = context['project_name2people']
        first_project_name, contributors_data = project_name2people[0]

        # The first project appears in the email
        self.assertEqual(first_project_name, project.name)

        # The second project doesn't appear
        self.assertEqual(len(project_name2people), 1)


    def test_dont_send_email_when_recipient_has_no_recent_fellow_contributors(self):
        # This recipient is the only recent member of her projects
        no_news_for_me = Person.create_dummy(email='dont_email_me@example.com')
        PortfolioEntry.create_dummy_with_project(person=no_news_for_me, is_published=True)

        # The person above should NOT get an email

        # We could now simply run the email sender and make sure that NO email
        # was sent. But this is consistent with a failure case, in which NO
        # email gets sent ever (for some reason). Because sending email to our
        # users is a pretty sensitive piece of functionality, I want to be
        # extra careful to test for failure cases. So I'll set up the database
        # so that some OTHER folks will get an email. Then we'll check to see
        # that no email was ever sent to the person named "no_news_for_me."

        project_with_two_contributors = Project.create_dummy()

        contributors_who_are_news_to_each_other = [] # initial value

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
                send_weekly_emails.Command.TIMESTAMP_KEY,
                override_time=when)

    def try_to_send_some_emails(self, expect_success):
        add_and_send = self.add_two_people_to_a_project_and_send_weekly_emails
        people, outbox = add_and_send(
                how_to_add_people=[
                    Notifications.add_contributor,
                    Notifications.add_wannahelper],
                outbox_or_context='outbox',
                emails_should_actually_be_sent=expect_success)
        were_emails_sent = bool(outbox)
        self.assertEqual(expect_success, were_emails_sent)

    def test_we_dont_send_emails_more_than_once_a_week(self):
        # Test that, no matter what, we never send out emails more than once a
        # week.

        # Here we test two scenarios.
        
        # First, what if we (accidentally) run the
        # send_weekly_emails command today, when we sent the emails yesterday?
        # We want to make sure that we can't accidentally send people two
        # emails in a single week...

        # Calculate some datetime objects we'll need during this test
        now = datetime.datetime.utcnow()

        just_under_seven_days = datetime.timedelta(days=6, hours=23)
        just_under_seven_days_ago = now - just_under_seven_days

        # Let's record that emails were sent under 7 days ago
        Notifications.set_when_emails_were_last_sent(just_under_seven_days_ago)

        # Try to send emails, but expect no emails to be sent, because we've
        # recorded that we sent emails within the last 7 days.
        self.try_to_send_some_emails(expect_success=False)

    def test_that_we_do_email_you_if_the_last_email_was_sent_long_enough_ago(self):

        # Now let's make sure that the converse scenario works as expected. We
        # sent the emails over seven days ago, and somebody runs the
        # send_weekly_emails command. In this scenario, emails SHOULD be sent.

        now = datetime.datetime.utcnow()
        just_over_seven_days = datetime.timedelta(days=7, hours=1)
        just_over_seven_days_ago = now - just_over_seven_days

        # Let's record that emails were sent just OVER 7 days ago
        Notifications.set_when_emails_were_last_sent(just_over_seven_days_ago)

        # Try to send emails, but expect some emails to YES be sent, because we've
        # recorded that we sent emails over 7 days ago.
        self.try_to_send_some_emails(expect_success=True)

    def test_that_contributors_and_wanna_helpers_are_emailed_about_one_another(self):
        # Set up the database so that a contributor will receive an email about
        # a wanna helper, and vice versa
        how_to_add_people = [Notifications.add_contributor, Notifications.add_wannahelper]
        people, email_contexts = self.add_two_people_to_a_project_and_send_weekly_emails(
                    how_to_add_people=how_to_add_people, outbox_or_context='context')

        contributor, wanna_helper = people

        contributor_e_c = email_contexts[contributor.pk]
        self.assert_(contributor_e_c)
        wannahelper_e_c = email_contexts[wanna_helper.pk]
        self.assert_(wannahelper_e_c)

        # Assert that contributor gets emailed about the wanna helper 
        wanna_helpers_in_email_to_contributor = contributor_e_c[
            'project_name2people'][0][1]['display_these_wannahelpers']
        self.assert_(wanna_helper in wanna_helpers_in_email_to_contributor)

        # Assert that wanna helper gets emailed about the contributor 
        contributors_in_email_to_wanna_helper = wannahelper_e_c[
                'project_name2people'][0][1]['display_these_contributors']
        self.assert_(contributor in contributors_in_email_to_wanna_helper)

    def test_projects_this_person_cares_about(self):
        # Test this method:
        # mysite.profile.management.commands.send_weekly_emails
        # .Command.get_projects_this_person_cares_about(person) 

        person = Person.create_dummy()

        # three projects
        project_i_contributed_to = Project.create_dummy()
        project_i_wanna_help = Project.create_dummy()
        project_i_wanna_help_and_contributed_to = Project.create_dummy()

        # first project
        Notifications.add_contributor(person, project_i_contributed_to)

        # second project
        Notifications.add_wannahelper(person, project_i_wanna_help)

        # third project
        Notifications.add_contributor(person, project_i_wanna_help_and_contributed_to)
        Notifications.add_wannahelper(person, project_i_wanna_help_and_contributed_to)

        projects_i_care_about = mysite.profile.management.commands.send_weekly_emails.Command.get_projects_this_person_cares_about(person) 
        expected = [project_i_contributed_to, project_i_wanna_help, 
                project_i_wanna_help_and_contributed_to]
        expected.sort(key=lambda x: x.name)
        self.assertEqual(projects_i_care_about, expected)

    def test_dont_tell_me_about_projects_where_i_am_the_only_participant(self):
        # FIXME: This will cease to make sense when we add project answers to
        # the email
        person = Person.create_dummy()
        project_i_wanna_help_and_contributed_to = Project.create_dummy()
        Notifications.add_contributor(person, project_i_wanna_help_and_contributed_to)
        Notifications.add_wannahelper(person, project_i_wanna_help_and_contributed_to)
        command = mysite.profile.management.commands.send_weekly_emails.Command()
        email_context = command.get_context_for_weekly_email_to(person) 
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
        seven_days_ago = now - datetime.timedelta(days=7)
        nine_days_ago = now - datetime.timedelta(days=9)

        # The timespan for this email is The Last Seven Days
        Timestamp.update_timestamp_for_string(
                send_weekly_emails.Command.TIMESTAMP_KEY,
                override_time=seven_days_ago)

        # This dude signs up to be a helper
        Notifications.add_wannahelper(new_wh, a_project)

        # This dude signed up too long ago to appear in this email
        Notifications.add_wannahelper(old_wh, a_project, nine_days_ago)

        # Assert that the new w.h. was included in the email and the old was not.
        command = mysite.profile.management.commands.send_weekly_emails.Command()
        email_context = command.get_context_for_weekly_email_to(email_recipient) 
        self.assert_(email_context)
        project_name2people = email_context['project_name2people']
        self.assertEqual(len(project_name2people), 1)
        project_name, people = project_name2people[0]
        self.assertEqual(
                [new_wh],
                people['display_these_wannahelpers'],
                )

class AfterCreatingADiaPingTwisted(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.customs.ping_twisted.ping_it')
    def test(self, mock_ping_it):
        ### This is a simple test. We just:
        # * Create a DIA
        # * Ensure the pingTwisted() function was called.
        asheesh = Person.objects.get(user__username='paulproteus')
        mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='gh', query='paulproteus')
        self.assertTrue(mock_ping_it.called)

# vim: set ai et ts=4 sw=4 nu:
