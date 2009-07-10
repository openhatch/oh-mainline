# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:
# Testing suite for profile

# Imports {{{
from search.models import Project
from profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag
import profile.views
import profile.controllers

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

from django.test.client import Client
from tasks import FetchPersonDataFromOhloh
from django.contrib.auth import authenticate
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

class ProfileTests(django.test.TestCase):
    # {{{
    fixtures = ['user-paulproteus', 'cchost-data-imported-from-ohloh']
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testSlash(self):
        response = self.client.get('/people/')

    def test__add_contribution(self):
        username = 'paulproteus'

        project_name = 'seeseehost'
        description = 'did some work'
        url = 'http://example.com/'
        exp = ProjectExp.create_from_text(username, project_name,
                                    description, url)
        found = list(ProjectExp.objects.filter(person__username=username))
        # Verify it shows up in the DB
        self.assert_('seeseehost' in [f.project.name for f in found])
        # Verify it shows up in profile_data_from_username
        data = profile.views.profile_data_from_username('paulproteus')
        self.assert_(data['person'].username == 'paulproteus')
        projects = [thing[0].project.name for thing in
                    data['exp_taglist_pairs']]
        self.assert_('seeseehost' in projects)
        # Delete it!
        exp.delete()

    def test__add_contribution__web(self):
        # {{{
        url_prefix = "http://openhatch.org"
        username = 'paulproteus'
        #person = Person.objects.get(username=username)
        #first_exp = ProjectExp.objects.filter(person=person)[0]
        url = '%s/people/%s/involvement/add/input' % (
                url_prefix, username)
        tc.go(make_twill_url(url))

        tc.fv('add_contrib', 'project_name', 'Babel')
        tc.fv('add_contrib', 'description', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        tc.find('Babel')

        # Go to old form again
        tc.go(make_twill_url(url))
        tc.fv('add_contrib', 'project_name', 'Baber')
        tc.fv('add_contrib', 'description', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        # Verify that leaving and coming back has it still
        # there
        tc.go(make_twill_url(url_prefix + '/people/paulproteus?tab=inv'))
        tc.find('Babel')
        tc.find('Baber')
        # }}}

    def test__project_exp_create_from_text__unit(self):
        # {{{

        # Create requisite objects
        person = Person.objects.get(username='paulproteus')
        project = Project.objects.get(name='ccHost')

        # Assemble text input
        username = person.username
        project_name = project.name
        description = "sample description"
        url = "http://sample.com"
        man_months = "3"
        primary_language = "perl"

        ProjectExp.create_from_text(
                person.username,
                project.name,
                description,
                url,
                man_months,
                primary_language)
        # }}}

    # }}}

class DebTagsTests(django.test.TestCase):
    # {{{
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

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

class QuebecTests(django.test.TestCase):
    '''
    The Québec milestone says:
    * You can save your profile.
    '''
    # {{{
    fixtures = ['user-paulproteus', 'cchost-data-imported-from-ohloh']
    def setUp(self):
        # {{{
        twill_setup()
        self.to_be_deleted = []
        # }}}

    def tearDown(self):
        # {{{
        twill_teardown()
        for delete_me in self.to_be_deleted:
            delete_me.delete()
        # }}}

    def testPersonModel(self):
        # {{{
        # Test creating a Person and fetching his or her contribution info
        username = 'paulproteus'
        new_person = Person(username=username)
        new_person.save()
        
        new_person.fetch_contrib_data_from_ohloh()
        self.to_be_deleted.append(new_person)
        # Verify that we actually created some ProjectExps related to me
        all_proj_exps = list(
            ProjectExp.objects.filter(person=new_person).all())
        self.to_be_deleted.extend(all_proj_exps)
        self.assert_(all_proj_exps, all_proj_exps)
        # }}}

    def testGetPersonDataDict(self):
        # {{{
        username = 'paulproteus'
        data = profile.views.profile_data_from_username(username,
                                                        fetch_ohloh_data=True)
        self.assertEquals(data['person'].username, username)
        cchost_among_project_exps = False
        for proj, tags in data['exp_taglist_pairs']:
            if proj.project.name == 'ccHost':
                cchost_among_project_exps = True
                break
        self.assert_(cchost_among_project_exps)
        # }}}
    # }}}

#class ExpTag(django.test.TestCase):

class TrentonTests(django.test.TestCase):
    '''
    The Trenton milestone says:
    * You can mark an experience as a favorite.
    '''
    # {{{

    fixtures = ['user-paulproteus']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def test_make_favorite_experience(self):
        # {{{
        return
        # NB: Disabled so we can focus on more important stuff.
        # FIXME: Re-enable.

        url = 'http://openhatch.org/people/paulproteus?tab=inv'

        tc.go(make_twill_url(url))

        # Verify neither is a favorite right now
        tc.notfind('Favorite: TrentonProj1')
        tc.notfind('Favorite: TrentonProj2')

        # Make the last one a favorite
        desired = None
        for form in tc.showforms():
            if 'make-exp-favorite' in form.name:
                desired = form
        assert desired is not None

        # Select that form by "editing" it
        tc.config('readonly_controls_writeable', True)
        tc.fv(desired.name, 'exp_id', desired.get_value('exp_id'))
        tc.submit()

        # Verify that the last one has become a favorite
        tc.notfind('Favorite: TrentonProj1')
        tc.find('Favorite: TrentonProj2')
        # }}}

    def test_make_favorite_tag(self):
        # {{{
        return
        # NB: Disabled so we can focus on more important stuff.
        # FIXME: Re-enable.

        url = 'http://openhatch.org/people/paulproteus?tab=inv'
        # Add an experience
        tc.go(make_twill_url(url))
        tc.fv('add_contrib', 'project_name', 'TrentonProj3')
        tc.fv('add_contrib', 'url', 'http://example.com')
        tc.fv('add_contrib', 'description', 'Totally rad')
        tc.submit()
        tc.find('TrentonProj3')

        # Find its tag submission form
        desired = None
        for form in tc.showforms():
            if 'add-tag-to-exp' in form.name:
                for control in form.controls:
                    if control.name == 'project_name':
                        if control.value == 'TrentonProj3':
                            desired = form
                            break
        assert desired is not None
        
        # Grab experience ID
        exp_id = str(int(desired.find_control('exp_id').value))

        # Give it two tags
        tc.config('readonly_controls_writeable', True)
        tc.fv(desired.name, 'tag_text', 'totally, rad')
        tc.submit()

        # Verify the tags stuck
        tc.find('totally')
        tc.find('rad')

        # Find the tag favoriting form for "rad"
        favorite_tag_forms = [form for form in tc.showforms()
                              if 'favorite-tag-exp' in form.name]
        matching_exp_id_forms = [f for f in favorite_tag_forms
                                 if f.find_control('exp_id').value == exp_id]
        right_tag_text_form = [f for f in matching_exp_id_forms
                               if f.find_control('tag_text').value == 'rad']
        assert len(right_tag_text_form) == 1
        desired = right_tag_text_form[0]

        # Select it and submit
        tc.fv(desired.name, 'exp_id', exp_id)
        tc.submit()

        tc.find('Favorite: rad')
        # }}}
    # }}}

import os
class OhlohIconTests(django.test.TestCase):
    '''Test that we can grab icons from Ohloh.'''
    def test_given_project_find_icon(self):
        import ohloh
        oh = ohloh.get_ohloh()
        icon = oh.get_icon_for_project('f-spot')
        icon_fd = StringIO(icon)
        from PIL import Image
        image = Image.open(icon_fd)
        self.assertEqual(image.size, (64, 64))

    def test_given_project_find_icon_failure(self):
        import ohloh
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'lolnomatxh')

    def test_find_icon_failure_when_proj_exists_but_lacks_icon(self):
        import ohloh
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'asdf')

    def test_find_icon_for_mozilla_firefox(self):
        import ohloh
        oh = ohloh.get_ohloh()
        icon = oh.get_icon_for_project('Mozilla Firefox')
        icon_fd = StringIO(icon)
        from PIL import Image
        image = Image.open(icon_fd)
        self.assertEqual(image.size, (64, 64))

    def test_find_icon_for_proj_with_space(self):
        import ohloh
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'surely nothing is called this name')

    def test_given_project_generate_internal_url(self):
        # First, delete the project icon
        url = profile.views.project_icon_url('f-spot', actually_fetch=False)
        path = url[1:] # strip leading '/'
        if os.path.exists(path):
            os.unlink(path)

        # Download the icon
        url = profile.views.project_icon_url('f-spot')
        self.assert_(os.path.exists(path))
        os.unlink(path)

    def test_given_project_generate_internal_url_for_proj_fail(self):
        # First, delete the project icon
        url = profile.views.project_icon_url('lolnomatzch',
                                             actually_fetch=False)
        path = url[1:] # strip leading '/'
        if os.path.exists(path):
            os.unlink(path)

        # Download the icon
        url = profile.views.project_icon_url('lolnomatzch')
        self.assert_(os.path.exists(path))
        os.unlink(path)


    def test_project_image_link(self):
        # First, delete the project icon
        url = profile.views.project_icon_url('f-spot',
                                             actually_fetch=False)
        path = url[1:] # strip leading '/'
        if os.path.exists(path):
            os.unlink(path)

        # Then retrieve (slowly) this URL that redirects to the image
        go_to_url = '/people/project_icon/f-spot'
        
        response = Client().get(go_to_url)
        # Assure ourselves that we were redirected to the above URL...
        self.assertEqual(response['Location'], 'http://testserver' + url)
        # and that the file exists on disk

        self.assert_(os.path.exists(path))

        # Remove it so the test has no side-effects
        os.unlink(path)

class CambridgeTests(django.test.TestCase):
    '''
    The Cambridge milestone says:
    * You can look up what projects (via local cache of sf.net) a person is on.
    '''
    # {{{
    def setUp(self):
        self.delete_me = []
        self.row = ['paulproteus', 'zoph', '1', 'Developer', '2009-06-11 21:53:19']
                
        twill_setup()

    def tearDown(self):
        for thing in self.delete_me:
            thing.delete()
        twill_teardown()

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

    def _test_import_one_flossmole_row(self, delete_now = True):
        # find it
        o = profile.models.Link_SF_Proj_Dude_FM.objects.get(
            person__username='paulproteus', project__unixname='zoph')
        self.assertEqual(o.position, 'Developer')
        self.assert_(o.is_admin)
        if delete_now:
            o.delete()
        else:
            self.delete_me.append(o)

    def test_import_one_flossmole_row(self, delete_now = True):
        self._create_one_flossmole_row_from_data()
        self._test_import_one_flossmole_row(delete_now = delete_now)

    def test_import_one_flossmole_row_text(self, delete_now = True):
        self._create_one_flossmole_row_from_text()
        self._test_import_one_flossmole_row(delete_now = delete_now)

    def _test_sf_person_projects_lookup(self):
        self.test_import_one_flossmole_row(delete_now=False)
        url = 'http://openhatch.org/people/sf_projects_by_person?u=paulproteus'
        tc.go(make_twill_url(url))
        tc.find('zoph')

    def test_sf_person_projects_lookup(self):
        self.test_import_one_flossmole_row(delete_now=False)
        self._test_sf_person_projects_lookup()
        for thing in self.delete_me:
            thing.delete()
        self.delete_me = []

    def test_sf_person_projects_lookup_text(self):
        self.test_import_one_flossmole_row_text(delete_now=False)
        self._test_sf_person_projects_lookup()
        for thing in self.delete_me:
            thing.delete()
        self.delete_me = []        
    # }}}

class PersonTabProjectExpTests(django.test.TestCase):
    # {{{
    fixtures = ['user-paulproteus', 'cchost-data-imported-from-ohloh']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def test_project_exp_page_template_displays_project_exp(self):
        # {{{
        url = 'http://openhatch.org/people/paulproteus?tab=inv'
        tc.go(make_twill_url(url))
        tc.find('ccHost')
        # }}}
    # }}}

class PersonInvolvementTests(django.test.TestCase):
    # {{{
    fixtures = ['user-paulproteus', 'cchost-data-imported-from-ohloh']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def test_person_involvement_add(self):
        # {{{
        url_prefix = 'http://openhatch.org'
        username = 'paulproteus'
        url = url_prefix + '/people/%s/involvement/add/input' % username
        tc.go(make_twill_url(url))
        tc.find('Add contribution')
        tc.fv('add_contrib', 'project_name', 'bumble')
        tc.fv('add_contrib', 'description', 'fiddlesticks')
        tc.fv('add_contrib', 'url', 'http://example.com')
        tc.submit()
        #tc.follow('involvement')
        tc.find('fiddlesticks')
        tc.find('http://example.com')
        # }}}

    def test_person_involvement_description(self):
        # {{{
        url = 'http://openhatch.org/people/paulproteus/tabs/involvement'
        tc.go(make_twill_url(url))
        tc.find('Month')
        tc.find('Months: 1')
        # }}}

    def test_tag_editor(self):
        # {{{
        tc.follow('tags')
        tc.follow('Edit')
        url = 'http://openhatch.org/people/paulproteus/'
        tc.find('Edit tags')
        # }}}

    def test_tag_editor_save(self):
        # {{{
        url = 'http://openhatch.org/people/paulproteus?tab=tags&edit=1'
        tc.go(make_twill_url(url))
        tags = ['jquery', 'python', 'c++',
                'qwer', 'jkl', 'qergqer', 
                'qe3rga', 'tvauetb', 'aerbgaeg',
                'q40ghqt', 'bgbhgb', '!#%!JG%!',
                'aye', 'bee', 'sea',
                ]
        tc.fv('edit-tags', 'edit-tags-understands', ', '.join(tags[:3]))
        tc.fv('edit-tags', 'edit-tags-understands_not', ', '.join(tags[3:6]))
        tc.fv('edit-tags', 'edit-tags-seeking', ', '.join(tags[6:9]))
        tc.fv('edit-tags', 'edit-tags-studying', ', '.join(tags[9:12]))
        tc.fv('edit-tags', 'edit-tags-can_mentor', ', '.join(tags[12:15]))
        tc.submit()
        self.assert_(list(profile.models.Link_Person_Tag.objects.filter(
            tag__text='jquery', person__username='paulproteus')))
        self.assert_(list(profile.models.Link_Person_Tag.objects.filter(
            tag__text='bgbhgb', person__username='paulproteus')))
        #out = profile.views.tags_dict_for_person(Person.objects.get(
        #    username='paulproteus'))
        for (n, thing) in enumerate(['understands',
                                    'will never understand',
                                    'looking for volunteering opportunities in',
                                    'currently learning about',
                                    'can mentor in']):
            tc.find(thing + '.*'
                    + ".*".join(map(re.escape, tags[n*3:(n+1)*3])))

        # Go back to the form and make sure some of these are there
        tc.go(make_twill_url(url))
        tc.find('aye')
        # }}}

    # }}}

class CommitImportTests(django.test.TestCase):
    # {{{
    fixtures = ['user-paulproteus']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()
    def test_poller_appears_correctly(self):
        # {{{
        url = 'http://openhatch.org/people/paulproteus/test_commit_importer'
        url = make_twill_url(url)
        tc.go(url)
        tc.find('test commit importer')
        # }}}

    # }}}

import time
from django.core import management
class CeleryTests(django.test.TestCase):
    fixtures = ['user-paulproteus']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def test_slow_loading_via_emulated_bgtask(self,
                                              use_cooked_data=True):
        """
        1. Go to the page that has paulproteus' data.
        2. Verify that the page doesn't yet know about ccHost
        3. Run the celery task ourselves, but instead of going to Ohloh, we hand-prepare data for it.
        """
        username='paulproteus'
        url = '/people/paulproteus/test_commit_importer_json'
        
        good_input = {
            'nobgtask': 'yes',
            }
        
        # Ask if background job has been completed.
        # We haven't called it, so the answer should be no.
        response_before = Client().get(url, good_input)
        self.assertEquals(simplejson.loads(response_before.content),
                [{'success': 0}])

        # Ask if involvement fact has been loaded.
        # We haven't loaded it, so the answer should be no.
        project_name = 'ccHost'
        self.assertFalse(list(ProjectExp.objects.filter(
            project__name=project_name)))

        # do the background load ourselves
        if use_cooked_data:
            cooked_data = [{'man_months': 1, 'project': u'ccHost',
            'project_homepage_url': u'http://wiki.creativecommons.org/CcHost',
            'primary_language': u'shell script'}]
        else:
            cooked_data=None

        # Instantiate the task
        task = FetchPersonDataFromOhloh()
        task.run(username, cooked_data=cooked_data)
        # NB: The task knows not to call Ohloh when we give it cooked data.

        self.assert_(Person.objects.get(username='paulproteus').ohloh_grab_completed)

        # Check again
        response_after = Client().get(url, good_input)

        # Ask if background job has been completed. (Hoping for yes.)
        self.assertEquals(simplejson.loads(response_after.content),
                [{'success': 1}])

        # Ask if involvement fact has been loaded. (Hoping for yes.)
        self.assert_(list(ProjectExp.objects.filter(
            project__name=project_name)))

    def test_background_check_if_ohloh_grab_completed(self):
        username = 'paulproteus'
        url = 'http://openhatch.org/people/%s/ohloh_grab_done' % urllib.quote(
            username)
        tc.go(make_twill_url(url))
        tc.find('False')

        person_obj = Person.objects.get(username=username)
        person_obj.ohloh_grab_completed = True
        person_obj.save()

        tc.go(make_twill_url(url))
        tc.find('True')

    def test_bg_loading_marks_grab_completed(self):
        username = 'paulproteus'
        url = 'http://openhatch.org/people/%s/ohloh_grab_done' % urllib.quote(
            username)
        tc.go(make_twill_url(url))
        tc.find('False')

        self.test_slow_loading_via_emulated_bgtask(use_cooked_data=True)

        tc.go(make_twill_url(url))
        tc.find('True')

    # FIXME: One day, test that after self.test_slow_loading_via_emulated_bgtask
    # getting the data does not go out to Ohloh.

# FIXME: One day, stub out the background jobs with mocks
# that ensure we actually call them!

class UserListTests(django.test.TestCase):
    fixtures = ['user-paulproteus', 'user-steve']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()
    
    def test_display_list_of_users(self):
        people = [(p.username, p.name)
                for p in profile.controllers.queryset_of_people()]
        self.assertEqual(people, [
            ('paulproteus', 'Asheesh Laroia'),
            ('steve', 'Steve Stevey')])

    def test_display_list_of_users_web(self):
        url = 'http://openhatch.org/people/'
        url = make_twill_url(url)
        tc.go(url)
        tc.find(r'Asheesh Laroia \(paulproteus\)')
        tc.find(r'Steve Stevey \(steve\)')

        tc.follow('Asheesh Laroia')
        tc.url('people/paulproteus') 
        tc.find('paulproteus')

    def test_front_page_link_to_list_of_users(self):
        url = 'http://openhatch.org/'
        url = make_twill_url(url)
        tc.go(url)
        tc.follow('See who else is on OpenHatch')

class AuthTests(django.test.TestCase):
    fixtures = ['user-paulproteus', 'auth-user-paulproteus']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()
    
    def test_login(self):
        user = authenticate(username='paulproteus', password="paulproteus's unbreakable password")
        self.assert_(user and user.is_active)

    def test_login_web(self):
        url = 'http://openhatch.org/'
        url = make_twill_url(url)
        tc.go(url)
        tc.fv('login','login-username',"paulproteus")
        tc.fv('login','login-password',"paulproteus's unbreakable password")
        tc.submit()
        tc.find('logged in')

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
        tc.fv('login','login-username',"paulproteus")
        tc.fv('login','login-password',"not actually paulproteus's unbreakable password")
        tc.submit()
        tc.find("oops")

class SetAPasswordTests(django.test.TestCase):
    # FIXME: I suppose the fixture should be called person-paulproteus
    fixtures = ['user-paulproteus', 'cchost-data-imported-from-ohloh']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def test_profile_links_to_signup(self):
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus'))
        tc.follow("Sign up to save your work")
        tc.find("Password: ")

    def test_signup_submission_creates_user(self):
        tc.go(make_twill_url('http://openhatch.org/people/signup'))
        tc.fv('signup', 'login-username', 'paulproteus')
        tc.fv('signup', 'login-password', "paulproteus's unbreakable password")
        tc.submit()
        tc.find("Log out")
