# -*- coding: utf-8 -*-
from __future__ import absolute_import
# vim: set ai et ts=4 sw=4:

# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
# Copyright (C) 2010 Karen Rustad
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2010 Mark Freeman
# Copyright (C) 2012 Berry Phillips
# Copyright (C) 2012 John Morrissey
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


# Imports {{{
from mysite.base.tests import TwillTests
from mysite.search.models import Bug, Project
from mysite.base.models import Timestamp
from mysite.profile.models import Person, Tag, TagType, Link_Person_Tag
import mysite.profile.views
from mysite.customs import ohloh
import mysite.customs.views
import mysite.base.depends

from django.core.urlresolvers import reverse

import logging
import mock
import os
import time
import twill
import urlparse

import django.test
import django.contrib.auth.models
import django.core.serializers
from django.conf import settings
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler

from StringIO import StringIO
from urllib2 import HTTPError
import datetime
from dateutil.tz import tzutc

import twisted.internet.defer

import mysite.customs.profile_importers
import mysite.customs.cia
import mysite.customs.feed

from django.utils.unittest import skipIf

import mysite.customs.models
import mysite.customs.management.commands.customs_daily_tasks
import mysite.customs.management.commands.customs_twist
import mysite.customs.management.commands.snapshot_public_data
from mysite.customs.data_transits import bug_data_transit, trac_data_transit


# We don't want the tests to depend on the optional bugimporters libarary.
try:
    from bugimporters.bugzilla import (BugzillaBugImporter, BugzillaBugParser,
            KDEBugzilla)
    from bugimporters.roundup import RoundupBugImporter, RoundupBugParser
    from bugimporters.google import GoogleBugImporter, GoogleBugParser
    from bugimporters.trac import TracBugImporter, TracBugParser
    from bugimporters.launchpad import LaunchpadBugImporter
    from bugimporters.github import GitHubBugImporter, GitHubBugParser
    import bugimporters.bugzilla # to make mock.patch() happy
except ImportError:
    BugzillaBugImporter = None
    BugzillaBugParser = None
    RoundupBugImporter = None
    RoundupBugParser = None
    TracBugImporter = None
    TracBugParser = None
    LaunchpadBugImporter = None
    GoogleBugImporter = None
    GoogleBugParser = None
    GitHubBugImporter = None
    GitHubBugParser = None
# }}}

importer_data_transits = {'bug': bug_data_transit, 'trac': trac_data_transit}


class FakeGetPage(object):
    '''In this function, we define the fake URLs we know about, and where
    the saved data is.'''
    def __init__(self):
        self.url2data = {}
        self.url2data['http://qa.debian.org/developer.php?login=asheesh%40asheesh.org'] = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'debianqa-asheesh.html')).read()
        self.url2data['http://github.com/api/v2/json/repos/show/paulproteus'] = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'github', 'json-repos-show-paulproteus.json')).read()
        self.url2data['http://github.com/paulproteus.json'] = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'github', 'paulproteus-personal-feed.json')).read()
        self.url2data['https://api.launchpad.net/1.0/people?ws.op=find&text=asheesh%40asheesh.org'] = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'people__ws.op=find&text=asheesh@asheesh.org')).read()
        self.url2data['https://launchpad.net/~paulproteus'] = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'launchpad', '~paulproteus')).read()
        self.url2data['https://launchpad.net/~Mozilla'] = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'launchpad', '~Mozilla')).read()
        self.url2data['http://api.bitbucket.org/1.0/users/paulproteus/'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'bitbucket', 'paulproteus.json')).read()
        self.url2data['http://www.ohloh.net/contributors.xml?query=paulproteus&api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', 'contributors.xml__query=paulproteus&api_key=JeXHeaQhjXewhdktn4nUw')).read()
        self.url2data['https://www.ohloh.net/accounts/paulproteus'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', 'paulproteus')).read()
        self.url2data['https://www.ohloh.net/p/debian/contributors/18318035536880.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '18318035536880.xml')).read()
        self.url2data['https://www.ohloh.net/p/cchost/contributors/65837553699824.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '65837553699824.xml')).read()
        self.url2data['https://www.ohloh.net/accounts/44c4e8d8ef5137fd8bcd78f9cee164ef'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '44c4e8d8ef5137fd8bcd78f9cee164ef')).read()
        self.url2data['http://www.ohloh.net/analyses/1454281.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '1454281.xml')).read()
        self.url2data['http://www.ohloh.net/analyses/1143684.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '1143684.xml')).read()
        self.url2data['http://www.ohloh.net/projects/15329.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '15329.xml')).read()
        self.url2data['http://www.ohloh.net/projects/479665.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '479665.xml')).read()
        self.url2data['https://www.ohloh.net/p/cchost/contributors/65837553699824'] = ''
        self.url2data['https://www.ohloh.net/p/ccsearch-/contributors/2060147635589231'] = ''
        self.url2data['https://www.ohloh.net/p/debian'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', 'debian')).read()
        self.url2data['https://www.ohloh.net/p/cchost'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', 'cchost')).read()
        self.url2data['https://www.ohloh.net/p/15329/contributors/65837553699824.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '65837553699824.xml')).read()
        self.url2data['https://www.ohloh.net/p/4265/contributors/18318035536880.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '18318035536880.xml')).read()
        self.url2data['http://www.ohloh.net/projects/4265.xml?api_key=JeXHeaQhjXewhdktn4nUw'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '4265.xml')).read()
        self.url2data['https://www.ohloh.net/p/debian/contributors/18318035536880'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'ohloh', '18318035536880')).read()
        self.url2data['https://api.launchpad.net/1.0/bugs/839461'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_839461')).read()
        self.url2data['https://api.launchpad.net/1.0/bugs/839461/subscriptions'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_839461_subscriptions')).read()
        self.url2data['https://api.launchpad.net/1.0/~vila'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', '~vila')).read()
        self.url2data['https://api.launchpad.net/1.0/bzr/+bug/839461'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_task_839461')).read()
        self.url2data['https://api.launchpad.net/1.0/bzr/+bug/839461closed'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_task_839461closed')).read()
        self.url2data['https://api.launchpad.net/1.0/bzr/+bug/839461doc'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_task_839461doc')).read()
        self.url2data['https://api.launchpad.net/1.0/bugs/839461doc'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_839461doc')).read()
        self.url2data['https://api.launchpad.net/1.0/bzr/+bug/839461bite'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_task_839461bite')).read()
        self.url2data['https://api.launchpad.net/1.0/bugs/839461bite'] = open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'launchpad', 'bugs_839461bite')).read()
        self.url2data['http://github.com/api/v2/json/issues/list/openhatch/misc/open']= open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'github', 'issue-list')).read()
        self.url2data['http://github.com/api/v2/json/issues/list/openhatch/misc/closed']= open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'github', 'issue-list-closed')).read()
        self.url2data['http://github.com/api/v2/json/issues/show/openhatch/misc/42']= open(os.path.join(settings.MEDIA_ROOT, 'sample-data', 'github', 'issue-show')).read()

    """This is a fake version of Twisted.web's getPage() function.
    It returns a Deferred that is already 'fired', and has the page content
    passed into it already.

    It never adds the Deferred to the 'reactor', so calling reactor.start()
    should be a no-op."""
    def getPage(self, url):
        assert type(url) == str
        d = twisted.internet.defer.Deferred()
        d.callback(self.url2data[url])
        return d

    """This is a fake version of Twisted.web's getPage() function.
    It returns a Deferred that is already 'fired', and has been passed a
    Failure containing an HTTP 404 Error.

    It never adds the Deferred to the 'reactor', so calling reactor.start()
    should be a no-op."""
    def get404(self, url):
        d = twisted.internet.defer.Deferred()
        d.errback(
                twisted.python.failure.Failure(
                    twisted.web.error.Error(
                        404, 'File Not Found', None)))
        return d

# Create a module-level global that is the fake getPage
fakeGetPage = FakeGetPage()

# Mocked out browser.open
open_causes_404 = mock.Mock()
def generate_404(self):
    import urllib2
    raise urllib2.HTTPError('', 404, {}, {}, None)
open_causes_404.side_effect = generate_404

def generate_403(self):
    import urllib2
    raise urllib2.HTTPError('', 403, {}, {}, None)

def generate_408(self):
    import urllib2
    raise urllib2.HTTPError('', 408, {}, {}, None)

def generate_504(self):
    import urllib2
    raise urllib2.HTTPError('', 504, {}, {}, None)

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

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class OhlohIconTests(django.test.TestCase):
    '''Test that we can grab icons from Ohloh.'''
    # {{{

    @skipIf(not mysite.base.depends.Image, "Skipping photo-related tests because PIL is missing. Look in ADVANCED_INSTALLATION.mkd for information.")
    def test_ohloh_gives_us_an_icon(self):
        oh = ohloh.get_ohloh()
        icon = oh.get_icon_for_project('f-spot')
        icon_fd = StringIO(icon)
        image = mysite.base.depends.Image.open(icon_fd)
        self.assertEqual(image.size, (64, 64))

    def test_ohloh_errors_on_nonexistent_project(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'lolnomatxh')

    def test_ohloh_errors_on_project_lacking_icon(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'asdf')

    def test_ohloh_errors_correctly_even_when_we_send_her_spaces(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project,
                'surely nothing is called this name')

    def test_populate_icon_from_ohloh(self):

        project = Project()
        project.name = 'Mozilla Firefox'
        project.populate_icon_from_ohloh()

        self.assert_(project.icon_raw)
        self.assertEqual(project.icon_raw.width, 64)
        self.assertNotEqual(project.date_icon_was_fetched_from_ohloh, None)

    def test_populate_icon_from_ohloh_uses_none_on_no_match(self):

        project = Project()
        project.name = 'lolnomatchiawergh'

        project.populate_icon_from_ohloh()

        self.assertFalse(project.icon_raw)
        # We don't know how to compare this against None,
        # but this seems to work.

        self.assertNotEqual(project.date_icon_was_fetched_from_ohloh, None)

    # }}}

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class ImportFromDebianQA(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    def test_asheesh_unit(self, do_nothing, do_nothing_also):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        dia = mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='db', query='asheesh@asheesh.org')

        # Create the DebianQA to track the state.
        dqa = mysite.customs.profile_importers.DebianQA(query=dia.query, dia_id=dia.id, command=None)

        # Check that we generate the right URL
        urlsAndCallbacks = dqa.getUrlsAndCallbacks()
        just_one, = urlsAndCallbacks
        url = just_one['url']
        callback = just_one['callback']
        self.assertEqual('http://qa.debian.org/developer.php?login=asheesh%40asheesh.org', url)
        self.assertEqual(callback, dqa.handlePageContents)

        # Check that we make Citations as expected
        page_contents = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'debianqa-asheesh.html')).read()
        dqa.handlePageContents(page_contents)

        projects = set([c.portfolio_entry.project.name for c in mysite.profile.models.Citation.objects.all()])
        self.assertEqual(projects, set(['ccd2iso', 'liblicense', 'exempi', 'Debian GNU/Linux', 'cue2toc', 'alpine']))

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def test_asheesh_integration(self, do_nothing, do_nothing_also):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        dia = mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='db', query='asheesh@asheesh.org')
        cmd = mysite.customs.management.commands.customs_twist.Command()
        cmd.handle(use_reactor=False)

        # And now, the dia should be completed.
        dia = mysite.profile.models.DataImportAttempt.objects.get(person=asheesh, source='db', query='asheesh@asheesh.org')
        self.assertTrue(dia.completed)

        # And Asheesh should have some new projects available.
        projects = set([c.portfolio_entry.project.name for c in mysite.profile.models.Citation.objects.all()])
        self.assertEqual(projects, set(['ccd2iso', 'liblicense', 'exempi', 'Debian GNU/Linux', 'cue2toc', 'alpine']))

    def test_404(self):
        pass # uhhh

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install oh-bugimporters. See ADVANCED_INSTALLATION.mkd for more.")
class LaunchpadProfileImport(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    def test_asheesh_unit(self, do_nothing, do_nothing_also):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        dia = mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='lp', query='asheesh@asheesh.org')

        # Create the LPPS to track the state.
        lpps = mysite.customs.profile_importers.LaunchpadProfilePageScraper(
            query=dia.query, dia_id=dia.id, command=None)

        # Check that we generate the right URL
        urlsAndCallbacks = lpps.getUrlsAndCallbacks()
        just_one, = urlsAndCallbacks
        url = just_one['url']
        callback = just_one['callback']
        self.assertEqual(url, 'https://api.launchpad.net/1.0/people?ws.op=find&text=asheesh%40asheesh.org')
        self.assertEqual(callback, lpps.parseAndProcessUserSearch)

    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    def test_email_address_to_username_discovery(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        dia = mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='lp', query='asheesh@asheesh.org')

        # setUp() already created the DataImportAttempt
        # so we just run the command:
        cmd = mysite.customs.management.commands.customs_twist.Command()
        cmd.handle(use_reactor=False)

        # And now, the dia should be completed.
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia.id)
        self.assertTrue(dia.completed)

        # And Asheesh should have some new projects available.
        projects = set([c.portfolio_entry.project.name for c in mysite.profile.models.Citation.objects.all()])
        self.assertEqual(projects,
                         set([u'Web Team projects', u'Debian GNU/Linux', u'lxml', u'Buildout', u'Ubuntu']))

    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    def test_mozilla_group_page_crash(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        dia = mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='lp', query='Mozilla')

        # setUp() already created the DataImportAttempt
        # so we just run the command:
        cmd = mysite.customs.management.commands.customs_twist.Command()
        cmd.handle(use_reactor=False)

        # And now, the dia should be completed.
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=dia.id)
        self.assertTrue(dia.completed)

        # And Asheesh should have no new projects available.
        self.assertFalse(mysite.profile.models.Citation.objects.all())

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class ImportFromBitbucket(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def setUp(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='bb', query='paulproteus')

        # With the DIA in place, we run the command and simulate
        # going out to Twisted.
        mysite.customs.management.commands.customs_twist.Command(
            ).handle(use_reactor=False)

        # Extract the citation objects so tests can easily refer to them.
        self.bayberry_data = mysite.profile.models.Citation.objects.get(
            portfolio_entry__project__name='bayberry-data')
        self.long_kwallet_thing = mysite.profile.models.Citation.objects.get(
            portfolio_entry__project__name='fix-crash-in-kwallet-handling-code')
        self.python_keyring_lib = mysite.profile.models.Citation.objects.get(
            portfolio_entry__project__name='python-keyring-lib')

    def test_create_three(self):
        self.assertEqual(
            3,
            mysite.profile.models.PortfolioEntry.objects.all().count())

    def test_contributor_role(self):
        # Check that the proper Citation objects were created.
        self.assertEqual(
            'Contributed to a repository on Bitbucket.',
            self.bayberry_data.contributor_role)

    def test_project_urls(self):
        # Verify that we generate URLs correctly, using the slug.
        self.assertEqual(
            'http://bitbucket.org/paulproteus/bayberry-data/',
            self.bayberry_data.url)
        self.assertEqual(
            'http://bitbucket.org/paulproteus/fix-crash-in-kwallet-handling-code/',
            self.long_kwallet_thing.url)

    def test_citation_descriptions(self):
        # This comes from the 'description'
        self.assertEqual(
            "Training data for an anti wiki spam corpus.",
            self.bayberry_data.portfolio_entry.project_description)
        # This comes from the 'slug' because there is no description
        self.assertEqual(
            "Fix crash in kwallet handling code",
            self.long_kwallet_thing.portfolio_entry.project_description)

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class TestAbstractOhlohAccountImporter(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def setUp(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        self.dia = mysite.profile.models.DataImportAttempt.objects.create(
            person=asheesh, source='rs', query='paulproteus')

        self.aoai = mysite.customs.profile_importers.AbstractOhlohAccountImporter(
            query=self.dia.query, dia_id=self.dia.id, command=None)

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def test_generate_url(self, do_nothing, do_nothing_1):
        params = {u'query': unicode(self.dia.query)}
        expected_query_items = sorted(
            {u'api_key': u'key',
             u'query': unicode(self.dia.query)}.items())

        url = self.aoai.url_for_ohloh_query(
            url=u'http://example.com/',
            params=params,
            API_KEY='key')
        base, rest = url.split('?', 1)
        self.assertEquals('http://example.com/', base)
        self.assertEquals(expected_query_items,
                          sorted(urlparse.parse_qsl(rest)))

        url = self.aoai.url_for_ohloh_query(
            url='http://example.com/?',
            params=params,
            API_KEY='key')
        base, rest = url.split('?', 1)
        self.assertEquals('http://example.com/', base)
        self.assertEquals(expected_query_items,
                          sorted(urlparse.parse_qsl(rest)))

    def test_parse_ohloh_invalid_xml(self):
        # No exception on invalid XML
        parsed = self.aoai.parse_ohloh_xml('''<broken''')
        self.assert_(parsed is None)

    def test_parse_ohloh_error_xml(self):
        # returns None if the XML is an Ohloh error
        parsed = self.aoai.parse_ohloh_xml('''<response><error /></response>''')
        self.assert_(parsed is None)

    def test_parse_ohloh_valid_xml(self):
        # returns some True value if there is a document
        parsed = self.aoai.parse_ohloh_xml('''<something></something>''')
        self.assertTrue(parsed)

    def test_xml_tag_to_dict(self):
        parsed = self.aoai.parse_ohloh_xml('''<response>
        <wrapper><key>value</key></wrapper>
        </response>''')
        self.assertTrue(parsed)

        as_dict_list = self.aoai.filter_ohloh_xml(
            parsed, selector='/wrapper', many=True)
        self.assertEquals([{'key': 'value'}],
                          as_dict_list)

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def test_filter_fake_matches(self, do_nothing, do_nothing_1):
        c_fs = [
        # One real match
            {
                'project': 'project_name',
                'contributor_name': 'paulproteus',
                'man_months': 3,
                'primary_language': 'Python',
                'permalink': 'http://example.com/',
                'analysis_id': 17, # dummy
                },
            # One irrelevant match
            {
                'project': 'project_name_2',
                'contributor_name': 'paulproteuss',
                'man_months': 3,
                'primary_language': 'Python',
                'permalink': 'http://example.com/',
                'analysis_id': 1717, # dummy
                }
            ]


        output = self.aoai.filter_out_irrelevant_ohloh_dicts(c_fs)
        self.assertEqual(1, len(output))
        self.assertEqual(17, output[0]['analysis_id'])

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class TestOhlohRepositorySearch(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def setUp(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        self.dia = mysite.profile.models.DataImportAttempt.objects.create(
            person=asheesh, source='rs', query='paulproteus')

        self.aoai = mysite.customs.profile_importers.RepositorySearchOhlohImporter(
            query=self.dia.query, dia_id=self.dia.id, command=None)

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def test_integration(self, ignore, ignore_2):
        # setUp() already created the DataImportAttempt
        # so we just run the command:
        cmd = mysite.customs.management.commands.customs_twist.Command()
        cmd.handle(use_reactor=False)

        # And now, the dia should be completed.
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=self.dia.id)
        self.assertTrue(dia.completed)

        # And Asheesh should have some new projects available.
        # FIXME: This should use the project name, not just the lame
        # current Ohloh analysis ID.
        projects = set([c.portfolio_entry.project.name for c in mysite.profile.models.Citation.objects.all()])
        self.assertEqual(projects,
                         set([u'Creative Commons search engine', u'ccHost']))

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class TestOhlohAccountImport(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def setUp(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        self.dia = mysite.profile.models.DataImportAttempt.objects.create(
            person=asheesh, source='oh', query='paulproteus')

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def test_integration(self, ignore, ignore_2):
        # setUp() already created the DataImportAttempt
        # so we just run the command:
        cmd = mysite.customs.management.commands.customs_twist.Command()
        cmd.handle(use_reactor=False)

        # And now, the dia should be completed.
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=self.dia.id)
        self.assertTrue(dia.completed)

        # And Asheesh should have some new projects available.
        # FIXME: This should use the project name, not just the lame
        # current Ohloh analysis ID.
        projects = set([c.portfolio_entry.project.name for c in mysite.profile.models.Citation.objects.all()])
        self.assertEqual(set(['Debian GNU/Linux', 'ccHost']),
                         projects)

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class TestOhlohAccountImportWithEmailAddress(TestOhlohAccountImport):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def setUp(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        self.dia = mysite.profile.models.DataImportAttempt.objects.create(
            person=asheesh, source='oh', query='paulproteus.ohloh@asheesh.org')


@skipIf(BugzillaBugImporter is None, "To run these tests, you must install oh-bugimporters. See ADVANCED_INSTALLATION.mkd for more.")
class TestCustomBugParser(django.test.TestCase):
    ### First, test that if we create the bug importer correctly, the
    ### right thing would happen.
    def test_bugzilla_bug_importer_uses_bugzilla_parser_by_default(self):
        bbi = BugzillaBugImporter(
            tracker_model=None, reactor_manager=None,
            bug_parser=None)
        self.assertEqual(bbi.bug_parser, BugzillaBugParser)

    def test_bugzilla_bug_importer_accepts_bug_parser(self):
        bbi = BugzillaBugImporter(
            tracker_model=None, reactor_manager=None,
            bug_parser=KDEBugzilla)
        self.assertEqual(bbi.bug_parser, KDEBugzilla)

    def test_kdebugparser_uses_tracker_specific_method(self):
        with mock.patch('bugimporters.bugzilla.KDEBugzilla.extract_tracker_specific_data') as mock_specific:
            bugzilla_data = mysite.base.depends.lxml.etree.XML(open(os.path.join(
                        settings.MEDIA_ROOT, 'sample-data', 'kde-117760-2010-04-09.xml')).read())
            bug_data = bugzilla_data.xpath('bug')[0]

            kdebugzilla = bugimporters.bugzilla.KDEBugzilla(bug_data)
            kdebugzilla.get_parsed_data_dict(base_url='http://bugs.kde.org/',
                                             bitesized_type=None,
                                             bitesized_text='',
                                             documentation_type=None,
                                             documentation_text='')
            self.assertTrue(mock_specific.called)

    ### Now, test that the customs_twist class will create an importer
    ### configured to use the right class.
    def test_customs_twist_creates_importers_correctly(self):
        tm = mysite.customs.models.BugzillaTrackerModel.all_trackers.create(
                tracker_name='KDE Bugzilla',
                base_url='http://bugs.kde.org/',
                bug_project_name_format='{tracker_name}',
                bitesized_type='key',
                bitesized_text='bitesized',
                documentation_type='key',
                custom_parser='bugzilla.KDEBugzilla',
                )
        twister = mysite.customs.management.commands.customs_twist.Command()
        importer = twister._get_importer_instance_for_tracker_model(tm)
        self.assertEqual(KDEBugzilla,
                         importer.bug_parser)

    ### Now, test that the customs_twist class will create an importer
    ### configured to use the right class.
    def test_customs_twist_creates_importers_correctly_for_none(self):
        twister = mysite.customs.management.commands.customs_twist.Command()
        importer = twister._get_importer_instance_for_tracker_model(None)
        self.assertTrue(importer)

@skipIf(True, "This should move to oh-bugimporters, and should be presumed to be broken at the moment.")
class BugzillaBugImporterTests(django.test.TestCase):
    fixtures = ['miro-project']
    def setUp(self):
        # Set up the BugzillaTrackerModels that will be used here.
        self.tm = mysite.customs.models.BugzillaTrackerModel.all_trackers.create(
                tracker_name='Miro',
                base_url='http://bugzilla.pculture.org/',
                bug_project_name_format='{tracker_name}',
                bitesized_type='key',
                bitesized_text='bitesized',
                documentation_type='key',
                )
        self.im = BugzillaBugImporter(self.tm, None, data_transits=importer_data_transits)

    def test_miro_bug_object(self):
        # Check the number of Bugs present.
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 0)

        # Parse XML document as if we got it from the web
        self.im.handle_bug_xml(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.project.name, 'Miro')
        self.assertEqual(bug.title, "Add test for torrents that use gzip'd urls")
        self.assertEqual(bug.description, """This broke. We should make sure it doesn't break again.
Trac ticket id: 2294
Owner: wguaraldi
Reporter: nassar
Keywords: Torrent unittest""")
        self.assertEqual(bug.status, 'NEW')
        self.assertEqual(bug.importance, 'normal')
        self.assertEqual(bug.people_involved, 5)
        self.assertEqual(bug.date_reported, datetime.datetime(2006, 6, 9, 12, 49))
        self.assertEqual(bug.last_touched, datetime.datetime(2008, 6, 11, 23, 56, 27))
        self.assertEqual(bug.submitter_username, 'nassar@pculture.org')
        self.assertEqual(bug.submitter_realname, 'Nick Nassar')
        self.assertEqual(bug.canonical_bug_link, 'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.good_for_newcomers)

    def test_full_grab_miro_bugs(self):
        # Check the number of Bugs present.
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 0)

        # Parse XML document as if we got it from the web
        self.im.handle_bug_xml(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assertFalse(bug.looks_closed)

        # And the new manager does find it
        self.assertEqual(Bug.open_ones.all().count(), 1)


    def test_miro_bugzilla_detects_closedness(self):
        # Check the number of Bugs present.
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 0)

        # Parse XML document as if we got it from the web
        self.im.handle_bug_xml(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data',
            'miro-2294-2009-08-06.xml')).read().replace(
            'NEW', 'CLOSED'))

        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

        # And the new manager successfully does NOT find it!
        self.assertEqual(Bug.open_ones.all().count(), 0)

    def test_full_grab_resolved_miro_bug(self):
        # Check the number of Bugs present.
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 0)

        # Parse XML document as if we got it from the web
        self.im.handle_bug_xml(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06-RESOLVED.xml')).read())

        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

    def test_full_grab_miro_bugs_refreshes_older_bugs(self):
        # Check the number of Bugs present.
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 0)

        # Parse XML document as if we got it from the web
        self.im.handle_bug_xml(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        # Pretend there's old data lying around:
        bug = Bug.all_bugs.get()
        bug.people_involved = 1
        bug.last_polled = datetime.datetime.now() - datetime.timedelta(days = 2)
        bug.save()

        # Now refresh.
        self.im.handle_bug_xml(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        # Now verify there is only one bug, and its people_involved is 5
        bug = Bug.all_bugs.get()
        self.assertEqual(bug.people_involved, 5)

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class BlogCrawl(django.test.TestCase):
    def test_summary2html(self):
        yo_eacute = mysite.customs.feed.summary2html('Yo &eacute;')
        self.assertEqual(yo_eacute, u'Yo \xe9')

    @mock.patch("feedparser.parse")
    def test_blog_entries(self, mock_feedparser_parse):
        mock_feedparser_parse.return_value = {
            'entries': [
                {
                    'title': 'Yo &eacute;',
                    'summary': 'Yo &eacute;'
                    }]}
        entries = mysite.customs.feed._blog_entries()
        self.assertEqual(entries[0]['title'],
                         u'Yo \xe9')
        self.assertEqual(entries[0]['unicode_text'],
                         u'Yo \xe9')

def raise_504(*args, **kwargs):
    raise HTTPError(url="http://theurl.com/", code=504, msg="", hdrs="", fp=open("/dev/null"))
mock_browser_open = mock.Mock()
mock_browser_open.side_effect = raise_504
@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class UserGetsMessagesDuringImport(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch("mechanize.Browser.open", mock_browser_open)
    def test_user_get_messages_during_import(self):
        paulproteus = Person.objects.get(user__username='paulproteus')

        self.assertEqual(len(paulproteus.user.get_and_delete_messages()), 0)

        self.assertRaises(HTTPError, mysite.customs.mechanize_helpers.mechanize_get, 'http://ohloh.net/somewebsiteonohloh', attempts_remaining=1, person=paulproteus)

        self.assertEqual(len(paulproteus.user.get_and_delete_messages()), 1)

@skipIf(RoundupBugImporter is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class RoundupBugImporterTests(django.test.TestCase):
    def setUp(self):
        # Set up the RoundupTrackerModel that will be used here.
        self.tm = mysite.customs.models.RoundupTrackerModel.all_trackers.create(
                tracker_name='Mercurial',
                base_url='http://mercurial.selenic.com/bts/',
                closed_status='resolved',
                bitesized_field='Topics',
                bitesized_text='bitesized',
                documentation_field='Topics',
                documentation_text='documentation',
                )
        self.im = RoundupBugImporter(self.tm, None, data_transits=importer_data_transits)

    def test_get_url_does_not_crash(self):
        self.assertTrue(self.tm.get_edit_url())


sample_launchpad_data_snapshot = mock.Mock()
sample_launchpad_data_snapshot.return_value = [dict(
        url=u'', project=u'rose.makesad.us', text=u'', status=u'',
        importance=u'low', reporter={u'lplogin': 'a',
                                    'realname': 'b'},
        tags=[], comments=[], date_updated=time.localtime(),
        date_reported=time.localtime(),
        title="Joi's Lab AFS",)]

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class ParseCiaMessage(django.test.TestCase):
    def test_with_ansi_codes(self):
        message = '\x02XBMC:\x0f \x0303jmarshallnz\x0f * r\x0226531\x0f \x0310\x0f/trunk/guilib/ (GUIWindow.h GUIWindow.cpp)\x02:\x0f cleanup: eliminate some duplicate code.'
        parsed = {'project_name': 'XBMC',
                  'committer_identifier': 'jmarshallnz',
                  'version': 'r26531',
                  'path': '/trunk/guilib/ (GUIWindow.h GUIWindow.cpp)',
                  'message': 'cleanup: eliminate some duplicate code.'}
        self.assertEqual(mysite.customs.cia.parse_ansi_cia_message(message),
                         parsed)

    def test_parse_a_middle_line(self):
        message = "\x02FreeBSD:\x0f Replace several instances of 'if (!a & b)' with 'if (!(a &b))' in order"
        parsed = {'project_name': 'FreeBSD',
                  'message': "Replace several instances of 'if (!a & b)' with 'if (!(a &b))' in order"}
        self.assertEqual(mysite.customs.cia.parse_ansi_cia_message(message),
                         parsed)

    def test_parse_a_middle_line_with_asterisk(self):
        message = "\x02FreeBSD:\x0f * Replace several instances of 'if (!a & b)' with 'if (!(a &b))' in order"
        parsed = {'project_name': 'FreeBSD',
                  'message': "* Replace several instances of 'if (!a & b)' with 'if (!(a &b))' in order"}
        self.assertEqual(mysite.customs.cia.parse_ansi_cia_message(message),
                         parsed)

    def test_find_module(self):
        tokens = ['KDE:', ' crissi', ' ', '*', ' r', '1071733', ' kvpnc', '/trunk/playground/network/kvpnc/ (6 files in 2 dirs)', ':', ' ']
        expected = {'project_name': 'KDE',
                    'committer_identifier': 'crissi',
                    'version': 'r1071733',
                    'path': '/trunk/playground/network/kvpnc/ (6 files in 2 dirs)',
                    'module': 'kvpnc',
                    'message': ''}
        self.assertEqual(mysite.customs.cia.parse_cia_tokens(tokens),
                         expected)

    def test_complicated_mercurial_version(self):
        tokens = ['Sphinx:', ' birkenfeld', ' ', '*', ' ', '88e880fe9101', ' r', '1756', ' ', '/EXAMPLES', ':', ' Regroup examples list by theme used.']
        expected = {'project_name': 'Sphinx',
                    'committer_identifier': 'birkenfeld',
                    'version': '88e880fe9101 r1756',
                    'path': '/EXAMPLES',
                    'message': 'Regroup examples list by theme used.'}
        self.assertEqual(mysite.customs.cia.parse_cia_tokens(tokens),
                         expected)

    def test_find_module_with_no_version(self):
        tokens = ['FreeBSD:', ' glarkin', ' ', '*', ' ports', '/lang/gcc42/ (Makefile distinfo files/patch-contrib__download_ecj)', ':', ' (log message trimmed)']
        expected = {'project_name': 'FreeBSD',
                    'committer_identifier': 'glarkin',
                    'path': '/lang/gcc42/ (Makefile distinfo files/patch-contrib__download_ecj)',
                    'module': 'ports',
                    'message':  '(log message trimmed)'}
        self.assertEqual(mysite.customs.cia.parse_cia_tokens(tokens),
                         expected)

    def test_find_module_in_moin(self):
        tokens = ['moin:', ' Thomas Waldmann <tw AT waldmann-edv DOT de>', ' default', ' ', '*', ' ', '5405:a1a1ce8894cb', ' 1.9', '/MoinMoin/util/SubProcess.py', ':', ' merged moin/1.8']
        expected = {'project_name': 'moin',
                    'committer_identifier': 'Thomas Waldmann <tw AT waldmann-edv DOT de>',
                    'branch': 'default',
                    'version': '5405:a1a1ce8894cb',
                    'module': '1.9',
                    'path': '/MoinMoin/util/SubProcess.py',
                    'message':  'merged moin/1.8'}
        self.assertEqual(mysite.customs.cia.parse_cia_tokens(tokens),
                         expected)


@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class LineAcceptorTest(django.test.TestCase):
    def test(self):

        got_response = []
        def callback(obj, got_response=got_response):
            got_response.append(obj)

        lines = [
            '\x02FreeBSD:\x0f \x0303trasz\x0f * r\x02201794\x0f \x0310\x0f/head/sys/ (4 files in 4 dirs)\x02:\x0f ',
            "\x02FreeBSD:\x0f Replace several instances of 'if (!a & b)' with 'if (!(a &b))' in order",
            '\x02FreeBSD:\x0f to silence newer GCC versions.',
            '\x02KDE:\x0f \x0303lueck\x0f * r\x021071711\x0f \x0310\x0f/branches/work/doc/kget/\x02:\x0f kget doc was moved back to trunk',
            '\x02SHR:\x0f \x0303mok\x0f \x0307libphone-ui-shr\x0f * r\x027cad6cdc76f9\x0f \x0310\x0f/po/ru.po\x02:\x0f po: updated russian translation from Vladimir Berezenko']
        agent = mysite.customs.cia.LineAcceptingAgent(callback)

        expecting_response = None
        # expecting no full message for the first THREE lines
        agent.handle_message(lines[0])
        self.assertFalse(got_response)

        agent.handle_message(lines[1])
        self.assertFalse(got_response)

        agent.handle_message(lines[2])
        self.assertFalse(got_response)

        # but now we expect something!
        agent.handle_message(lines[3])
        wanted = {'project_name': 'FreeBSD', 'path': '/head/sys/ (4 files in 4 dirs)', 'message': "Replace several instances of 'if (!a & b)' with 'if (!(a &b))' in order\nto silence newer GCC versions.", 'committer_identifier': 'trasz', 'version': 'r201794'}
        got = got_response[0]
        self.assertEqual(got, wanted)
        got_response[:] = []

        # FIXME use (project_name, version) pair instead I guess

        # and again, but differently
        agent.handle_message(lines[4])
        wanted = {'project_name': 'KDE', 'path': '/branches/work/doc/kget/', 'message': "kget doc was moved back to trunk", 'committer_identifier': 'lueck', 'version': 'r1071711'}
        self.assertEqual(got_response[0], wanted)
        got_response[:] = []

def do_list_of_work(l):
    '''Some helper methods in mysite.customs.management.commands.customs_daily_tasks
       return a list of worker functions to call. This wrapper simply executes all
       the elements of l, assuming they are callables.'''
    for thing in l:
        thing()

@skipIf(GoogleBugImporter is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class GoogleBugImport(django.test.TestCase):
    def setUp(self):
        # Set up the Twisted TrackerModels that will be used here.
        self.tm = mysite.customs.models.GoogleTrackerModel.all_trackers.create(
                tracker_name='SymPy',
                google_name='sympy',
                bitesized_type='label',
                bitesized_text='EasyToFix',
                documentation_type='label',
                documentation_text='Documentation')

    def test_create_google_data_dict_with_everything(self):
        atom_dict = {
                'id': {'text': 'http://code.google.com/feeds/issues/p/sympy/issues/full/1215'},
                'published': {'text': '2008-11-24T11:15:58.000Z'},
                'updated': {'text': '2009-12-06T23:01:11.000Z'},
                'title': {'text': 'fix html documentation'},
                'content': {'text': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module"""},
                'author': {'name': {'text': 'fabian.seoane'}},
                'cc': [
                    {'username': {'text': 'asmeurer'}}
                    ],
                'owner': {'username': {'text': 'Vinzent.Steinberg'}},
                'label': [
                    {'text': 'Type-Defect'},
                    {'text': 'Priority-Critical'},
                    {'text': 'Documentation'},
                    {'text': 'Milestone-Release0.6.6'}
                    ],
                'state': {'text': 'closed'},
                'status': {'text': 'Fixed'}
                }
        bug_atom = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        gbp = GoogleBugParser(
                bug_url='http://code.google.com/p/sympy/issues/detail?id=1215')
        gbp.bug_atom = bug_atom

        got = gbp.get_parsed_data_dict(self.tm)
        wanted = {'title': 'fix html documentation',
                  'description': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module""",
                  'status': 'Fixed',
                  'importance': 'Critical',
                  'people_involved': 3,
                  'date_reported': datetime.datetime(2008, 11, 24, 11, 15, 58),
                  'last_touched': datetime.datetime(2009, 12, 06, 23, 01, 11),
                  'looks_closed': True,
                  'submitter_username': 'fabian.seoane',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://code.google.com/p/sympy/issues/detail?id=1215',
                  'good_for_newcomers': False,
                  'concerns_just_documentation': True,
                  '_project_name': 'SymPy',
                  }
        self.assertEqual(wanted, got)

    def test_create_google_data_dict_author_in_list(self):
        atom_dict = {
                'id': {'text': 'http://code.google.com/feeds/issues/p/sympy/issues/full/1215'},
                'published': {'text': '2008-11-24T11:15:58.000Z'},
                'updated': {'text': '2009-12-06T23:01:11.000Z'},
                'title': {'text': 'fix html documentation'},
                'content': {'text': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module"""},
                'author': [{'name': {'text': 'fabian.seoane'}}],
                'cc': [
                    {'username': {'text': 'asmeurer'}}
                    ],
                'owner': {'username': {'text': 'Vinzent.Steinberg'}},
                'label': [
                    {'text': 'Type-Defect'},
                    {'text': 'Priority-Critical'},
                    {'text': 'Documentation'},
                    {'text': 'Milestone-Release0.6.6'}
                    ],
                'state': {'text': 'closed'},
                'status': {'text': 'Fixed'}
                }
        bug_atom = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        gbp = GoogleBugParser(
                bug_url='http://code.google.com/p/sympy/issues/detail?id=1215')
        gbp.bug_atom = bug_atom

        got = gbp.get_parsed_data_dict(self.tm)
        wanted = {'title': 'fix html documentation',
                  'description': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module""",
                  'status': 'Fixed',
                  'importance': 'Critical',
                  'people_involved': 3,
                  'date_reported': datetime.datetime(2008, 11, 24, 11, 15, 58),
                  'last_touched': datetime.datetime(2009, 12, 06, 23, 01, 11),
                  'looks_closed': True,
                  'submitter_username': 'fabian.seoane',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://code.google.com/p/sympy/issues/detail?id=1215',
                  'good_for_newcomers': False,
                  'concerns_just_documentation': True,
                  '_project_name': 'SymPy',
                  }
        self.assertEqual(wanted, got)

    def test_create_google_data_dict_owner_in_list(self):
        atom_dict = {
                'id': {'text': 'http://code.google.com/feeds/issues/p/sympy/issues/full/1215'},
                'published': {'text': '2008-11-24T11:15:58.000Z'},
                'updated': {'text': '2009-12-06T23:01:11.000Z'},
                'title': {'text': 'fix html documentation'},
                'content': {'text': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module"""},
                'author': {'name': {'text': 'fabian.seoane'}},
                'cc': [
                    {'username': {'text': 'asmeurer'}}
                    ],
                'owner': [{'username': {'text': 'Vinzent.Steinberg'}}],
                'label': [
                    {'text': 'Type-Defect'},
                    {'text': 'Priority-Critical'},
                    {'text': 'Documentation'},
                    {'text': 'Milestone-Release0.6.6'}
                    ],
                'state': {'text': 'closed'},
                'status': {'text': 'Fixed'}
                }
        bug_atom = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        gbp = GoogleBugParser(
                bug_url='http://code.google.com/p/sympy/issues/detail?id=1215')
        gbp.bug_atom = bug_atom

        got = gbp.get_parsed_data_dict(self.tm)
        wanted = {'title': 'fix html documentation',
                  'description': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module""",
                  'status': 'Fixed',
                  'importance': 'Critical',
                  'people_involved': 3,
                  'date_reported': datetime.datetime(2008, 11, 24, 11, 15, 58),
                  'last_touched': datetime.datetime(2009, 12, 06, 23, 01, 11),
                  'looks_closed': True,
                  'submitter_username': 'fabian.seoane',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://code.google.com/p/sympy/issues/detail?id=1215',
                  'good_for_newcomers': False,
                  'concerns_just_documentation': True,
                  '_project_name': 'SymPy',
                  }
        self.assertEqual(wanted, got)

    def test_create_google_data_dict_without_status(self):
        atom_dict = {
                'id': {'text': 'http://code.google.com/feeds/issues/p/sympy/issues/full/1215'},
                'published': {'text': '2008-11-24T11:15:58.000Z'},
                'updated': {'text': '2009-12-06T23:01:11.000Z'},
                'title': {'text': 'fix html documentation'},
                'content': {'text': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module"""},
                'author': {'name': {'text': 'fabian.seoane'}},
                'cc': [
                    {'username': {'text': 'asmeurer'}}
                    ],
                'owner': {'username': {'text': 'Vinzent.Steinberg'}},
                'label': [
                    {'text': 'Type-Defect'},
                    {'text': 'Priority-Critical'},
                    {'text': 'Documentation'},
                    {'text': 'Milestone-Release0.6.6'}
                    ],
                'state': {'text': 'closed'},
                'status': None
                }
        bug_atom = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        gbp = GoogleBugParser(
                bug_url='http://code.google.com/p/sympy/issues/detail?id=1215')
        gbp.bug_atom = bug_atom

        got = gbp.get_parsed_data_dict(self.tm)
        wanted = {'title': 'fix html documentation',
                  'description': """http://docs.sympy.org/modindex.html

I don't see for example the solvers module""",
                  'status': '',
                  'importance': 'Critical',
                  'people_involved': 3,
                  'date_reported': datetime.datetime(2008, 11, 24, 11, 15, 58),
                  'last_touched': datetime.datetime(2009, 12, 06, 23, 01, 11),
                  'looks_closed': True,
                  'submitter_username': 'fabian.seoane',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://code.google.com/p/sympy/issues/detail?id=1215',
                  'good_for_newcomers': False,
                  'concerns_just_documentation': True,
                  '_project_name': 'SymPy',
                  }
        self.assertEqual(wanted, got)


@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class DataExport(django.test.TestCase):
    def test_snapshot_user_table_without_passwords(self):
        # We'll pretend we're running the snapshot_public_data management command. But
        # to avoid JSON data being splatted all over stdout, we create a fake_stdout to
        # capture that data.
        fake_stdout = StringIO()

        # Now, set up the test:
        # Create a user object
        u = django.contrib.auth.models.User.objects.create(username='bob')
        u.set_password('something_secret')
        u.save()

        # snapshot the public version of that user's data into fake stdout
        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        # Now, delete the user and see if we can reimport bob
        u.delete()
        mysite.profile.models.Person.objects.all().delete() # Delete any leftover Persons too

        ## This code re-imports from the snapshot.
        # for more in serializers.deserialize(), read http://docs.djangoproject.com/en/dev/topics/serialization
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        ### Now the tests:
        # The user is back
        new_u = django.contrib.auth.models.User.objects.get(username='bob')
        # and the user's password is blank (instead of the real password)
        self.assertEquals(new_u.password, '')

    def test_snapshot_user_table_without_all_email_addresses(self):
        # We'll pretend we're running the snapshot_public_data management command. But
        # to avoid JSON data being splatted all over stdout, we create a fake_stdout to
        # capture that data.
        fake_stdout = StringIO()

        # Now, set up the test:
        # Create two Person objects, with corresponding email addresses
        u1 = django.contrib.auth.models.User.objects.create(username='privateguy', email='hidden@example.com')
        Person.create_dummy(user=u1)

        u2 = django.contrib.auth.models.User.objects.create(username='publicguy', email='public@example.com')
        Person.create_dummy(user=u2, show_email=True)

        # snapshot the public version of the data into fake stdout
        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        # Now, delete the them all and see if they come back
        django.contrib.auth.models.User.objects.all().delete()
        Person.objects.all().delete()

        ## This code re-imports from the snapshot.
        # for more in serializers.deserialize(), read http://docs.djangoproject.com/en/dev/topics/serialization
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        ### Now the tests:
        # Django user objects really should have an email address
        # so, if we hid it, we make one up based on the user ID
        new_p1 = Person.objects.get(user__username='privateguy')
        self.assertEquals(new_p1.user.email,
                 'user_id_%d_has_hidden_email_address@example.com' % new_p1.user.id)

        new_p2 = Person.objects.get(user__username='publicguy')
        self.assertEquals(new_p2.user.email, 'public@example.com')

    def test_snapshot_bug(self):
        # data capture, woo
        fake_stdout = StringIO()
        # make fake bug
        b = Bug.create_dummy_with_project()
        b.title = 'fire-ant'
        b.save()

        # snapshot fake bug into fake stdout
        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        #now, delete bug...
        b.delete()

        # let's see if we can re-import fire-ant!
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        # testing to see if there are ANY bugs
        self.assertTrue(Bug.all_bugs.all())
        # testing to see if fire-ant is there
        mysite.search.models.Bug.all_bugs.get(title='fire-ant')

    def test_snapshot_timestamp(self):
        # data capture, woo
        fake_stdout = StringIO()

        # Create local constants that refer to values we will insert and check
        TIMESTAMP_KEY_TO_USE = 'birthday of Asheesh with arbitrary time'
        TIMESTAMP_DATE_TO_USE = datetime.datetime(1985, 10, 20, 3, 21, 20)

        # make fake Timestamp
        t = Timestamp()
        t.key = TIMESTAMP_KEY_TO_USE
        t.timestamp = TIMESTAMP_DATE_TO_USE
        t.save()

        # snapshot fake timestamp into fake stdout
        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        #now, delete the timestamp...
        t.delete()

        # let's see if we can re-import the timestamp
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        # testing to see if there are ANY
        self.assertTrue(Timestamp.objects.all())
        # testing to see if ours is there
        reincarnated_t = mysite.base.models.Timestamp.objects.get(key=TIMESTAMP_KEY_TO_USE)
        self.assertEquals(reincarnated_t.timestamp, TIMESTAMP_DATE_TO_USE)

    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    def test_snapshot_project(self,fake_icon):
        fake_stdout = StringIO()
        # make fake Project
        proj = Project.create_dummy_no_icon(name="karens-awesome-project",language="Python")

        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        # now delete fake Project...
        proj.delete()

        # let's see if we can reincarnate it!
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        # test: are there ANY projects?
        self.assertTrue(Project.objects.all())
        # test: is our lovely fake project there?
        mysite.search.models.Project.objects.get(name="karens-awesome-project")

    def test_not_explode_when_user_has_no_person(self):
        fake_stdout = StringIO()
        # make a User
        django.contrib.auth.models.User.objects.create(username='x')
        # but slyly remove the Person objects
        Person.objects.get(user__username='x').delete()

        # do a snapshot...
        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        # delete the User
        django.contrib.auth.models.User.objects.all().delete()

        # let's see if we can reincarnate it!
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        django.contrib.auth.models.User.objects.get(
            username='x')

    @mock.patch('mysite.customs.ohloh.Ohloh.get_icon_for_project')
    def test_snapshot_project_with_icon(self,fake_icon):
        fake_icon_data = open(os.path.join(
            settings.MEDIA_ROOT, 'no-project-icon.png')).read()
        fake_icon.return_value = fake_icon_data

        fake_stdout = StringIO()
        # make fake Project
        proj = Project.create_dummy(name="karens-awesome-project",language="Python")
        proj.populate_icon_from_ohloh()
        proj.save()

        icon_raw_path = proj.icon_raw.path

        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        # now delete fake Project...
        proj.delete()

        # let's see if we can reincarnate it!
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        # test: are there ANY projects?
        self.assertTrue(Project.objects.all())
        # test: is our lovely fake project there?
        mysite.search.models.Project.objects.get(name="karens-awesome-project")
        #self.assertEquals(icon_raw_path,
        #reincarnated_proj.icon_raw.path)

    def test_snapshot_person(self):

        fake_stdout=StringIO()
        # make fake Person who doesn't care if people know where he is
        zuckerberg = Person.create_dummy(
            first_name="mark",
            location_confirmed = True,
            location_display_name='Palo Alto',
            latitude=0,
            longitude=0)
        self.assertEquals(zuckerberg.get_public_location_or_default(), 'Palo Alto')

        # ...and make a fake Person who REALLY cares about his location being private
        munroe = Person.create_dummy(first_name="randall",
                                     location_confirmed = False,
                                     location_display_name='Cambridge',
                                     latitude=0,
                                     longitude=0)
        self.assertEquals(munroe.get_public_location_or_default(), 'Inaccessible Island')


        # Creating dummy tags, tags_persons and tagtypes
        # Dummy TagTypes
        tagtype_understands = TagType(name="understands")
        tagtype_understands.save()
        tagtype_can_mentor = TagType(name="can_mentor")
        tagtype_can_mentor.save()

        # Dummy Tags
        tag_facebook_development = Tag(text="Facebook development", tag_type=tagtype_understands)
        tag_facebook_development.save()
        tag_something_interesting = Tag(text="Something interesting", tag_type=tagtype_can_mentor)
        tag_something_interesting.save()

        # Dummy Links
        link_zuckerberg = Link_Person_Tag(person=zuckerberg, tag=tag_facebook_development)
        link_zuckerberg.save()
        link_munroe = Link_Person_Tag(person=munroe, tag=tag_something_interesting)
        link_munroe.save()

        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)

        # now, delete fake people
        zuckerberg.delete()
        munroe.delete()
        # ...and tags, tagtypes, and links too
        tag_facebook_development.delete()
        tag_something_interesting.delete()
        tagtype_understands.delete()
        tagtype_can_mentor.delete()
        link_zuckerberg.delete()
        link_munroe.delete()

        # and delete any User objects too
        django.contrib.auth.models.User.objects.all().delete()
        mysite.profile.models.Tag.objects.all().delete()
        mysite.profile.models.TagType.objects.all().delete()
        mysite.profile.models.Link_Person_Tag.objects.all().delete()
        # go go reincarnation gadget
        for obj in django.core.serializers.deserialize('json', fake_stdout.getvalue()):
            obj.save()

        # did we snapshot/save ANY Persons?
        self.assertTrue(Person.objects.all())

        # did our fake Persons get saved?
        new_zuckerberg = mysite.profile.models.Person.objects.get(user__first_name="mark")
        new_munroe = mysite.profile.models.Person.objects.get(user__first_name="randall")

        # check that location_confirmed was saved accurately
        self.assertEquals(new_zuckerberg.location_confirmed, True)
        self.assertEquals(new_munroe.location_confirmed, False)

        # check that location_display_name is appropriate
        self.assertEquals(new_zuckerberg.location_display_name, 'Palo Alto')
        self.assertEquals(new_munroe.location_display_name, 'Inaccessible Island')

        # Check that Zuckerburg has a real lat/long
        self.assertNotEqual(mysite.profile.models.DEFAULT_LATITUDE,
                            new_zuckerberg.latitude)
        self.assertNotEqual(mysite.profile.models.DEFAULT_LONGITUDE,
                            new_zuckerberg.longitude)

        # Check that Randall has no lat/long
        self.assertEquals(mysite.profile.models.DEFAULT_LATITUDE,
                          new_munroe.latitude)
        self.assertEquals(mysite.profile.models.DEFAULT_LONGITUDE,
                          new_munroe.longitude)

        # check that we display both as appropriate
        self.assertEquals(new_zuckerberg.get_public_location_or_default(), 'Palo Alto')
        self.assertEquals(new_munroe.get_public_location_or_default(), 'Inaccessible Island')

        # get tags linked to our two dummy users...
        new_link_zuckerberg = mysite.profile.models.Link_Person_Tag.objects.get(id = new_zuckerberg.user_id)
        new_link_munroe = mysite.profile.models.Link_Person_Tag.objects.get(id = new_munroe.user_id)

        new_tag_facebook_development = mysite.profile.models.Tag.objects.get(link_person_tag__person = new_zuckerberg)
        new_tag_something_interesting = mysite.profile.models.Tag.objects.get(link_person_tag__person = new_munroe)

        # ...and tagtypes for the tags
        new_tagtype_understands = mysite.profile.models.TagType.objects.get(tag__tag_type = new_tag_facebook_development.tag_type)
        new_tagtype_can_mentor = mysite.profile.models.TagType.objects.get(tag__tag_type = new_tag_something_interesting.tag_type)

        # finally, check values
        self.assertEquals(new_link_zuckerberg.person, new_zuckerberg)
        self.assertEquals(new_link_munroe.person, new_munroe)

        self.assertEquals(new_tag_facebook_development.text, 'Facebook development')
        self.assertEquals(new_tag_something_interesting.text, 'Something interesting')

        self.assertEquals(new_tagtype_understands.name, 'understands')
        self.assertEquals(new_tagtype_can_mentor.name, 'can_mentor')

    def test_load_persons_and_profiles1(self):
        self.load_snapshot_file('snapshot1.json')

    def test_load_persons_and_profiles2(self):
        self.load_snapshot_file('snapshot2.json')

    def load_snapshot_file(self, snapshot_file_name):
        snapshot_file_path = os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'snapshots', snapshot_file_name
        )
        with open(snapshot_file_path) as snapshot_file:
            for obj in django.core.serializers.deserialize('json', snapshot_file, using='default'):
                obj.save()

# vim: set nu:

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class TestOhlohAccountImportWithException(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    def setUp(self, do_nothing, do_nothing_1):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        self.dia = mysite.profile.models.DataImportAttempt.objects.create(
            person=asheesh, source='oh', query='paulproteus')

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh',)
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    @mock.patch('twisted.web.client.getPage', fakeGetPage.getPage)
    @mock.patch('mysite.customs.profile_importers.AbstractOhlohAccountImporter.convert_ohloh_contributor_fact_to_citation', mock.Mock(side_effect=KeyError))
    def test_exception_email(self, ignore, ignore_2):
        # setUp() already created the DataImportAttempt
        # so we just run the command:
        cmd = mysite.customs.management.commands.customs_twist.Command()
        cmd.handle(use_reactor=False)

        from django.core import mail

        self.assertTrue(mail.outbox)
        self.assertEqual("[Django] Async error on the site",
                         mail.outbox[0].subject)

        self.assertTrue(all(d.completed for d in mysite.profile.models.DataImportAttempt.objects.all()))

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class BugTrackerEditingViews(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(BugTrackerEditingViews, self).setUp()
        self.twisted = mysite.search.models.Project.create_dummy(name='Twisted System')

    def test_slash_does_not_crash_tracker_editor(self):
        mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name="something/or other")
        client = self.login_with_client()
        url = reverse(mysite.customs.views.list_trackers)
        response = client.post(url, {'list_trackers-tracker_type': 'trac'})
        self.assertEqual(200, response.status_code)

    def test_bug_tracker_edit_form_fills_in_hidden_field(self):
        client = self.login_with_client()
        url = reverse(mysite.customs.views.add_tracker,
                      kwargs={'tracker_type': 'trac'}
                      ) + '?project_id=%d' % (self.twisted.id, )
        response = client.get(url)
        self.assertEqual(self.twisted,
                         response.context['tracker_form'].initial['created_for_project'])

    def test_bug_tracker_edit_url_missing_url_id_302s(self):
        client = self.login_with_client()
        url = reverse(mysite.customs.views.edit_tracker_url, kwargs={
                'tracker_type': 'trac', 'tracker_name': 'whatever',
                'url_id': '000'})

        # reverse won't work without a url_id so we need to add one
        # then remove it once the url has been generated.
        url = url.replace('000', '')

        response = client.get(url)
        # This should redirect to what amounts to a not-found page

        assert response.status_code == 302


@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class BugzillaTrackerEditingViews(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(BugzillaTrackerEditingViews, self).setUp()
        self.kde = mysite.search.models.Project.create_dummy(name='KDE')

    def test_form_create_bugzilla_tracker(self):
        # We start with no BugzillaTrackerModel objects in the DB
        self.assertEqual(0,
                         mysite.customs.models.BugzillaTrackerModel.objects.all().select_subclasses().count())
        form = mysite.customs.forms.BugzillaTrackerForm({
                'tracker_name': 'KDE Bugzilla',
                'base_url': 'https://bugs.kde.org/',
                'created_for_project': self.kde.id,
                'query_url_type': 'xml',
                'max_connections': '8',
                'bug_project_name_format': 'format'})
        if form.errors:
            logging.info(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(1,
                         mysite.customs.models.BugzillaTrackerModel.objects.all().select_subclasses().count())

    def test_form_create_bugzilla_tracker_with_custom_parser(self):
        # We start with no BugzillaTrackerModel objects in the DB
        self.assertEqual(0,
                         mysite.customs.models.BugzillaTrackerModel.objects.all().select_subclasses().count())
        form = mysite.customs.forms.BugzillaTrackerForm({
                'tracker_name': 'KDE Bugzilla',
                'base_url': 'https://bugs.kde.org/',
                'created_for_project': self.kde.id,
                'query_url_type': 'xml',
                'max_connections': '8',
                'custom_parser': 'bugzilla.KDEBugzilla',
                'bug_project_name_format': 'format'})
        if form.errors:
            logging.info(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(1,
                         mysite.customs.models.BugzillaTrackerModel.objects.all().select_subclasses().count())
        btm = mysite.customs.models.BugzillaTrackerModel.objects.all().select_subclasses().get()
        self.assertTrue('bugzilla.KDEBugzilla', btm.custom_parser)


@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class LaunchpadTrackerEditingViews(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(LaunchpadTrackerEditingViews, self).setUp()
        self.kde = mysite.search.models.Project.create_dummy(name='KDE')

    def test_form_create_launchpad_tracker(self):
        # We start with no LaunchpadTrackerModel objects in the DB
        self.assertEqual(0,
                         mysite.customs.models.LaunchpadTrackerModel.objects.all().select_subclasses().count())
        form = mysite.customs.forms.LaunchpadTrackerForm({
                'tracker_name': 'KDE Bugzill',
                'launchpad_name': 'https://bugs.kde.org/',
                'created_for_project': self.kde.id,
                'bitsized_tag': 'easy',
                'max_connections': '8',
                'documentation_tag': 'doc',
                'bug_project_name_format': 'format'})
        if form.errors:
            logging.info(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(1,
                         mysite.customs.models.LaunchpadTrackerModel.objects.all().select_subclasses().count())
        self.assertEqual(1,
                         mysite.customs.models.LaunchpadQueryModel.objects.all().count())


### Tests for importing bug data from YAML files, as emitted by oh-bugimporters
class ExportTrackerAsDict(django.test.TestCase):
    def setUp(self, *args, **kwargs):
        # Set up the Twisted TrackerModel that will be used here.
        self.tm = mysite.customs.models.TracTrackerModel.all_trackers.create(
                tracker_name='Twisted',
                base_url='http://twistedmatrix.com/trac/',
                bug_project_name_format='{tracker_name}',
                bitesized_type='keywords',
                bitesized_text='easy',
                documentation_type='keywords',
                documentation_text='documentation')
        for url in ['http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority',
                     'http://twistedmatrix.com/trac/query?status=assigned&status=new&status=reopened&format=csv&order=priority&keywords=~documentation']:
            mysite.customs.models.TracQueryModel.objects.create(url=url,
                                                                tracker=self.tm)
    def test_export(self):
        exported = self.tm.as_dict()
        golden = {'documentation_text': 'documentation',
                  'documentation_type': 'keywords',
                  'queries': [u'http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority',
                              u'http://twistedmatrix.com/trac/query?status=assigned&status=new&status=reopened&format=csv&order=priority&keywords=~documentation'],
                  'base_url': 'http://twistedmatrix.com/trac/',
                  'bitesized_text': 'easy',
                  'bitesized_type': 'keywords',
                  'bug_project_name_format': '{tracker_name}',
                  'tracker_name': 'Twisted',
                  'as_appears_in_distribution': '',
                  }
        self.assertEqual(golden, exported)

class ImportBugsFromFiles(django.test.TestCase):
    def setUp(self, *args, **kwargs):
        # Create the Twisted project object
        mysite.search.models.Project.objects.create(name='Twisted')

        # Set up the Twisted TrackerModel that will be used here.
        self.tm = mysite.customs.models.TracTrackerModel.all_trackers.create(
                tracker_name='Twisted',
                base_url='http://twistedmatrix.com/trac/',
                bug_project_name_format='{tracker_name}',
                bitesized_type='keywords',
                bitesized_text='easy',
                documentation_type='keywords',
                documentation_text='documentation')

    def test_import_from_data_dict(self):
        sample_data = [
            {'status': 'new', 'as_appears_in_distribution': '',
             'description': "This test method sets the mode of sub1 such that it cannot be deleted in the usual way:\r\r    [Error 5] Access is denied: '_trial_temp\\\\twisted.test.test_paths\\\\FilePathTestCase\\\\test_getPermissions_Windows\\\\bvk9lu\\\\temp\\\\sub1'\r\rThe test should ensure that regardless of the test outcome, this file ends up deletable, or it should delete it itself.\r",
             'importance': 'high',
             'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/5228',
             'date_reported': datetime.datetime(2011, 8, 9, 16, 22, 34),
             '_tracker_name': 'Twisted',
             'submitter_realname': '',
             'last_touched': datetime.datetime(2012, 4, 12, 17, 44, 14),
             'people_involved': 3,
             'title': 'twisted.test.test_paths.FilePathTestCase.test_getPermissions_Windows creates undeleteable file',
             '_project_name': 'Twisted',
             'submitter_username': 'exarkun',
             'last_polled': datetime.datetime(2012, 9, 2, 22, 18, 56, 240068),
             'looks_closed': False,
             'good_for_newcomers': True,
             'concerns_just_documentation': False}]
        self.assertFalse(Bug.all_bugs.all())
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertTrue(Bug.all_bugs.all())

    def test_import_from_data_dict_with_isoformat_date(self):
        sample_data = [
            {'status': 'new', 'as_appears_in_distribution': '',
             'description': "This test method sets the mode of sub1 such that it cannot be deleted in the usual way:\r\r    [Error 5] Access is denied: '_trial_temp\\\\twisted.test.test_paths\\\\FilePathTestCase\\\\test_getPermissions_Windows\\\\bvk9lu\\\\temp\\\\sub1'\r\rThe test should ensure that regardless of the test outcome, this file ends up deletable, or it should delete it itself.\r",
             'importance': 'high',
             'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/5228',
             'date_reported': datetime.datetime(2011, 8, 9, 16, 22, 34).isoformat(),
             '_tracker_name': 'Twisted',
             'submitter_realname': '',
             'last_touched': datetime.datetime(2012, 4, 12, 17, 44, 14).isoformat(),
             'people_involved': 3,
             'title': 'twisted.test.test_paths.FilePathTestCase.test_getPermissions_Windows creates undeleteable file',
             '_project_name': 'Twisted',
             'submitter_username': 'exarkun',
             'last_polled': datetime.datetime(2012, 9, 2, 22, 18, 56, 240068).isoformat(),
             'looks_closed': False,
             'good_for_newcomers': True,
             'concerns_just_documentation': False}]
        self.assertFalse(Bug.all_bugs.all())
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertTrue(Bug.all_bugs.all())
