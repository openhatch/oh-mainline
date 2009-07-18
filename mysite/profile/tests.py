# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4 nu:
# Testing suite for profile

# Imports {{{
from search.models import Project
from profile.models import Person, ProjectExp, Tag, TagType, Link_Person_Tag, Link_ProjectExp_Tag
import profile.views
import profile.controllers
import settings
from customs import ohloh 

import re
import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
import django.test
from django.test import TestCase
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler
from StringIO import StringIO
import urllib
import simplejson
import BeautifulSoup

from django.test.client import Client
import tasks 
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
# }}}

# FIXME: Later look into http://stackoverflow.com/questions/343622/how-do-i-submit-a-form-given-only-the-html-source

# Functions you'll need: {{{
def twill_setup():
    app = AdminMediaHandler(WSGIHandler())
    twill.add_wsgi_intercept("127.0.0.1", 8080, lambda: app)

def twill_teardown():
    twill.remove_wsgi_intercept('127.0.0.1', 8080)

def make_twill_url(url):
    # modify this
    return url.replace("http://openhatch.org/", "http://127.0.0.1:8080/")

def twill_quiet():
    # suppress normal output of twill.. You don't want to
    # call this if you want an interactive session
    twill.set_output(StringIO())
# }}}

class TwillTests(django.test.TestCase):
    '''Some basic methods needed by other testing classes.'''
    # {{{
    def setUp(self):
        twill_setup()
        twill_quiet()

    def tearDown(self):
        twill_teardown()

    def login(self):
        # Visit login page
        login_url = 'http://openhatch.org/people/login'
        tc.go(make_twill_url(login_url))

        # Log in
        username = "paulproteus"
        password = "paulproteus's unbreakable password"
        tc.fv('login', 'login_username', username)
        tc.fv('login', 'login_password', password)
        tc.submit()
    # }}}

class ProfileTests(TwillTests):
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

    # }}}

class DebTagsTests(TwillTests):
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

#class ExpTag(TwillTests):

class CambridgeTests(TwillTests):
    '''
    The Cambridge milestone says:
    * You can look up what projects (via local cache of sf.net) a person is 
    on.
    '''
    # {{{
    row = ['paulproteus', 'zoph', '1', 'Developer', '2009-06-11 21:53:19']

    def _create_one_flossmole_row_from_data(self):
        # make it
        m, _ = profile.models.Link_SF_Proj_Dude_FM.create_from_flossmole_row_data(
            *self.row)
        return m

    def _create_one_flossmole_row_from_text(self):
        # make it
        m, _ = profile.models.Link_SF_Proj_Dude_FM.create_from_flossmole_row_string(
            '\t'.join(self.row))
        return m

    def _test_import_one_flossmole_row(self):
        # find it
        o = profile.models.Link_SF_Proj_Dude_FM.objects.get(
            person__username='paulproteus', project__unixname='zoph')
        self.assertEqual(o.position, 'Developer')
        self.assert_(o.is_admin)

    def test_import_one_flossmole_row(self):
        self._create_one_flossmole_row_from_data()
        self._test_import_one_flossmole_row()

    def test_import_one_flossmole_row_text(self):
        self._create_one_flossmole_row_from_text()
        self._test_import_one_flossmole_row()

    def _test_sf_person_projects_lookup(self):
        self.test_import_one_flossmole_row()
        url = 'http://openhatch.org/people/sf_projects_by_person?u=paulproteus'
        tc.go(make_twill_url(url))
        tc.find('zoph')

    def test_sf_person_projects_lookup(self):
        self.test_import_one_flossmole_row()
        self._test_sf_person_projects_lookup()

    def test_sf_person_projects_lookup_text(self):
        self.test_import_one_flossmole_row_text()
        self._test_sf_person_projects_lookup()
    # }}}

class PersonTabProjectExpTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def test_project_exp_page_template_displays_project_exp(self):
        # {{{
        url = 'http://openhatch.org/people/paulproteus'
        tc.go(make_twill_url(url))
        tc.find('ccHost')
        # }}}
    # }}}

class ProjectExpTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
            'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def test_projectexp_add(self):
        """Paulproteus can login and add a projectexp."""
        # {{{

        self.login()

        tc.follow('Add project to your portfolio')

        tc.find('Add project to your portfolio')
        tc.fv('projectexp_add', 'project__name', 'bumble')
        tc.fv('projectexp_add', 'project_exp__description', 'fiddlesticks')
        tc.fv('projectexp_add', 'project_exp__url', 'http://example.com')
        tc.submit()
        tc.find('fiddlesticks')
        tc.find('http://example.com')
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

        # Visit login page
        login_url = 'http://openhatch.org/people/login'
        tc.go(make_twill_url(login_url))

        # Log in
        username = "paulproteus"
        password = "paulproteus's unbreakable password"
        tc.fv('login', 'login_username', username)
        tc.fv('login', 'login_password', password)
        tc.submit()

        # Load up the ProjectExp edit page.
        project_name = 'ccHost'
        exp_url = 'http://openhatch.org/people/projects/edit/%s/' % (
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
    def test_info_go_to_edit_mode(self):
        # {{{
        self.login()
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        tc.follow('Edit')
        tc.find('personal_info_edit_mode') # a check-string
        # }}}

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
        url = 'http://openhatch.org/people/edit'
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
        self.login()
        self.update_tags(self.tags)
        # }}}

    def test_tag_edit_twice(self):
        # {{{
        self.login()
        self.update_tags(self.tags)
        self.update_tags(self.tags_2)
        # }}}

    # }}}

class CommitImportTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_poller_appears_correctly(self):
        # {{{
        url = 'http://openhatch.org/people/test_commit_importer'
        url = make_twill_url(url)
        tc.go(url)
        tc.find('test commit importer')
        # }}}

    # }}}

import time
from django.core import management
class CeleryTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']


    def test_slow_loading_via_emulated_bgtask(self, 
            use_cooked_data=True):
        """1. Go to the page that has paulproteus' data.  2. Verify that the page doesn't yet know about ccHost. 3. Run the celery task ourselves, but instead of going to Ohloh, we hand-prepare data for it."""

        url = '/people/test_commit_importer_json'
        
        good_input = {
            'nobgtask': 'yes',
            }
        
        client = Client()
        username='paulproteus'
        password="paulproteus's unbreakable password"
        client.login(username=username,
                     password=password)

        # Ask if background job has been completed.
        # We haven't called it, so the answer should be no.
        response_before = client.get(url, good_input)
        self.assertEquals(
                simplejson.loads(response_before.content),
                [{'success': 0}])

        # Ask if involvement fact has been loaded.
        # We haven't loaded it, so the answer should be no.
        project_name = 'ccHost'
        self.assertFalse(list(ProjectExp.objects.filter(
            project__name=project_name)))

        # do the background load ourselves
        if use_cooked_data:
            cooked_data = [{
                'man_months': 1,
                'project': u'ccHost',
                'project_homepage_url':
                u'http://wiki.creativecommons.org/CcHost',
                'primary_language': u'shell script'}]
        else:
            cooked_data=None

        # Instantiate the task
        # For us, commit_username is also paulproteus.
        # The above cooked_data is a snapshot of 
        # paulproteus's contributions as indexed by Ohloh.
        commit_username=username # = 'paulproteus'

        task = tasks.FetchPersonDataFromOhloh()
        task.run(username=username,
                 commit_username=commit_username,
                 cooked_data=cooked_data)
        # NB: The task knows not to call Ohloh when we give it cooked data.

        self.assert_(Person.objects.get(
            user__username='paulproteus').ohloh_grab_completed)

        # Check again
        response_after = client.get(url, good_input)

        # Ask if background job has been completed. (Hoping for yes.)
        self.assertEquals(simplejson.loads(response_after.content),
                [{'success': 1}])

        # Ask if involvement fact has been loaded. (Hoping for yes.)
        self.assert_(list(ProjectExp.objects.filter(
            project__name=project_name)))

    def test_background_check_if_ohloh_grab_completed(self):
        username='paulproteus'

        tc.go(make_twill_url('http://openhatch.org/people/login'))
        tc.fv('login', 'login_username', username)
        tc.fv('login', 'login_password', "paulproteus's unbreakable password")
        tc.submit()

        url = 'http://openhatch.org/people/ohloh_grab_done'
        tc.go(make_twill_url(url))
        tc.find('False')

        person_obj = Person.objects.get(user__username=username)
        person_obj.ohloh_grab_completed = True
        person_obj.save()

        tc.go(make_twill_url(url))
        tc.find('True')

    def test_bg_loading_marks_grab_completed(self):
        username = 'paulproteus'
        url = 'http://openhatch.org/people/ohloh_grab_done'
        tc.go(make_twill_url(url))
        tc.find('False')

        self.test_slow_loading_via_emulated_bgtask(use_cooked_data=True)

        tc.go(make_twill_url(url))
        tc.find('True')

    # FIXME: One day, test that after self.test_slow_loading_via_emulated_bgtask
    # getting the data does not go out to Ohloh.

# FIXME: One day, stub out the background jobs with mocks
# that ensure we actually call them!
    # }}}

class UserListTests(TwillTests):
    # {{{
    fixtures = [ 'user-paulproteus', 'person-paulproteus',
            'user-barry', 'person-barry']

    def test_display_list_of_users(self):
        people = [(p.user.username, p.user.first_name, p.user.last_name)
                for p in profile.controllers.queryset_of_people()]
        self.assertEqual(people, [
            ('paulproteus', 'Asheesh', 'Laroia'),
            ('barry', 'Barry', 'Spinoza')])

    def test_display_list_of_users_web(self):
        url = 'http://openhatch.org/people/'
        url = make_twill_url(url)
        tc.go(url)
        tc.find(r'Asheesh Laroia \(paulproteus\)')
        tc.find(r'Barry Spinoza \(barry\)')

        tc.follow('Asheesh Laroia')
        tc.url('people/paulproteus') 
        tc.find('paulproteus')

    def test_front_page_link_to_list_of_users(self):
        url = 'http://openhatch.org/'
        url = make_twill_url(url)
        tc.go(url)
        tc.follow('See who else is on OpenHatch')
    # }}}

class AuthTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    
    def test_login(self):
        user = authenticate(username='paulproteus', password="paulproteus's unbreakable password")
        self.assert_(user and user.is_active)

    def test_login_web(self):
        url = 'http://openhatch.org/'
        url = make_twill_url(url)
        tc.go(url)
        tc.fv('login','login_username',"paulproteus")
        tc.fv('login','login_password',"paulproteus's unbreakable password")
        tc.submit()
        tc.find('paulproteus')

    def test_logout_web(self):
        self.test_login_web()
        url = 'http://openhatch.org/search/'
        url = make_twill_url(url)
        tc.go(url)
        tc.follow('Log out')
        tc.find('ciao')

    def test_login_bad_password_web(self):
        url = 'http://openhatch.org/'
        url = make_twill_url(url)
        tc.go(url)
        tc.fv('login','login_username',"paulproteus")
        tc.fv('login','login_password',"not actually paulproteus's unbreakable password")
        tc.submit()
        tc.find("oops")

class SetAPasswordTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus',
            'cchost-data-imported-from-ohloh']
    username = 'ziggy'
    password = "ziggy's impregnable passkey"

    def test_follow_link_from_front_page(self):
        """This test:
        * Creates a new user
        * Verifies that we are at ziggy's profile page"""
        tc.go(make_twill_url('http://openhatch.org/'))
        tc.fv('create_profile', 'create_profile_username', self.username)
        tc.fv('create_profile', 'create_profile_password', self.password)
        tc.submit()
        # Should be at ziggy's profile.
        tc.find(self.username)
        tc.find('profile')

    def test_signup_on_front_page_lets_person_sign_back_in(self):
        ''' The point of this test is to:
        * Create the account for ziggy
        * Log out
        * Log back in as him '''
        self.test_follow_link_from_front_page()
        tc.follow('logout')
        tc.go(make_twill_url('http://openhatch.org/'))
        tc.fv('login', 'login_username', self.username)
        tc.fv('login', 'login_password', self.password)
        tc.submit()
        # Should be back at ziggy's profile
        tc.find(self.username)
        tc.find('profile')
    # }}}

class ImportCommitsViaCommitUsernameViaOhloh(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def submit_commit_name(self, cooked_data_password):
        tc.go(make_twill_url('http://openhatch.org/people/login'))
        tc.fv('login', 'login_username', 'paulproteus')
        tc.fv('login', 'login_password', "paulproteus's unbreakable password")
        tc.submit()

        tc.fv('enter_free_software_username', 'commit_username', 'paulproteus')

        # Since we don't actually want to call Ohloh,
        # we thought to create a mock object, but ran into difficulties.
        # So we're fudging by using pre-cooked data.
        cooked_data = [{'man_months': 1, 'project': u'ccHost',
            'project_homepage_url': u'http://wiki.creativecommons.org/CcHost',
            'primary_language': u'shell script'}]
        # FIXME: Secure this better.
        cooked_data_string = simplejson.dumps(cooked_data)
        tc.config('readonly_controls_writeable', True)
        tc.fv('enter_free_software_username', 'cooked_data', cooked_data_string)
        tc.fv('enter_free_software_username', 
                'cooked_data_password', cooked_data_password)
        tc.submit()
        tc.find('ccHost')

    def test_commit_name_submit_triggers_ohloh_import_via_commit_username(self):
        self.submit_commit_name(settings.cooked_data_password)

    def test_cooked_data_fails_on_bad_password(self):
        self.assertRaises(ValueError, self.submit_commit_name,
                settings.cooked_data_password + '...NOT')
    # }}}
