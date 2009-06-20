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

    def tearDown(self):
        twill_teardown()

    def testSlash(self):
        response = self.client.get('/people/')

    def testAddContribution(self):
        # {{{
        url = 'http://openhatch.org/people/'
        tc.go(make_twill_url(url))
        tc.fv('add_contrib', 'project', 'Babel')
        tc.fv('add_contrib', 'contrib_text', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        # Assert that we are not in some weird GET place with
        # CGI args
        tc.url(r'^[^?]*$')

        tc.find('Babel')
        tc.fv('add_contrib', 'project', 'Baber')
        tc.fv('add_contrib', 'contrib_text', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        # Verify that leaving and coming back has it still
        # there
        tc.go(make_twill_url(url))
        tc.find('Babel')
        tc.find('Baber')
        # }}}
    # }}}

class OmanTests(django.test.TestCase):
    # {{{
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testFormEnterYourUsername(self):
        # {{{
        url = 'http://openhatch.org/people/'
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
        url = 'http://openhatch.org/people/'
        tc.go(make_twill_url(url))
        tc.fv('enter_free_software_email', 'email', 'asheesh@asheesh.org')
        tc.submit()

        tc.find('ccHost')
    # }}}

class DebTagsTests(django.test.TestCase):
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testAddOneDebtag(self):
        profile.views.add_one_debtag_to_project('alpine', 'implemented-in::c')
        self.assertEqual(profile.views.list_debtags_of_project('alpine'),
                         ['implemented-in::c'])
    

class QuebecTests(django.test.TestCase):
    '''
    The Québec milestone says:
    * You can save your profile.
    '''
    # {{{
    def setUp(self):
        twill_setup()
        self.to_be_deleted = []

    def tearDown(self):
        twill_teardown()
        # FIXME: delete the paulproteus person
        # and all related ProjectExps

    def testPersonModel(self):
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

    def testGetPersonDataDict(self):
        username = 'paulproteus'
        data = profile.views.get_data_dict_for_display_person(username)
        self.assertEquals(data['person'].username, username)
        cchost_among_project_exps = False
        for exp in data['project_exps']:
            if exp.project.name == 'ccHost':
                cchost_among_project_exps = True
                break
        self.assert_(cchost_among_project_exps)
    # }}}

class SomervilleTests(django.test.TestCase):
    '''
    The Somerville milestone says:
    * You can add tags to annotate each code experience
    '''
    # {{{
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testNewLink_ProjectExp_Tag(self):
        # {{{
        stipe = Person(name='Michael Stipe', username='stipe')
        language = TagType(name='language', prefix='lang')
        python = Tag(text='python', tag_type=language)
        exaile = Project(name='exaile')
        project_exp = ProjectExp(person=stipe, project=exaile)
        proj_exp_tag = Link_ProjectExp_Tag(
                project_exp=project_exp,
                tag=python,
                source="test")
        # }}}

    def testAddTagToProjectExp(self):
        # {{{
        person, person_created = Person.objects.get_or_create(
                username='stipe')
        if person_created: print "Person %s was created" % person

        project, project_created = Project.objects.get_or_create(
                name='murmur')
        if project_created: print "Project %s was created" % project

        project_exp, proj_exp_created = ProjectExp.objects.get_or_create(
                person=person, project=project)
        if proj_exp_created: print "ProjectExp %s was created" % project_exp

        profile.views.add_tag_to_project_exp("stipe", "murmur", "awesome")
        # }}}

    def testAddTagToProjectExpWithoutFunction(self):
        # {{{

        tag_type, created = TagType.objects.get_or_create(name='misc')
        if created: print "tag type %s was created" % tag_type

        tag, tag_created = Tag.objects.get_or_create(
                text='exemplary futility',
                tag_type=tag_type)
        if tag_created: print "tag %s was created" % tag

        person, person_created = Person.objects.get_or_create(
                username='stipe')
        if person_created: print "person %s was created" % person

        project, project_created = Project.objects.get_or_create(
                name='exaile')
        if project_created: print "project %s was created" % project

        project_exp, project_exp_created = ProjectExp.objects.get_or_create(
                person=person, project=project)
        if project_exp_created: print "project_exp %s was created" % project_exp

        link, link_created = Link_ProjectExp_Tag.objects.get_or_create(
                tag=tag, project_exp=project_exp)
        if link_created: print "link %s was created" % link

        # }}}

    def testAddTagFailsOnBadInput(self):
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

    def testAddTagWorks(self):
        # {{{
        url = '/people/add_tag_to_project_exp'

        username = 'stipe'
        project_name = 'automatic'
        tag_text = 'baller'

        person, person_created = Person.objects.get_or_create(
                username=username)
        project, project_created = Project.objects.get_or_create(
                name=project_name)
        exp, exp_created = ProjectExp.objects.get_or_create(
                person=person, project=project)

        good_input = {
            'username': username,
            'project_name': project_name,
            'tag_text': tag_text
            }

        client = Client()

        self.assertContains(client.get(url, good_input), username)
        self.assertContains(client.get(url, good_input), project_name)
        self.assertContains(client.get(url, good_input), tag_text)
        # }}}

    # }}}
