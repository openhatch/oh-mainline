# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:

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
from profile.tasks import FetchPersonDataFromOhloh
# }}}

import ohloh
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
