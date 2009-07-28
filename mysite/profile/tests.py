# Imports {{{
import base.tests
from base.tests import make_twill_url

from search.models import Project
from profile.models import Person, ProjectExp, Tag, TagType, Link_Person_Tag, Link_ProjectExp_Tag, DataImportAttempt

import profile.views

import settings

from customs import ohloh 

import re
from StringIO import StringIO
import urllib
import simplejson
import BeautifulSoup
import time
import tasks 
import mock

import django.test
from django.core import management
from django.test.client import Client
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
# }}}

class ProfileTests(base.tests.TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus',
            'cchost-data-imported-from-ohloh']

    def testSlash(self):
        response = self.client.get('/people/')

    def test__projectexp_add(self):
        # {{{
        username = 'paulproteus'

        project_name = 'seeseehost'
        description = 'did some work'
        url = 'http://example.com/'
        exp = ProjectExp.create_from_text(username, project_name,
                                    description, url)
        found = list(ProjectExp.objects.filter(person__user__username=username))
        # Verify it shows up in the DB
        self.assert_('seeseehost' in [f.project.name for f in found])
        # Verify it shows up in profile_data_from_username
        data = profile.views.profile_data_from_username('paulproteus')
        self.assert_(data['person'].user.username == 'paulproteus')
        projects = [thing[0].project.name for thing in
                    data['exp_taglist_pairs']]
        self.assert_('seeseehost' in projects)
        # }}}

    def test__project_exp_create_from_text__unit(self):
        # {{{

        # Create requisite objects
        person = Person.objects.get(user__username='paulproteus')
        project = Project.objects.get(name='ccHost')

        # Assemble text input
        username = person.user.username
        project_name = project.name
        description = "sample description"
        url = "http://sample.com"
        man_months = "3"
        primary_language = "perl"

        ProjectExp.create_from_text(
                person.user.username,
                project.name,
                description,
                url,
                man_months,
                primary_language)
        # }}}

    def test_change_my_name(self):
        """Test that user can change his/her first and last name, and that it appears in the logged-in user's profile page."""
        # {{{
        self.login_with_twill()

        # Assert we're on profile page.
        tc.url('/people/paulproteus')

        # No named entered yet
        tc.notfind('Newfirst Newlast')

        # Let's go enter a name
        tc.follow('Edit name')

        tc.url('/edit/name')
        tc.fv('edit_name', 'first_name', 'Newfirst')
        tc.fv('edit_name', 'last_name', 'Newlast')
        tc.submit()

        tc.url('/people/paulproteus')

        # Has name been entered correctly? Hope so!
        tc.find('Newfirst')
        tc.find('Newlast')
        # }}}

    # }}}

class DebTagsTests(base.tests.TwillTests):
    # {{{

    def testAddOneDebtag(self):
        tag = profile.views.add_one_debtag_to_project('alpine', 'implemented-in::c')
        self.assertEqual(profile.views.list_debtags_of_project('alpine'),
                         ['implemented-in::c'])

    def testImportDebtags(self):
        profile.views.import_debtags(cooked_string=
                                     'alpine: works-with::mail, protocol::smtp') # side effects galore!
        self.assertEqual(set(profile.views.list_debtags_of_project('alpine')),
                         set(['works-with::mail', 'protocol::smtp']))
    # }}}

#class ExpTag(base.tests.TwillTests):

# If you're looking for SourceForge and FLOSSMole stuff, look in the repository history.

class PersonTabProjectExpTests(base.tests.TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def test_project_exp_page_template_displays_project_exp(self):
        # {{{
        url = 'http://openhatch.org/people/paulproteus'
        tc.go(make_twill_url(url))
        tc.find('ccHost')
        # }}}
    # }}}

class ProjectExpTests(base.tests.TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
            'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def projectexp_add(self, project__name, project_exp__description, project_exp__url):
        """Paulproteus can login and add a projectexp to bumble."""
        # {{{
        self.login_with_twill()

        tc.follow('Add +')

        tc.url('/form/projectexp_add')
        tc.fv('projectexp_add', 'project__name', project__name)
        tc.fv('projectexp_add', 'project_exp__description', project_exp__description)
        tc.fv('projectexp_add', 'project_exp__url', project_exp__url)
        tc.submit()
        tc.find(project__name)
        tc.find(project_exp__description)
        tc.find(project_exp__url)
        # }}}

    def test_projectexp_add(self):
        """Paulproteus can login and add two projectexps."""
        # {{{
        self.login_with_twill()
        self.projectexp_add('asdf', 'qwer', 'jkl')
        self.projectexp_add('asdf', 'QWER!', 'JKL!')
        # }}}

    def test_projectexp_delete(self):
        '''The server can log in paulproteus remove the word 'ccHost' from his profile by posting to the delete controller's URL.'''
        # {{{
        client = Client()
        username='paulproteus'
        client.login(username=username,
                     password="paulproteus's unbreakable password")

        person_page = '/people/%s/' % urllib.quote(username)
        
        # Load up the profile page
        response = client.get(person_page)
        # See! It talks about ccHost!
        self.assertContains(response, 'ccHost')

        # POST saying we want to delete the ccHost experience...
        # luckily I read the fixture and I know its ID is 13
        response = client.post('/people/delete-experience/do',
                               {'id': '13'})
        
        # Now re-GET the profile
        response = client.get(person_page)

        # See! It no longer talks about ccHost!
        self.assertNotContains(response, 'ccHost')
        # }}}

    def test_projectexp_delete_unauthorized(self):
        '''Barry tries to delete a ProjectExp he doesn't own and fails.'''
        # {{{

        # Meet Barry, a shady character.
        barry = User.objects.get(username='barry')
        barry_password = 'parallelism'
        client = Client()
        login_success = client.login( username=barry.username, 
                password=barry_password)
        self.assert_(login_success)

        # Barry doesn't own ProjectExp #13
        self.assertNotEqual( barry,
                ProjectExp.objects.get(id=13).person.user)

        # What happens if he tries to delete ProjectExp #13
        response = client.post('/people/delete-experience/do',
                {'id': '13'})

        # Still there, Barry. Keep on truckin'.
        self.assert_(ProjectExp.objects.get(id=13))

        # }}}

    def test_projectexp_delete_web(self):
        '''Notorious user of OpenHatch, paulproteus, can log in and remove the word 'ccHost' from his profile by clicking the appropriate delete button.'''
        # {{{

        self.login_with_twill()

        # Load up the ProjectExp edit page.
        project_name = 'ccHost'
        exp_url = 'http://openhatch.org/people/paulproteus/projects/%s' % (
                urllib.quote(project_name))
        tc.go(make_twill_url(exp_url))

        # See! It talks about ccHost!
        tc.find(project_name)

        # Click the correct delete button...
        tc.config('readonly_controls_writeable', True)
        tc.fv('delete-projectexp-13', 'id', '13')   # Bring twill's attention
                                                    # to the form named
                                                    # ``delete-projectexp-13''.
        tc.submit()

        # FIXME: What page are we on now?

        # Alakazam! It's gone.
        tc.notfind('ccHost')
        # }}}

    def test_cannot_delete_exps_without_id(self):
        '''While paulproteus is logged in, he posts directly to /people/delete-experience/do without specifying the id of the projectexp you want to delete. The server returns a 500 error and a check string.'''
        # {{{
        
        client = Client()
        username='paulproteus'
        client.login(username=username,
                     password="paulproteus's unbreakable password")

        person_page = '/people/%s/' % urllib.quote(username)
        
        # POST saying we want to delete the
        # ccHost experience...
        # But it's missing the ID!
        post_data = {}
        response = client.post('/people/delete-experience/do',
                post_data)
        
        self.assertEquals(response.status_code, 500)
        # }}}

    def test_person_involvement_description(self):
        # {{{
        username = 'paulproteus'
        project_name = 'ccHost'
        url = 'http://openhatch.org/people/%s/projects/%s' % (
                urllib.quote(username), urllib.quote(project_name))
        tc.go(make_twill_url(url))
        tc.find('1 month')
        tc.find('shell script')
        # }}}

    # FIXME: Move these next two functions to their proper home.

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
        url = 'http://openhatch.org/people/edit/info'
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
            self.assert_(', '.join(tag_dict[tag_type_name]) in text)

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

# Create a mock Ohloh get_contribution_by_username
mock_gcibu = mock.Mock()
mock_gcibu.return_value = [{
        'man_months': 1,
        'project': u'ccHost',
        'project_homepage_url':
            u'http://wiki.creativecommons.org/CcHost',
        'primary_language': u'shell script'}]

# Create a mock Ohloh get_contribution_info_by_ohloh_username
mock_gcibou = mock.Mock()
mock_gcibou.return_value = [{
        'man_months': 1,
        'project': u'who knows',
        'project_homepage_url':
            u'http://wiki.creativecommons.org/CcHost',
        'primary_language': u'Vala'}]

# Create a mock Launchpad get_info_for_launchpad_username
mock_giflu = mock.Mock()
mock_giflu.return_value = {
        'F-Spot': {
            'url': 'http://launchpad.net/f-spot',
            'involvement_types': ['Bug Management', 'Bazaar Branches'],
            'languages': ['python', 'ruby'],
            }
        }

# FIXME: If this is made dynamically, it would be easier!
class MockFetchPersonDataFromOhloh(object):
    real_task_class = profile.tasks.FetchPersonDataFromOhloh
    @classmethod
    def delay(*args, **kwargs):
        args = args[1:] # FIXME: Wonder why I need this
        task = MockFetchPersonDataFromOhloh.real_task_class()
        task.run(*args, **kwargs)

class CeleryTests(base.tests.TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('customs.ohloh.Ohloh.get_contribution_info_by_username', mock_gcibu)
    @mock.patch('profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_ohloh_import_via_emulated_bgtask(self):
        """1. Go to the page that has paulproteus' data.  2. Verify that the page doesn't yet know about ccHost. 3. Run the celery task ourselves, but instead of going to Ohloh, we hand-prepare data for it."""
        # {{{
        # do this work for user = paulproteus
        username = 'paulproteus'
        person = Person.objects.get(user__username=username)

        # Store a note in the DB we're about to do a background task
        dia = DataImportAttempt(query=username, source='rs',
                                person=person)
        dia.person_wants_data = True
        dia.save()
        

        url = '/people/gimme_json_that_says_that_commit_importer_is_done'
        
        client = self.login_with_client()

        # Ask if background job has been completed.
        # We haven't even created the background job, so it should
        # not be!
        response_before = client.get(url)
        response_json = simplejson.loads(response_before.content)
        self.assertEquals(
            response_json[0]['pk'], dia.id)
        self.assertFalse(response_json[0]['fields']['completed'])
        
        # Ask if involvement fact has been loaded.
        # We haven't loaded it, so the answer should be no.
        project_name = 'ccHost'
        self.assertFalse(list(ProjectExp.objects.filter(
            project__name=project_name)))

        dia.do_what_it_says_on_the_tin()
        # NB: The task is being run, but the ohloh API communication
        # is mocked out.

        # Now that we have synchronously run the task, it should be
        # marked as completed.
        self.assert_(DataImportAttempt.objects.get(id=dia.id).completed)

        # Check again
        response_after = client.get(url)

        # Ask if background job has been completed. (Hoping for yes.)
        response_json = simplejson.loads(response_after.content)
        self.assertEquals(
            response_json[0]['pk'], dia.id)
        self.assert_(response_json[0]['fields']['completed'])

        # Ask if involvement fact has been loaded. (Hoping for yes.)
        self.assert_(list(ProjectExp.objects.filter(
            project__name=project_name, person=person)))

        # }}}

    # FIXME: One day, test that after self.test_slow_loading_via_emulated_bgtask
    # getting the data does not go out to Ohloh.

    @mock.patch('customs.lp_grabber.get_info_for_launchpad_username', mock_giflu)
    @mock.patch('profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_launchpad_import_via_emulated_bgtask(self):
        """1. Go to the page that has paulproteus' data.  2. Verify that the page doesn't yet know about F-Spot. 3. Run the celery task ourselves, but instead of going to Launchpad, we hand-prepare data for it."""
        # {{{
        # do this work for user = paulproteus
        username='paulproteus'
        person = Person.objects.get(user__username=username)

        # Store a note in the DB we're about to do a background task
        dia = DataImportAttempt(query=username, source='lp',
                                person=Person.objects.get(
                                    user__username=username))
        dia.person_wants_data = True
        dia.save()

        url = '/people/gimme_json_that_says_that_commit_importer_is_done'
        
        client = Client()
        password="paulproteus's unbreakable password"
        client.login(username=username,
                     password=password)

        # Ask if background job has been completed.
        # We haven't even created the background job, so it should
        # not be!
        response_before = client.get(url)
        response_json = simplejson.loads(response_before.content)
        self.assertEquals(
            response_json[0]['pk'], dia.id)
        self.assertFalse(response_json[0]['fields']['completed'])
        
        # Ask if involvement fact has been loaded.
        # We haven't loaded it, so the answer should be no.
        project_name = 'F-Spot'
        self.assertFalse(list(ProjectExp.objects.filter(
            project__name=project_name)))

        dia.do_what_it_says_on_the_tin()
        # NB: The task is being run, but the ohloh API communication
        # is mocked out.

        # Now that we have synchronously run the task, it should be
        # marked as completed.
        self.assert_(DataImportAttempt.objects.get(id=dia.id).completed)

        # Check again
        response_after = client.get(url)

        # Ask if background job has been completed. (Hoping for yes.)
        response_json = simplejson.loads(response_after.content)
        self.assertEquals(
            response_json[0]['pk'], dia.id)
        self.assert_(response_json[0]['fields']['completed'])

        # Ask if involvement fact has been loaded. (Hoping for yes.)
        self.assert_(list(ProjectExp.objects.filter(
            project__name=project_name, person=person)))

        # }}}

    # FIXME: One day, test that after self.test_slow_loading_via_emulated_bgtask
    # getting the data does not go out to Ohloh.

    # }}}

class UserListTests(base.tests.TwillTests):
    # {{{
    fixtures = [ 'user-paulproteus', 'person-paulproteus',
            'user-barry', 'person-barry']

    def test_display_list_of_users_web(self):
        url = 'http://openhatch.org/people/'
        url = make_twill_url(url)
        tc.go(url)
        tc.find(r'paulproteus')
        tc.find(r'Barry Spinoza \(barry\)')

        tc.follow('paulproteus')
        tc.url('people/paulproteus') 
        tc.find('paulproteus')

    def test_front_page_link_to_list_of_users(self):
        url = 'http://openhatch.org/'
        url = make_twill_url(url)
        tc.go(url)
        tc.follow('Find other folks on OpenHatch')
    # }}}

class ImportContributionsTests(base.tests.TwillTests):
    """ """
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    # Don't include cchost-paulproteus, because we need paulproteus to have
    # zero projectexps at the beginning of test_person_gets_data_iff_they_want_it

    form_url = "http://openhatch.org/people/portfolio/import/"

    def test_show_suggested_data_sources(self):
        # {{{
        self.login_with_twill()

        tc.go(make_twill_url(self.form_url))

        # Check we're on the right page.
        # FIXME: Check URL instead.
        tc.find('Find your contributions around the web!')

        # Enter a username
        username = 'paulproteus'
        tc.fv('usernames_or_emails', 'commit_username_0', username)

        # Click the button that says 'Show me the data sources!'
        tc.submit()

        # ... Magic happens behind the scenes ...

        # Check we're on the right page.
        # FIXME: Check URL instead.
        tc.find('Find your contributions around the web!')

        # Check that suggestions correctly appear
        tc.find("Search all repositories for %s" % username)
        tc.find("I&#39;m %s on Ohloh; import my data." % username)
        tc.find("I&#39;m %s on Launchpad; import my data." % username)

        # FIXME: Verify that BG jobs get created.
        # }}}

    def test_select_data_sources(self):
        # {{{
        client = Client()
        username='paulproteus'
        password="paulproteus's unbreakable password"
        client.login(username=username,
                     password=password)

        ohloh_repo_search_dia = DataImportAttempt(
                    query='who cares',
                    person=Person.objects.get(user__username='paulproteus'),
                    source='rs')
        ohloh_repo_search_dia.save()

        ohloh_account_dia = DataImportAttempt(
                    query='who cares',
                    person=Person.objects.get(user__username='paulproteus'),
                    source='ou')
        ohloh_account_dia.save()

        launchpad_account_dia = DataImportAttempt(
                    query='query',
                    person=Person.objects.get(user__username='paulproteus'),
                    source='lp')
        launchpad_account_dia.save()

        # The default value of person_wants_data is False
        # and this test depends on that being so.
        self.assertFalse(ohloh_repo_search_dia.person_wants_data)
        self.assertFalse(ohloh_account_dia.person_wants_data)
        self.assertFalse(launchpad_account_dia.person_wants_data)

        url = "/people/user_selected_these_dia_checkboxes"
        checkbox_ids_string = "data_import_attempt_%d" % ohloh_repo_search_dia.id
        response = client.post(url, {'checkboxIDs': 
                                     checkbox_ids_string })

        self.assertEqual(response.status_code, 200)

        # Re-get the Ohloh Repository Search object from the DB
        ohloh_repo_search_dia = DataImportAttempt.objects.get(
                    query='who cares',
                    person=Person.objects.get(user__username='paulproteus'),
                    source='rs')
        self.assert_(ohloh_repo_search_dia.person_wants_data)
        self.assertFalse(ohloh_account_dia.person_wants_data)
        self.assertFalse(launchpad_account_dia.person_wants_data)
#}}}

    @mock.patch('customs.ohloh.Ohloh.get_contribution_info_by_username', mock_gcibu)
    @mock.patch('customs.ohloh.Ohloh.get_contribution_info_by_ohloh_username', mock_gcibou)
    @mock.patch('profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_person_gets_data_iff_they_want_it(self):
        # {{{
        client = Client()
        username='paulproteus'
        password="paulproteus's unbreakable password"
        client.login(username=username,
                     password=password)

        a_person = Person.objects.get(user__username='paulproteus')

        # Make two DIAs, attach some ProjectExps to each,
        # as if user had successfully imported some ProjectExps.

        ohloh_repo_search_dia = DataImportAttempt(
                    query='who cares',
                    person=a_person,
                    source='rs')
        ohloh_repo_search_dia.person_wants_data = True
        ohloh_repo_search_dia.save()

        ohloh_account_dia = DataImportAttempt(
                    query='who cares',
                    person=a_person,
                    source='ou')
        ohloh_account_dia.save()

        launchpad_account_dia = DataImportAttempt(
                    query='query',
                    person=Person.objects.get(user__username='paulproteus'),
                    source='lp')
        launchpad_account_dia.save()

        # The default value of person_wants_data is False
        # and this test depends on that being so.
        self.assertFalse(ohloh_account_dia.person_wants_data)
        self.assertFalse(launchpad_account_dia.person_wants_data)

	a_project, _ = Project.objects.get_or_create(name='ccHost')
        an_exp = ProjectExp(project=a_project, description='the description')
        an_exp.data_import_attempt = ohloh_repo_search_dia
        an_exp.save()

        another_project, _ = Project.objects.get_or_create(name='a project name')
        another_exp = ProjectExp(project=another_project, description='the description')
        another_exp.data_import_attempt = ohloh_account_dia
        another_exp.save()

        ohloh_repo_search_dia.do_what_it_says_on_the_tin()
        ohloh_account_dia.do_what_it_says_on_the_tin()
        launchpad_account_dia.do_what_it_says_on_the_tin()

        x = ProjectExp.objects.get(person=a_person)
        self.assertEqual(x.id, an_exp.id)
        # }}}

    def test_action_via_view(self):
        """Send a Person objects and a list of usernames and email addresses to the action controller. Test that the controller really added some corresponding DIAs for that Person."""
        # {{{
        client = Client()
        username='paulproteus'
        client.login(username=username,
                     password="paulproteus's unbreakable password")

        data = {}
        commit_usernames_and_emails = ["bilbo", "bilbo@baggin.gs"]
        for n, cu in enumerate(commit_usernames_and_emails):
            data["commit_username_%d" % n] = cu

        # Not a DIA in sight.
        self.assertFalse(list(DataImportAttempt.objects.filter(person=Person.objects.get(user__username='paulproteus'))))

        response = client.post('/people/portfolio/import/prepare_data_import_attempts_do', data) 

        # DIAs, nu?
        self.assert_(list(DataImportAttempt.objects.filter(person=Person.objects.get(user__username='paulproteus'))))
        #}}}

    # }}}

# vim: set ai et ts=4 sw=4 nu:

