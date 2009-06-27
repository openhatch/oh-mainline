# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:
# Testing suite for profile

# Imports {{{
from search.models import Project
from profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag
import profile.views

import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
import django.test
from django.test import TestCase
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler
from StringIO import StringIO

from django.test.client import Client
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
    def setUp(self):
        twill_setup()
        self.sample_person = Person(username='stipe')
        self.sample_person.save()
        self.sample_project = Project(name='automatic')
        self.sample_project.save()

    def tearDown(self):
        twill_teardown()
        self.sample_person.delete()
        self.sample_project.delete()

    def testSlash(self):
        response = self.client.get('/people/')

    def test__add_contribution(self):
        username = 'paulproteus'
        url = 'http://openhatch.org/people/%s' % username
        tc.go(make_twill_url(url))

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
        username = 'paulproteus'
        url = 'http://openhatch.org/people/%s?tab=inv' % username
        tc.go(make_twill_url(url))
        tc.fv('add_contrib', 'project_name', 'Babel')
        tc.fv('add_contrib', 'description', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        tc.find('Babel')

        # Go to old form again
        url = 'http://openhatch.org/people/?u=%s&tab=inv' % username
        tc.go(make_twill_url(url))
        tc.fv('add_contrib', 'project_name', 'Baber')
        tc.fv('add_contrib', 'description', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        # Verify that leaving and coming back has it still
        # there
        tc.go(make_twill_url(url))
        tc.find('Babel')
        tc.find('Baber')
        # }}}

    def test__project_exp_create_from_text__unit(self):
        # {{{

        # Create requisite objects
        person = self.sample_person
        project = self.sample_project

        # Assemble text input
        username = person.username
        project_name = project.name
        description = "sample description"
        url = "http://sample.com"
        man_months = "3"
        primary_language = "brainfuck"

        ProjectExp.create_from_text(
                person.username,
                project.name,
                description,
                url,
                man_months,
                primary_language)
        # }}}

    # }}}

class OmanTests(django.test.TestCase):
    # {{{
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def test_slurper_accepts_username(self):
        # {{{
        url = 'http://openhatch.org/people/exp_scraper'
        tc.go(make_twill_url(url))
        tc.fv('enter_free_software_username', 'u', 'paulproteus')
        tc.submit()

        tc.find('ccHost')
        # }}}
    # }}}

import ohloh
class OhlohTests(django.test.TestCase):
    # {{{
    def testProjectDataById(self):
        # {{{
        oh = ohloh.get_ohloh()
        data = oh.project_id2projectdata(15329)
        self.assertEqual('ccHost', data['name'])
        self.assertEqual('http://wiki.creativecommons.org/CcHost',
                         data['homepage_url'])
        # }}}
        
    def testProjectNameByAnalysisId(self):
        # {{{
        oh = ohloh.get_ohloh()
        self.assertEqual('ccHost', oh.analysis2projectdata(603185)['name'])
        # }}}

    def testFindByUsername(self):
        # {{{
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_username('paulproteus')
        self.assertEqual([{'project': u'ccHost',
                           'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                           'man_months': 1,
                           'primary_language': 'shell script'}],
                         projects)
        # }}}

    def testFindByOhlohUsername(self):
        # {{{
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_ohloh_username('paulproteus')
        self.assertEqual([{'project': u'ccHost',
                           'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                           'man_months': 1,
                           'primary_language': 'shell script'}],
                         projects)
        # }}}

    def testFindByEmail(self): 
        # {{{
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_email('asheesh@asheesh.org')
        assert {'project': u'playerpiano',
                'project_homepage_url': 'http://code.google.com/p/playerpiano',
                'man_months': 1,
                'primary_language': 'Python'} in projects
        # }}}

    def testFindContributionsInOhlohAccountByUsername(self):
        # {{{
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_ohloh_username('paulproteus')
        
        assert {'project': u'ccHost',
                'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                'man_months': 1,
                'primary_language': 'shell script'} in projects
        # }}}


    def testFindContributionsInOhlohAccountByEmail(self):
        oh = ohloh.get_ohloh()
        username = oh.email_address_to_ohloh_username('paulproteus.ohloh@asheesh.org')
        projects = oh.get_contribution_info_by_ohloh_username(username)
        
        assert {'project': u'ccHost',
                'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                'man_months': 1,
                'primary_language': 'shell script'} in projects


    def testFindUsernameByEmail(self):
        # {{{
        oh = ohloh.get_ohloh()
        username = oh.email_address_to_ohloh_username('paulproteus.ohloh@asheesh.org')
        self.assertEquals(username, 'paulproteus')
        # }}}

    def testFindByUsernameNotAsheesh(self):
        # {{{
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_username('keescook')
        self.assert_(len(projects) > 1)
        # }}}
    # }}}

class PerthTests(django.test.TestCase):
    '''
    The Perth milestone says:
    * The web form needs to be able to search by email also.
    '''
    # {{{
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testFormEnterYourEmail(self):
        url = 'http://openhatch.org/people/xp_slurp'
        tc.go(make_twill_url(url))
        tc.fv('enter_free_software_email', 'email', 'paulproteus.ohloh@asheesh.org')
        tc.submit()
        tc.follow('involvement')
        tc.find('ccHost')

    def testFormDoesntBlowUpForNoMatch(self):
        url = 'http://openhatch.org/people/xp_slurp'
        tc.go(make_twill_url(url))
        tc.fv('enter_free_software_email', 'email', 'asheesh@asheesh.org')
        tc.submit()
        tc.follow('involvement')
        tc.find('playerpiano')
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

class ExpTag(django.test.TestCase):
    # {{{
    def setUp(self):
        twill_setup()
        self.sample_person = Person(username='stipe')
        self.sample_person.save()

        self.sample_project = Project(name='automatic')
        self.sample_project.save()

        self.sample_tag_type = TagType(name='asdf')
        self.sample_tag_type.save()

        self.sample_tag = Tag(tag_type=self.sample_tag_type, text='baller')
        self.sample_tag.save()

        self.sample_exp = ProjectExp(
                person=self.sample_person,
                project=self.sample_project)
        self.sample_exp.save()

    def tearDown(self):
        twill_teardown()
        self.sample_person.delete()
        self.sample_project.delete()
        self.sample_tag.delete()
        self.sample_exp.delete()
        self.sample_tag_type.delete()

    def test__exp_tag_model_create_and_delete(self):
        # {{{

        tag_type, created = TagType.objects.get_or_create(name='misc')

        tag, tag_created = Tag.objects.get_or_create(
                text='exemplary futility',
                tag_type=tag_type)

        person, person_created = Person.objects.get_or_create(
                username='stipe')

        project, project_created = Project.objects.get_or_create(
                name='exaile')

        project_exp, project_exp_created = ProjectExp.objects.get_or_create(
                person=person, project=project)

        link_exp_tag, link_created = Link_ProjectExp_Tag.objects.get_or_create(
                tag=tag, project_exp=project_exp)
        self.assert_(link_created)

        link_exp_tag.delete()
        # }}}

    def test__exp_tag_add__unit(self, return_it = False):
        # {{{
        # Constants:
        project_name='murmur'
        username='stipe'
        tag_text='awesome'
    
        person, person_created = Person.objects.get_or_create(
                username=username)
        #if person_created: print "Person %s was created" % person

        project, project_created = Project.objects.get_or_create(
                name=project_name)
        #if project_created: print "Project %s was created" % project

        project_exp, proj_exp_created = ProjectExp.objects.get_or_create(
                person=person, project=project)
        #if proj_exp_created: print "ProjectExp %s was created" % project_exp

        profile.views.add_tag_to_project_exp(username, project_name, tag_text)
        # Verify it worked
        inserted = Link_ProjectExp_Tag.objects.get(tag__text='awesome')
        self.assertEqual(inserted.project_exp.project, project)
        self.assertEqual(inserted.tag.text, tag_text)
        self.assertEqual(inserted.project_exp.person, person)
        self.assert_(inserted.id) # make sure it got in there
        if return_it:
            return inserted
        else:
            inserted.delete()
        # }}}

    def test__exp_tag_remove__unit(self):
        tag_link = self.test__exp_tag_add__unit(return_it = True)
        returned = profile.views.project_exp_tag__remove(
            tag_link.project_exp.person.username,
            tag_link.project_exp.project.name,
            tag_link.tag.text)

        try:
            profile.views.project_exp_tag__remove(
            tag_link.project_exp.person.username,
            tag_link.project_exp.project.name,
            tag_link.tag.text)
            assert False, "Should have NOT found it"
        except Link_ProjectExp_Tag.DoesNotExist:
            pass # w00t

    def test__exp_tag_add__web(self, username='stipe',
                               project_name='automatic',
                               tag_text='baller'):
        # {{{
        # Do it twice: note that it doesn't fail
        for k in range(2):
            url = '/people/add_tag_to_project_exp'
            
            good_input = {
                'username': username,
                'project_name': project_name,
                'tag_text': tag_text
                }
            
            response = Client().post(url, good_input)
            response = Client().get('/people/', {'u': username})
            
            self.assertContains(response, username)
            self.assertContains(response, project_name)
            self.assertContains(response, tag_text)

        # }}}

    def test__project_exp_tag__remove__web(self):
        # {{{
        tag_text='ballew'
        username = 'stipe'
        project_name = 'automatic'
        
        self.test__exp_tag_add__web(tag_text=tag_text,
                                    username=username,
                                    project_name=project_name)

        url = 'http://openhatch.org/people/?u=' + username
        tc.go(make_twill_url(url))
        
        # FIXME: Loop over forms
        tc.fv('add-tag-to-exp', 'tag_text', tag_text)
        tc.submit()
        tc.find(tag_text)

        # All this so we can click the right Delete button
        desired = None
        for form in tc.showforms():
            if 'remove-tag' in form.name:
                desired = form
        tc.config('readonly_controls_writeable', True)
        self.assertEqual(desired.get_value('tag_text'), tag_text)
        tc.fv(desired.name, 'tag_text', desired.get_value('tag_text'))
        tc.submit()
        tc.notfind(tag_text)
        
        # }}}

    def test__project_exp_tag_add__web__failure(self):
        # {{{
        url = '/people/add_tag_to_project_exp'

        username = 'stipe'
        project_name = 'automatic'

        Person.objects.get_or_create(username=username)
        Project.objects.get_or_create(name=project_name)

        good_input = {
            'username': username,
            'project_name': project_name,
            'tag_text': 'baller'
            }

        client = Client()

        # Test that add tag fails if any of the fields are missing.
        for key in good_input.keys():
            bad_input = {}
            bad_input.update(good_input)
            del bad_input[key]
            self.assertEquals(client.get(url, bad_input).status_code, 500)
        # }}}

    def test__project_exp_tag_remove__web__failure(self):
        # {{{
        url = '/people/project_exp_tag__remove'

        username = 'stipe'
        project_name = 'automatic'

        Person.objects.get_or_create(username=username)
        Project.objects.get_or_create(name=project_name)

        good_input = {
            'username': username,
            'project_name': project_name,
            'tag_text': 'baller'
            }

        client = Client()

        # Test that add tag fails if any of the fields are missing.
        for key in good_input.keys():
            bad_input = {}
            bad_input.update(good_input)
            del bad_input[key]
            self.assert_('error' in
                         client.get(url, bad_input)['Location'])
        # }}}

    def test__exp_tag_add_multiple_tags__web(self):
        tag_text = 'rofl, con, hipster'
        desired_tags = ['rofl', 'con', 'hipster']
        username='stipe'
        project_name='automatic'
        
        url = '/people/add_tag_to_project_exp'
        
        good_input = {
            'username': username,
            'project_name': project_name,
            'tag_text': tag_text
            }
        
        response = Client().post(url, good_input)
        response = Client().get('/people/', {'u': username})
        
        self.assertContains(response, username)
        self.assertContains(response, project_name)
        self.assertNotContains(response, tag_text) # the thing
                                                   # withspaces will
                                                   # not fly
        for tag in desired_tags: # but each tag alone, that's splendid
            self.assertContains(response, tag)


    """
    test that tag dupes aren't added, and that a notification is returned 'you tried to add a duplicate tag: %s'.
    do that for each dupe, and return a summary notification: 'you tried to add the following duplicate tags: ...'
    """

    # }}}

class UnadillaTests(django.test.TestCase):
    """
    The Unadilla milestone says:
    * You can write what you're interested in working on
    """
    # {{{
    fixtures = ['user-paulproteus']
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testEnterWhatYouLikeWorkingOn(self):
        # {{{
        url = 'http://openhatch.org/people/?u=paulproteus&tab=tags'
        tc.go(make_twill_url(url))
        tc.fv('what_you_like_working_on', 'like-working-on', 'barbies')
        tc.fv('what_you_like_working_on', 'username', 'paulproteus')
        tc.submit()
        tc.find('barbies')
        
        tc.fv('what_you_like_working_on', 'like-working-on', 'barbiequeue')
        tc.submit()
        tc.find('barbiequeue')
        # }}}

    # }}}

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

class AnchorageTests(django.test.TestCase):
    # {{{

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def test_xp_slurper_input_form(self):
        url = 'http://openhatch.org/people/xp_slurp'
        tc.go(make_twill_url(url))
        # FIXME: Check the actual template instead of
        # using a check string.
        tc.find("[xp_slurper]")

    def test_xp_slurper_fails_without_username(self):
        # If no username entered, user is returned
        # to scraper input form with a notification.
        url = 'http://openhatch.org/people/xp_slurp_do'
        tc.go(make_twill_url(url))
        tc.find("Please enter a username.")
    # }}}

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
