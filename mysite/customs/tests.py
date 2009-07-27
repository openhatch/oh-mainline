# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:

# Imports {{{
from search.models import Project
from profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag
import profile.views

import mock
import os
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
import ohloh
import lp_grabber

from django.test.client import Client
from profile.tasks import FetchPersonDataFromOhloh
# }}}

# Mocked out browser.open
open_causes_404 = mock.Mock()
def generate_404(self):
    import urllib2
    raise urllib2.HTTPError('', 404, {}, {}, None)
open_causes_404.side_effect = generate_404


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

class SlowlohTests(django.test.TestCase):
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
        project_name = 'ccHost'
        analysis_id = oh.get_latest_project_analysis_id(project_name);
        self.assertEqual(project_name, oh.analysis2projectdata(analysis_id)['name'])
        # }}}

    def testFindByUsername(self, should_equal = None):
        # {{{
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_username('paulproteus')
        if should_equal is None:
            should_equal = [{'project': u'ccHost',
                             'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                             'man_months': 1,
                             'primary_language': 'shell script'}]

        self.assertEqual(projects, should_equal)
        # }}}

    @mock.patch('mechanize.Browser.open', open_causes_404)
    def testFindByUsernameWith404(self):
        # {{{
        self.testFindByUsername([])
        # }}}

    def testFindByOhlohUsername(self, should_equal = None):
        # {{{
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_ohloh_username('paulproteus')
        if should_equal is None:
            should_equal = [{'project': u'ccHost',
                             'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                           'man_months': 1,
                             'primary_language': 'shell script'}]
        self.assertEqual(should_equal, projects)
        # }}}

    @mock.patch('mechanize.Browser.open', open_causes_404)
    def testFindByOhlohUsernameWith404(self):
        # {{{
        self.testFindByOhlohUsername([])
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

class QuebecTests(django.test.TestCase):
    '''
    The Québec milestone says:
    * You can save your profile.
    '''
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus', 'cchost-data-imported-from-ohloh']
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
        new_person = Person.objects.get(user__username=username)
        new_person.save()
        
        new_person.fetch_contrib_data_from_ohloh()
        self.to_be_deleted.append(new_person)
        # Verify that we actually created some ProjectExps related to me
        all_proj_exps = list(
            ProjectExp.objects.filter(person=new_person).all())
        self.to_be_deleted.extend(all_proj_exps)
        self.assert_(all_proj_exps, all_proj_exps)
        # }}}

    # }}}

class OhlohIconTests(django.test.TestCase):
    '''Test that we can grab icons from Ohloh.'''
    # {{{
    def test_given_project_find_icon(self):
        oh = ohloh.get_ohloh()
        icon = oh.get_icon_for_project('f-spot')
        icon_fd = StringIO(icon)
        from PIL import Image
        image = Image.open(icon_fd)
        self.assertEqual(image.size, (64, 64))

    def test_given_project_find_icon_failure(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'lolnomatxh')

    def test_find_icon_failure_when_proj_exists_but_lacks_icon(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'asdf')

    def test_find_icon_for_mozilla_firefox(self):
        oh = ohloh.get_ohloh()
        icon = oh.get_icon_for_project('Mozilla Firefox')
        icon_fd = StringIO(icon)
        from PIL import Image
        image = Image.open(icon_fd)
        self.assertEqual(image.size, (64, 64))

    def test_find_icon_for_proj_with_space(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project,
                'surely nothing is called this name')

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
    # }}}

class LaunchpadDataTests(django.test.TestCase):
    def test_project2language(self):
        langs = lp_grabber.project2languages('gwibber')
        self.assertEqual(langs, ['Python'])

        # The project, lazr, is registered on Launchpad, but doesn't
        # have a language assigned to it.
        no_langs = lp_grabber.project2languages('lazr')
        self.assertEqual(no_langs, [])

    def test_greg_has_branch_for_gwibber(self):
        info = lp_grabber.get_info_for_launchpad_username(
            'greg.grossmeier')
        self.assertEqual(info['Gwibber']['involvement_types'],
                         set(['Bazaar Branches', 'Bug Management']))
        self.assertEqual(info['Gwibber']['url'],
                         'https://launchpad.net/gwibber')
        return info

    def test_greg_has_python_involvement(self):
        langs = lp_grabber.person_to_bazaar_branch_languages('greg.grossmeier')
        self.assertEqual(langs, ['Python'])

