# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:

# Imports {{{
from mysite.search.models import Bug, Project
from mysite.base.models import Timestamp
from mysite.profile.models import Person, Tag, TagType
import mysite.profile.views
from mysite.profile.tests import MockFetchPersonDataFromOhloh

import mock
import os
import re
import time
import twill
import lxml
import sys
from twill import commands as tc
from twill.shell import TwillCommandLoop

import django.test
import django.contrib.auth.models
import django.core.serializers
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler

from StringIO import StringIO
import urllib
from urllib2 import HTTPError
import simplejson
import datetime
from dateutil.tz import tzutc
import ohloh
import lp_grabber
import gdata.client

from mysite.profile.tasks import FetchPersonDataFromOhloh
import mysite.customs.profile_importers
import mysite.customs.cia
import mysite.customs.feed
import mysite.customs.github

import mysite.customs.models
import mysite.customs.bugtrackers.roundup
import mysite.customs.bugtrackers.launchpad
import mysite.customs.lp_grabber
import mysite.customs.management.commands.customs_daily_tasks
import mysite.customs.management.commands.snapshot_public_data
# }}}

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

class OhlohTestsThatHitTheNetwork(django.test.TestCase):
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

    def testFindByUsername(self, do_contents_check=True):
        # {{{
        oh = ohloh.get_ohloh()
        projects, web_response = oh.get_contribution_info_by_username('paulproteus')
        # We test the web_response elsewhere
        should_have = {'project': u'ccHost',
                       'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                       'man_months': 1,
                       'primary_language': 'shell script'}

        # Clean the 'permalink' values out of each project...
        for proj in projects:
            if 'permalink' in proj:
                del proj['permalink']

        if do_contents_check:
            self.assert_(should_have in projects)

        return projects
        # }}}

    @mock.patch('mechanize.Browser.open', open_causes_404)
    def testFindByUsernameWith404(self):
        # {{{
        self.assertEqual([], self.testFindByUsername(do_contents_check=False))
        # }}}

    def testFindByOhlohUsername(self, should_have = None):
        # {{{
        oh = ohloh.get_ohloh()
        projects, web_response = oh.get_contribution_info_by_ohloh_username('paulproteus')
        if should_have is None:
            should_have = [{'project': u'ccHost',
                             'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                             'man_months': 1,
                             'primary_language': 'shell script'}]
        for proj in projects:
            del proj['permalink']
        self.assertEqual(should_have, projects)
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
        projects, web_response = oh.get_contribution_info_by_ohloh_username('paulproteus')
        for proj in projects:
            del proj['permalink']
        
        assert {'project': u'ccHost',
                'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                'man_months': 1,
                'primary_language': 'shell script'} in projects
        # }}}

    def testFindContributionsInOhlohAccountByEmail(self):
        oh = ohloh.get_ohloh()
        username = oh.email_address_to_ohloh_username('paulproteus.ohloh@asheesh.org')
        projects, web_response = oh.get_contribution_info_by_ohloh_username(username)
        for proj in projects:
            del proj['permalink']
        
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
        projects, web_response = oh.get_contribution_info_by_username('keescook')
        self.assert_(len(projects) > 1)
        # }}}

    def test_find_debian(self):
        self.assertNotEqual("debian", "ubuntu", "This is an assumption of this test.")
        oh = ohloh.get_ohloh()
        project_data = oh.project_name2projectdata("Debian GNU/Linux")
        self.assertEqual(project_data['name'], 'Debian GNU/Linux', "Expected that when we ask Ohloh, what project is called 'Debian GNU/Linux', Ohloh gives a project named 'Debian GNU/Linux', not, for example, 'Ubuntu'.")

    def test_find_empty_project_without_errors(self):
        oh = ohloh.get_ohloh()
        project_data = oh.project_name2projectdata("theres no PROJECT quite LIKE THIS ONE two pound curry irrelevant keywords watch me fail please if not god help us")
        self.assertEqual(project_data, None, "We successfully return None when the project is not found.")
    # }}}

class OhlohIconTests(django.test.TestCase):
    '''Test that we can grab icons from Ohloh.'''
    # {{{
    def test_ohloh_gives_us_an_icon(self):
        oh = ohloh.get_ohloh()
        icon = oh.get_icon_for_project('f-spot')
        icon_fd = StringIO(icon)
        from PIL import Image
        image = Image.open(icon_fd)
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

class ImportFromDebianQA(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    @mock.patch('mysite.search.tasks.PopulateProjectIconFromOhloh')
    def test_asheesh(self, do_nothing, do_nothing_also):
        # Create a DataImportAttempt for Asheesh
        asheesh = Person.objects.get(user__username='paulproteus')
        dia = mysite.profile.models.DataImportAttempt.objects.create(person=asheesh, source='db', query='asheesh@asheesh.org')

        # Create the DebianQA to track the state.
        dqa = mysite.customs.profile_importers.DebianQA(query=dia.query, dia_id=dia.id)

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

    def test_404(self):
        pass # uhhh

class LaunchpadDataTests(django.test.TestCase):
    def test_project2language(self):
        langs = lp_grabber.project2languages('gwibber')
        self.assertEqual(langs, ['Python'])

        # The project, lazr, is registered on Launchpad, but doesn't
        # have a language assigned to it.
        no_langs = lp_grabber.project2languages('lazr')
        self.assertEqual(no_langs, [])

    @mock.patch('mechanize.Browser.open', open_causes_404)
    def test_person_who_404s(self):
        info = lp_grabber.get_info_for_launchpad_username('Mr. 404')
        self.assertEqual(info, {})

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

class BugzillaTests(django.test.TestCase):
    fixtures = ['miro-project']
    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_kde(self, mock_xml_opener):
        p = Project.create_dummy(name='kmail')
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'kde-117760-2010-04-09.xml')).read())
        kde = mysite.customs.bugtrackers.bugzilla.KDEBugzilla()
        kde.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.submitter_username, 'hasso kde org')
        self.assertEqual(bug.submitter_realname, 'Hasso Tepper')

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_kde_harder_bug(self, mock_xml_opener):
        p = Project.create_dummy(name='kphotoalbum')
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'kde-182054-2010-04-09.xml')).read())
        kde = mysite.customs.bugtrackers.bugzilla.KDEBugzilla()
        kde.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.submitter_username, 'jedd progsoc org')
        self.assertEqual(bug.submitter_realname, '')

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_old_miro_bug_object(self, mock_xml_opener):
        # Parse XML document as if we got it from the web
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        miro.update()
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

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_old_full_grab_miro_bugs(self, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        miro.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assertFalse(bug.looks_closed)

        # And the new manager does find it
        self.assertEqual(Bug.open_ones.all().count(), 1)


    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_old_miro_bugzilla_detects_closedness(self, mock_xml_opener):
        cooked_xml = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data',
            'miro-2294-2009-08-06.xml')).read().replace(
            'NEW', 'CLOSED')
        mock_xml_opener.return_value = lxml.etree.XML(cooked_xml)

        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        miro.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

        # And the new manager successfully does NOT find it!
        self.assertEqual(Bug.open_ones.all().count(), 0)

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_old_full_grab_resolved_miro_bug(self, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06-RESOLVED.xml')).read())

        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        miro.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_old_full_grab_miro_bugs_refreshes_older_bugs(self, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())
        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        miro.update()

        # Pretend there's old data lying around:
        bug = Bug.all_bugs.get()
        bug.people_involved = 1
        bug.last_polled = datetime.datetime.now() - datetime.timedelta(days = 2)
        bug.save()

        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        # Now refresh
        miro.update()

        # Now verify there is only one bug, and its people_involved is 5
        bug = Bug.all_bugs.get()
        self.assertEqual(bug.people_involved, 5)


    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    @mock.patch("mysite.customs.bugtrackers.bugzilla.MiroBugzilla.generate_current_bug_xml")
    def test_old_regrab_miro_bugs_refreshes_older_bugs_even_when_missing_from_csv(self, mock_xml_bug_tree, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        # Situation: Assume there are zero bitesized bugs today.
        # Desire: We re-get old bugs that don't show up in the xml bug list.

        # Prereq: We have some bug with lame data:
        bug = Bug()
        bug.people_involved = 1
        bug.canonical_bug_link = 'http://bugzilla.pculture.org/show_bug.cgi?id=2294'
        bug.date_reported = datetime.datetime.now()
        bug.last_touched = datetime.datetime.now()
        bug.last_polled = datetime.datetime.now() - datetime.timedelta(days = 2)
        bug.project, _ = Project.objects.get_or_create(name='Miro')
        bug.save()

        # Prepare an empty generator
        mock_xml_bug_tree.return_value = iter([])

        # Now, do a crawl and notice that we updated the bug even
        # though the xml bug list is empty
        
        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        miro.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.people_involved, 5)

    # Tests below are for the new abstracted importer. The original
    # versions of the tests are left above until this is integrated.

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_miro_bug_object(self, mock_xml_opener):
        # Parse XML document as if we got it from the web
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        miro_tracker = mysite.customs.models.BugzillaTracker(
                project_name='Miro',
                base_url='http://bugzilla.pculture.org/',
                bug_project_name_format='{project}',
                query_url_type='xml',
                bitesized_type='key',
                bitesized_text='bitesized'
                )
        miro_tracker.save()
        miro_tracker_query_url = mysite.customs.models.BugzillaUrl(
                url='http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                bugzilla_tracker=miro_tracker
                )
        miro_tracker_query_url.save()
        gen_miro = mysite.customs.bugtrackers.bugzilla.generate_bugzilla_tracker_classes(tracker_name='Miro')
        miro = gen_miro.next()
        self.assert_(issubclass(miro, mysite.customs.bugtrackers.bugzilla.BugzillaBugTracker))
        miro_instance = miro()
        miro_instance.update()
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

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_full_grab_miro_bugs(self, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        miro_tracker = mysite.customs.models.BugzillaTracker(
                project_name='Miro',
                base_url='http://bugzilla.pculture.org/',
                bug_project_name_format='{project}',
                query_url_type='xml',
                bitesized_type='key',
                bitesized_text='bitesized'
                )
        miro_tracker.save()
        miro_tracker_query_url = mysite.customs.models.BugzillaUrl(
                url='http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                bugzilla_tracker=miro_tracker
                )
        miro_tracker_query_url.save()
        gen_miro = mysite.customs.bugtrackers.bugzilla.generate_bugzilla_tracker_classes(tracker_name='Miro')
        miro = gen_miro.next()
        self.assert_(issubclass(miro, mysite.customs.bugtrackers.bugzilla.BugzillaBugTracker))
        miro_instance = miro()
        miro_instance.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assertFalse(bug.looks_closed)

        # And the new manager does find it
        self.assertEqual(Bug.open_ones.all().count(), 1)


    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_miro_bugzilla_detects_closedness(self, mock_xml_opener):
        cooked_xml = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data',
            'miro-2294-2009-08-06.xml')).read().replace(
            'NEW', 'CLOSED')
        mock_xml_opener.return_value = lxml.etree.XML(cooked_xml)

        miro_tracker = mysite.customs.models.BugzillaTracker(
                project_name='Miro',
                base_url='http://bugzilla.pculture.org/',
                bug_project_name_format='{project}',
                query_url_type='xml',
                bitesized_type='key',
                bitesized_text='bitesized'
                )
        miro_tracker.save()
        miro_tracker_query_url = mysite.customs.models.BugzillaUrl(
                url='http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                bugzilla_tracker=miro_tracker
                )
        miro_tracker_query_url.save()
        gen_miro = mysite.customs.bugtrackers.bugzilla.generate_bugzilla_tracker_classes(tracker_name='Miro')
        miro = gen_miro.next()
        self.assert_(issubclass(miro, mysite.customs.bugtrackers.bugzilla.BugzillaBugTracker))
        miro_instance = miro()
        miro_instance.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

        # And the new manager successfully does NOT find it!
        self.assertEqual(Bug.open_ones.all().count(), 0)

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_full_grab_resolved_miro_bug(self, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06-RESOLVED.xml')).read())

        miro_tracker = mysite.customs.models.BugzillaTracker(
                project_name='Miro',
                base_url='http://bugzilla.pculture.org/',
                bug_project_name_format='{project}',
                query_url_type='xml',
                bitesized_type='key',
                bitesized_text='bitesized'
                )
        miro_tracker.save()
        miro_tracker_query_url = mysite.customs.models.BugzillaUrl(
                url='http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                bugzilla_tracker=miro_tracker
                )
        miro_tracker_query_url.save()
        gen_miro = mysite.customs.bugtrackers.bugzilla.generate_bugzilla_tracker_classes(tracker_name='Miro')
        miro = gen_miro.next()
        self.assert_(issubclass(miro, mysite.customs.bugtrackers.bugzilla.BugzillaBugTracker))
        miro_instance = miro()
        miro_instance.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    def test_full_grab_miro_bugs_refreshes_older_bugs(self, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())
        miro_tracker = mysite.customs.models.BugzillaTracker(
                project_name='Miro',
                base_url='http://bugzilla.pculture.org/',
                bug_project_name_format='{project}',
                query_url_type='xml',
                bitesized_type='key',
                bitesized_text='bitesized'
                )
        miro_tracker.save()
        miro_tracker_query_url = mysite.customs.models.BugzillaUrl(
                url='http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                bugzilla_tracker=miro_tracker
                )
        miro_tracker_query_url.save()
        gen_miro = mysite.customs.bugtrackers.bugzilla.generate_bugzilla_tracker_classes(tracker_name='Miro')
        miro = gen_miro.next()
        self.assert_(issubclass(miro, mysite.customs.bugtrackers.bugzilla.BugzillaBugTracker))
        miro_instance = miro()
        miro_instance.update()

        # Pretend there's old data lying around:
        bug = Bug.all_bugs.get()
        bug.people_involved = 1
        bug.last_polled = datetime.datetime.now() - datetime.timedelta(days = 2)
        bug.save()

        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        # Now refresh
        miro_instance.update()

        # Now verify there is only one bug, and its people_involved is 5
        bug = Bug.all_bugs.get()
        self.assertEqual(bug.people_involved, 5)


    @mock.patch("mysite.customs.bugtrackers.bugzilla.url2bug_data")
    @mock.patch("mysite.customs.bugtrackers.bugzilla.MiroBugzilla.generate_current_bug_xml")
    def test_regrab_miro_bugs_refreshes_older_bugs_even_when_missing_from_csv(self, mock_xml_bug_tree, mock_xml_opener):
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        # Situation: Assume there are zero bitesized bugs today.
        # Desire: We re-get old bugs that don't show up in the xml bug list.

        # Prereq: We have some bug with lame data:
        bug = Bug()
        bug.people_involved = 1
        bug.canonical_bug_link = 'http://bugzilla.pculture.org/show_bug.cgi?id=2294'
        bug.date_reported = datetime.datetime.now()
        bug.last_touched = datetime.datetime.now()
        bug.last_polled = datetime.datetime.now() - datetime.timedelta(days = 2)
        bug.project, _ = Project.objects.get_or_create(name='Miro')
        bug.save()

        # Prepare an empty generator
        mock_xml_bug_tree.return_value = iter([])

        # Now, do a crawl and notice that we updated the bug even
        # though the xml bug list is empty
        
        miro_tracker = mysite.customs.models.BugzillaTracker(
                project_name='Miro',
                base_url='http://bugzilla.pculture.org/',
                bug_project_name_format='{project}',
                query_url_type='xml',
                bitesized_type='key',
                bitesized_text='bitesized'
                )
        miro_tracker.save()
        miro_tracker_query_url = mysite.customs.models.BugzillaUrl(
                url='http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                bugzilla_tracker=miro_tracker
                )
        miro_tracker_query_url.save()
        gen_miro = mysite.customs.bugtrackers.bugzilla.generate_bugzilla_tracker_classes(tracker_name='Miro')
        miro = gen_miro.next()
        self.assert_(issubclass(miro, mysite.customs.bugtrackers.bugzilla.BugzillaBugTracker))
        miro_instance = miro()
        miro_instance.update()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.people_involved, 5)

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
class UserGetsMessagesDuringImport(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch("mechanize.Browser.open", mock_browser_open)
    def test_user_get_messages_during_import(self):
        paulproteus = Person.objects.get(user__username='paulproteus')

        self.assertEqual(len(paulproteus.user.get_and_delete_messages()), 0)

        self.assertRaises(HTTPError, mysite.customs.ohloh.mechanize_get, 'http://ohloh.net/somewebsiteonohloh', attempts_remaining=1, person=paulproteus)

        self.assertEqual(len(paulproteus.user.get_and_delete_messages()), 1)

class OhlohLogging(django.test.TestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_we_save_ohloh_data_in_success(self):
        # Create a DIA
        # Ask it to do_what_it_says_on_the_tin
        # That will cause it to go out to the network and download some data from Ohloh.
        # Two cases to verify:
        # 1. An error - verify that we save the HTTP response code
        paulproteus = Person.objects.get(user__username='paulproteus')
        success_dia = mysite.profile.models.DataImportAttempt(
            source='rs', person=paulproteus, query='queree')
        success_dia.save()
        success_dia.do_what_it_says_on_the_tin() # go out to Ohloh

        # refresh the DIA with the data from the database
        success_dia = mysite.profile.models.DataImportAttempt.objects.get(
            pk=success_dia.pk)
        self.assertEqual(success_dia.web_response.status, 200)
        self.assert_('ohloh.net' in success_dia.web_response.url)
        self.assert_('<?xml' in success_dia.web_response.text)

    @mock.patch('mechanize.Browser.open', None)
    def _test_we_save_ohloh_data_in_failure(self):
        # Create a DIA
        # Ask it to do_what_it_says_on_the_tin
        # That will cause it to go out to the network and download some data from Ohloh.
        # Two cases to verify:
        # 2. Success - verify that we store the same data Ohloh gave us back
        paulproteus = Person.objects.get(user__username='paulproteus')
        success_dia = DataImportAttempt(
            source='rs', person=paulproteus, query='queree')
        success_dia.do_what_it_says_on_the_tin() # go out to Ohloh
        self.assertEqual(error_dia.web_response.text, 'response text')
        self.assertEqual(error_dia.web_response.url, 'http://theurl.com/')
        self.assertEqual(error_dia.web_response.status, 200)

class MercurialRoundupGrab(django.test.TestCase):

    closed_bug_filename = os.path.join(settings.MEDIA_ROOT, 'sample-data',
            "closed-mercurial-bug.html")

    # When we query for bugs, we'll always get bugs with Status=closed.
    # That's because we're patching out the method that returns a dictionary
    # of the bug's metadata. That dictionary will always contain 'closed' at 'Status'.
    @mock.patch('urllib2.urlopen')
    def test_scrape_bug_status_and_mark_as_closed(self, mock_urlopen,
                                                  project_name='Mercurial',
                                                  should_do_something=True,
                                                  should_use_urlopen=True):
        if Project.objects.filter(name=project_name):
            roundup_project = Project.objects.get(name=project_name)
        else:
            roundup_project = Project.create_dummy(name=project_name)

        mock_urlopen.return_value=open(MercurialRoundupGrab.closed_bug_filename)

        tracker = mysite.customs.bugtrackers.roundup.MercurialTracker()
        did_create = tracker.create_bug_object_for_remote_bug_id_if_necessary(1)
        self.assertEqual(did_create, should_do_something)

        bug = Bug.all_bugs.get()
        self.assert_(bug.looks_closed)

        if should_use_urlopen:
            self.assert_(mock_urlopen.called)

    def test_reimport_same_bug_works(self):
        # First, we do an import.
        self.test_scrape_bug_status_and_mark_as_closed()
        # Immediately we attempt to re-import it. urllib2.urlopen should never
        # be called, because the bug data is so fresh.
        self.test_scrape_bug_status_and_mark_as_closed(should_do_something=False,
                                                       should_use_urlopen=False)

    def test_reimport_same_bug_works_when_bug_is_stale(self):
        # First, import the bug
        self.test_scrape_bug_status_and_mark_as_closed()
        # Then, set it as stale
        bug = Bug.all_bugs.get()
        bug.last_polled = datetime.datetime(1970, 1,1)
        bug.save()

        # Now, re-import. We should call urlopen, and 
        # create_bug_object_for_remote_bug_id_if_necessary should return True
        # because that's what its return value signifies.
        self.test_scrape_bug_status_and_mark_as_closed(should_do_something=True,
                                                       should_use_urlopen=True)

sample_launchpad_data_snapshot = mock.Mock()
sample_launchpad_data_snapshot.return_value = [dict(
        url=u'', project=u'rose.makesad.us', text=u'', status=u'',
        importance=u'low', reporter={u'lplogin': 'a',
                                    'realname': 'b'},
        tags=[], comments=[], date_updated=time.localtime(),
        date_reported=time.localtime(),
        title="Joi's Lab AFS",)]

class AutoCrawlTests(django.test.TestCase):
    @mock.patch('mysite.customs.bugtrackers.launchpad.snapshot_data_from_project', 
                sample_launchpad_data_snapshot)
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def testSearch(self, do_nothing):
        # Verify that we can't find a bug with the right description
        self.assertRaises(mysite.search.models.Bug.DoesNotExist,
                          mysite.search.models.Bug.all_bugs.get,
                          title="Joi's Lab AFS")
        # Now get all the bugs about rose
        mysite.customs.bugtrackers.launchpad.grab_lp_bugs(lp_project='rose',
                                            openhatch_project_name=
                                            u'rose.makesad.us')
        # Now see, we have one!
        b = mysite.search.models.Bug.all_bugs.get(title="Joi's Lab AFS")
        self.assertEqual(b.project.name, u'rose.makesad.us')
        # Ta-da.
        return b

    def test_running_job_twice_does_update(self):
        b = self.testSearch()
        b.description = u'Eat more potato starch'
        b.title = u'Yummy potato paste'
        b.save()

        new_b = self.testSearch()
        self.assertEqual(new_b.title, "Joi's Lab AFS") # bug title restored
        # thanks to fresh import

class LaunchpadImporterTests(django.test.TestCase):

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def test_lp_update_handler(self, do_nothing):
        '''Test the Launchpad import handler with some fake data.'''
        some_date = datetime.datetime(2009, 4, 1, 2, 2, 2)
        query_data = dict(project='GNOME-Do',
                          canonical_bug_link='http://example.com/1')
        new_data = dict(title='Title', status='Godforsaken',
                        description='Everything should be better',
                        importance='High',
                        people_involved=1000 * 1000,
                        submitter_username='yourmom',
                        submitter_realname='Your Mom',
                        date_reported=some_date,
                        last_touched=some_date,
                        last_polled=some_date)

        # Create the bug...
        mysite.customs.bugtrackers.launchpad.handle_launchpad_bug_update(
                project_name=query_data['project'],
                canonical_bug_link=query_data['canonical_bug_link'], 
                new_data=new_data)
        # Verify that the bug was stored.
        bug = Bug.all_bugs.get(canonical_bug_link=
                                       query_data['canonical_bug_link'])
        for key in new_data:
            self.assertEqual(getattr(bug, key), new_data[key])

        # Now re-do the update, this time with more people involved
        new_data['people_involved'] = 1000 * 1000 * 1000
        # pass the data in...
        mysite.customs.bugtrackers.launchpad.handle_launchpad_bug_update(
                project_name=query_data['project'],
                canonical_bug_link=query_data['canonical_bug_link'], 
                new_data=new_data)
        # Do a get; this will explode if there's more than one with the
        # canonical_bug_link, so it tests duplicate finding.
        bug = Bug.all_bugs.get(canonical_bug_link=
                                       query_data[u'canonical_bug_link'])

        for key in new_data:
            self.assertEqual(getattr(bug, key), new_data[key])

    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def test_lp_data_clean(self, do_nothing):
        now_t = (2009, 4, 1, 5, 13, 2) # partial time tuple
        now_d = datetime.datetime(2009, 4, 1, 5, 13, 2)
        # NOTE: We do not test for time zone correctness.
        sample_in = dict(project='GNOME-Do', url='http://example.com/1',
                         title='Title', text='Some long text',
                         importance=None, status='Ready for take-off',
                         comments=[{'user': {
                             'lplogin': 'jones', 'realname': 'Jones'}}],
                         reporter={'lplogin': 'bob', 'realname': 'Bob'},
                         date_reported=now_t,
                         date_updated=now_t,
                         )
        sample_out_query = dict(canonical_bug_link='http://example.com/1')
        sample_out_data = dict(title='Title', description='Some long text',
                               importance='Unknown', status='Ready for take-off',
                               people_involved=2, submitter_realname='Bob',
                               submitter_username='bob',
                               date_reported=now_d,
                               last_touched=now_d)
        out_q, out_d = mysite.customs.bugtrackers.launchpad.clean_lp_data_dict(sample_in)
        self.assertEqual(sample_out_query, out_q)
        # Make sure last_polled is at least in the same year
        self.assertEqual(out_d['last_polled'].year, datetime.date.today().year)
        del out_d['last_polled']
        self.assertEqual(sample_out_data, out_d)

class LaunchpadImportByEmail(django.test.TestCase):

    def test_get_asheesh(self):
        u = mysite.customs.lp_grabber.get_launchpad_username_by_email('asheesh@asheesh.org')
        self.assertEqual(u, "paulproteus")

class LaunchpadImporterMarksFixedBugsAsClosed(django.test.TestCase):
    def test(self):
        '''Start with a bug that is "Fix Released"

        Verify that we set looks_closed to True'''
        # retry this with committed->released
        lp_data_dict = {'project': '',
                        'url': '',
                        'title': '',
                        'text': '',
                        'status': 'Fix Committed',
                        'importance': '',
                        'reporter': {'lplogin': '', 'realname': ''},
                        'comments': '',
                        'date_updated': datetime.datetime.now().timetuple(),
                        'date_reported': datetime.datetime.now().timetuple()}
        # maybe I could have done this with a defaultdict of str with
        # just the non-str exceptions
        query_data, new_data = mysite.customs.bugtrackers.launchpad.clean_lp_data_dict(
            lp_data_dict)
        self.assertTrue(new_data['looks_closed'])

    def test_with_status_missing(self):
        '''Verify we do not explode if Launchpad gives us a bug with no Status

        Verify that we set looks_closed to True'''
        # retry this with committed->released
        lp_data_dict = {'project': '',
                        'url': '',
                        'title': '',
                        'text': '',
                        'importance': '',
                        'reporter': {'lplogin': '', 'realname': ''},
                        'comments': '',
                        'date_updated': datetime.datetime.now().timetuple(),
                        'date_reported': datetime.datetime.now().timetuple()}
        # maybe I could have done this with a defaultdict of str with
        # just the non-str exceptions
        query_data, new_data = mysite.customs.bugtrackers.launchpad.clean_lp_data_dict(
            lp_data_dict)
        self.assertEqual(new_data['status'], 'Unknown')


class OnlineGithub(django.test.TestCase):
    def test_get_language(self):
        top_lang = mysite.customs.github.find_primary_language_of_repo(
            github_username='phinze',
            github_reponame='tircd')
        self.assertEqual(top_lang, 'Perl')

    def test_find_tircd_for_phinze(self):
        '''This test gives our github info_by_username a shot.'''
        repos = mysite.customs.github.repos_by_username('phinze')
        found_tircd_yet = False
        for repo in repos:
            if repo.name == 'tircd':
                found_tircd_yet = True
        self.assertTrue(found_tircd_yet)

    def test_find_unicode_username(self):
        '''This test gives our github info_by_username a shot.'''
        repos = list(mysite.customs.github.repos_by_username(u'\xe9 nobody but hey at least he is mister unicode'))
        self.assertEqual(repos, [])

class OnlineGithubFailures(django.test.TestCase):
    def test_username_404(self):
        '''This test gives our github info_by_username a user to 404 on .'''
        repos = list(mysite.customs.github.repos_by_username('will_never_be_found_PDo7jHoi'))
        self.assertEqual(repos, [])

    @mock.patch('mysite.customs.github._github_repos_list')
    def test_username_with_at_sign(self, mock_repo_list):
        '''This test gives our github info_by_username a user to 404 on .'''
        repos = list(mysite.customs.github.repos_by_username('something@example.com'))
        self.assertFalse(mock_repo_list.called)
        self.assertEqual(repos, [])

    @mock.patch('mysite.customs.github._github_repos_list')
    def test_username_with_at_sign(self, mock_repo_list):
        '''This test gives our github info_by_username a user to 404 on .'''
        repos = list(mysite.customs.github.repos_by_username('something@example.com'))
        self.assertFalse(mock_repo_list.called)
        self.assertEqual(repos, [])

    @mock.patch('mysite.customs.github._get_repositories_user_watches')
    def test_at_sign_user_watch_list(self, mock_method_that_should_not_be_called):
        things = list(mysite.customs.github.repos_user_collaborates_on('something@example.com'))
        self.assertFalse(mock_method_that_should_not_be_called.called)
        self.assertEqual(things, [])

    def test_username_space_404(self):
        '''This test gives our github info_by_username a user to 404 on .'''
        repos = list(mysite.customs.github.repos_by_username('will_never_be_found misterr PDo7jHoi'))
        self.assertEqual(repos, [])

    def test_at_sign_404(self):
        '''This test gives our github info_by_username an email to 404 on.'''
        repos = list(mysite.customs.github.repos_by_username('will_@_never_be_found_PDo7jHoi'))
        self.assertEqual(repos, [])

    def test_at_sign_403(self):
        '''This test gives our github info_by_username an email to 403 on.'''
        repos = list(mysite.customs.github.repos_by_username('dummy@example.com'))
        self.assertEqual(repos, [])

    def test_watching_404(self):
        repos = list(mysite.customs.github._get_repositories_user_watches('will_never_be_found_PDo7jHoi'))
        self.assertEqual(repos, [])

    def test_watching_404_with_space(self):
        repos = list(mysite.customs.github._get_repositories_user_watches('will_never_be_found mister PDo7jHoi'))
        self.assertEqual(repos, [])

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

def tracbug_tests_extract_tracker_specific_data(trac_data, ret_dict):
    # Make modifications to ret_dict using provided metadata
    # Check for the bitesized keyword
    ret_dict['bite_size_tag_name'] = 'easy'
    ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
    # Then pass ret_dict back
    return ret_dict

class TracBug(django.test.TestCase):
    @mock.patch('mysite.customs.bugtrackers.trac.TracBug.as_bug_specific_csv_data')
    def test_create_bug_object_data_dict_more_recent(self, m):
        m.return_value = {
            'branch': '',
            'branch_author': '',
            'cc': 'thijs_ exarkun',
            'component': 'core',
            'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
            'id': '4298',
            'keywords': 'easy',
            'launchpad_bug': '',
            'milestone': '',
            'owner': 'djfroofy',
            'priority': 'normal',
            'reporter': 'thijs',
            'resolution': '',
            'status': 'new',
            'summary': 'Deprecate twisted.persisted.journal',
            'type': 'task'}
        tb = mysite.customs.bugtrackers.trac.TracBug(
            bug_id=4298,
            BASE_URL='http://twistedmatrix.com/trac/')
        cached_html_filename = os.path.join(settings.MEDIA_ROOT, 'sample-data', 'twisted-trac-4298-on-2010-04-02.html')
        tb._bug_html_page = unicode(
            open(cached_html_filename).read(), 'utf-8')
        self.assertEqual(tb.component, 'core')

        got = tb.as_data_dict_for_bug_object(tracbug_tests_extract_tracker_specific_data)
        del got['last_polled']
        wanted = {'title': 'Deprecate twisted.persisted.journal',
                  'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
                  'status': 'new',
                  'importance': 'normal',
                  'people_involved': 4,
                  # FIXME: Need time zone
                  'date_reported': datetime.datetime(2010, 2, 23, 0, 46, 30),
                  'last_touched': datetime.datetime(2010, 3, 12, 18, 43, 5),
                  'looks_closed': False,
                  'submitter_username': 'thijs',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/4298',
                  'good_for_newcomers': True,
                  'looks_closed': False,
                  'bite_size_tag_name': 'easy',
                  'concerns_just_documentation': False,
                  'as_appears_in_distribution': '',
                  }
        self.assertEqual(wanted, got)

    @mock.patch('mysite.customs.bugtrackers.trac.TracBug.as_bug_specific_csv_data')
    def test_create_bug_object_data_dict(self, m):
        m.return_value = {
            'branch': '',
            'branch_author': '',
            'cc': 'thijs_ exarkun',
            'component': 'core',
            'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
            'id': '4298',
            'keywords': 'easy',
            'launchpad_bug': '',
            'milestone': '',
            'owner': 'djfroofy',
            'priority': 'normal',
            'reporter': 'thijs',
            'resolution': '',
            'status': 'new',
            'summary': 'Deprecate twisted.persisted.journal',
            'type': 'task'}
        tb = mysite.customs.bugtrackers.trac.TracBug(
            bug_id=4298,
            BASE_URL='http://twistedmatrix.com/trac/')
        cached_html_filename = os.path.join(settings.MEDIA_ROOT, 'sample-data', 'twisted-trac-4298.html')
        tb._bug_html_page = unicode(
            open(cached_html_filename).read(), 'utf-8')

        got = tb.as_data_dict_for_bug_object(tracbug_tests_extract_tracker_specific_data)
        del got['last_polled']
        wanted = {'title': 'Deprecate twisted.persisted.journal',
                  'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
                  'status': 'new',
                  'importance': 'normal',
                  'people_involved': 5,
                  # FIXME: Need time zone
                  'date_reported': datetime.datetime(2010, 2, 22, 19, 46, 30),
                  'last_touched': datetime.datetime(2010, 2, 24, 0, 8, 47),
                  'looks_closed': False,
                  'submitter_username': 'thijs',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/4298',
                  'good_for_newcomers': True,
                  'looks_closed': False,
                  'bite_size_tag_name': 'easy',
                  'concerns_just_documentation': False,
                  'as_appears_in_distribution': '',
                  }
        self.assertEqual(wanted, got)

    @mock.patch('mysite.customs.bugtrackers.trac.TracBug.as_bug_specific_csv_data')
    def test_create_bug_that_lacks_modified_date(self, m):
        m.return_value = {
            'branch': '',
            'branch_author': '',
            'cc': 'thijs_ exarkun',
            'component': 'core',
            'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
            'id': '4298',
            'keywords': 'easy',
            'launchpad_bug': '',
            'milestone': '',
            'owner': 'djfroofy',
            'priority': 'normal',
            'reporter': 'thijs',
            'resolution': '',
            'status': 'new',
            'summary': 'Deprecate twisted.persisted.journal',
            'type': 'task'}
        tb = mysite.customs.bugtrackers.trac.TracBug(
            bug_id=4298,
            BASE_URL='http://twistedmatrix.com/trac/')
        cached_html_filename = os.path.join(settings.MEDIA_ROOT, 'sample-data', 'twisted-trac-4298-without-modified.html')
        tb._bug_html_page = unicode(
            open(cached_html_filename).read(), 'utf-8')

        got = tb.as_data_dict_for_bug_object(tracbug_tests_extract_tracker_specific_data)
        del got['last_polled']
        wanted = {'title': 'Deprecate twisted.persisted.journal',
                  'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
                  'status': 'new',
                  'importance': 'normal',
                  'people_involved': 5,
                  # FIXME: Need time zone
                  'date_reported': datetime.datetime(2010, 2, 22, 19, 46, 30),
                  'last_touched': datetime.datetime(2010, 2, 22, 19, 46, 30),
                  'looks_closed': False,
                  'submitter_username': 'thijs',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/4298',
                  'good_for_newcomers': True,
                  'looks_closed': False,
                  'bite_size_tag_name': 'easy',
                  'concerns_just_documentation': False,
                  'as_appears_in_distribution': '',
                  }
        self.assertEqual(wanted, got)

    @mock.patch('mysite.customs.bugtrackers.trac.TracBug.as_bug_specific_csv_data')
    def test_create_bug_that_lacks_modified_date_and_uses_owned_by_instead_of_assigned_to(self, m):
        m.return_value = {
            'branch': '',
            'branch_author': '',
            'cc': 'thijs_ exarkun',
            'component': 'core',
            'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
            'id': '4298',
            'keywords': 'easy',
            'launchpad_bug': '',
            'milestone': '',
            'owner': 'djfroofy',
            'priority': 'normal',
            'reporter': 'thijs',
            'resolution': '',
            'status': 'new',
            'summary': 'Deprecate twisted.persisted.journal',
            'type': 'task'}
        tb = mysite.customs.bugtrackers.trac.TracBug(
            bug_id=4298,
            BASE_URL='http://twistedmatrix.com/trac/')
        cached_html_filename = os.path.join(settings.MEDIA_ROOT, 'sample-data', 'twisted-trac-4298-without-modified-using-owned-instead-of-assigned.html')
        tb._bug_html_page = unicode(
            open(cached_html_filename).read(), 'utf-8')

        got = tb.as_data_dict_for_bug_object(tracbug_tests_extract_tracker_specific_data)
        del got['last_polled']
        wanted = {'title': 'Deprecate twisted.persisted.journal',
                  'description': "This package hasn't been touched in 4 years which either means it's stable or not being used at all. Let's deprecate it (also see #4111).",
                  'status': 'new',
                  'importance': 'normal',
                  'people_involved': 5,
                  # FIXME: Need time zone
                  'date_reported': datetime.datetime(2010, 2, 22, 19, 46, 30),
                  'last_touched': datetime.datetime(2010, 2, 22, 19, 46, 30),
                  'looks_closed': False,
                  'submitter_username': 'thijs',
                  'submitter_realname': '',
                  'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/4298',
                  'good_for_newcomers': True,
                  'looks_closed': False,
                  'bite_size_tag_name': 'easy',
                  'concerns_just_documentation': False,
                  'as_appears_in_distribution': '',
                  }
        self.assertEqual(wanted, got)

    @mock.patch('mysite.customs.ohloh.mechanize_get')
    def test_bug_that_404s_is_deleted(self, mock_error):
        mock_error.side_effect = generate_404

        dummy_project = Project.create_dummy()
        bug = Bug()
        bug.project = dummy_project
        bug.canonical_bug_link = 'http://twistedmatrix.com/trac/ticket/1234'
        bug.date_reported = datetime.datetime.utcnow()
        bug.last_touched = datetime.datetime.utcnow()
        bug.last_polled = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        bug.save()
        self.assert_(Bug.all_bugs.count() == 1)

        twisted = mysite.customs.bugtrackers.trac.TwistedTrac()
        twisted.refresh_all_bugs()
        self.assert_(Bug.all_bugs.count() == 0)

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

class OhlohCitationUrlIsUseful(django.test.TestCase):
    def test_ohloh_assemble_url(self):
        project = 'cchost'
        contributor_id = 65837553699824
        wanted = 'https://www.ohloh.net/p/cchost/contributors/65837553699824'
        got = mysite.customs.ohloh.generate_contributor_url(project, contributor_id)
        self.assertEqual(wanted, got)

    def test_slow_ou_paulproteus_import(self):
        oh = mysite.customs.ohloh.get_ohloh()
        got, _ = oh.get_contribution_info_by_ohloh_username(
            ohloh_username='paulproteus')
        # find the ccHost dict
        cchost_data = None
        for entry in got:
            if entry['project'] == 'ccHost':
                cchost_data = entry
        self.assertEqual(cchost_data['permalink'],
                         'https://www.ohloh.net/p/cchost/contributors/65837553699824')

    def test_slow_rs_paulproteus_import(self):
        oh = mysite.customs.ohloh.get_ohloh()
        got, _ = oh.get_contribution_info_by_username(
            username='paulproteus')
        # find the ccHost dict
        cchost_data = None
        for entry in got:
            if entry['project'] == 'ccHost':
                cchost_data = entry
        self.assertEqual(cchost_data['permalink'],
                         'https://www.ohloh.net/p/cchost/contributors/65837553699824')
        
class OnlineBitbucket(django.test.TestCase):
    def test_repo_for_markfreeman(self):
        """This method test to verify an expected
         repository exist for user markfreeman."""
        repos = mysite.customs.bitbucket.get_user_repos('markfreeman')
        found_expected_repo = False
        for repo in repos:
            if repo['name'] == 'py_bitbucket':
                found_expected_repo = True
        self.assertTrue(found_expected_repo)
        
    def test_unknown_username_404(self):
        """This method test that passing an unknown user name 
        will result in an empty list."""
        repos = list(mysite.customs.bitbucket.get_user_repos('no-user-jhkhsdf'))
        self.assertEqual(repos, [])
        
    def test_user_name_space_404(self):
        """This method test that passing a user name
         with a space will result in an empty list."""
        repos = list(mysite.customs.bitbucket.get_user_repos('mark freeman'))
        self.assertEqual(repos, [])
        
class OpenSolaris(django.test.TestCase):

    open_bug_filename = os.path.join(settings.MEDIA_ROOT, 'sample-data',
            "open-opensolaris-bug.html")

    @mock.patch('urllib2.urlopen')
    @mock.patch('mysite.customs.bugtrackers.opensolaris.Bug.all_bugs.get')
    def test_existing_bug_is_updated(self, mock_bug_to_update, mock_urlopen):
        """This method tests that an existing bug
         which should be updated is updated"""
        mock_urlopen.return_value = open(self.open_bug_filename)
        bug = Bug()
        bug.canonical_bug_link = "http://bugs.opensolaris.org/bugdatabase/view_bug.do?bug_id=1"
        bug.last_polled = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        mock_bug_to_update.return_value = bug
        bug_result = mysite.customs.bugtrackers.opensolaris.create_bug_object_for_remote_bug_id_if_necessary(1)
        self.assertEquals(bug_result, True)

    @mock.patch('mysite.customs.bugtrackers.opensolaris.Bug.all_bugs.get')
    def test_existing_bug_is_not_updated(self, mock_bug_to_not_update):
        """This method tests that an existing bug
         which should not be updated is not updated"""
        bug = Bug()
        bug.canonical_bug_link = "http://bugs.opensolaris.org/bugdatabase/view_bug.do?bug_id=1"
        bug.last_polled = datetime.datetime.utcnow()
        mock_bug_to_not_update.return_value = bug
        bug_result = mysite.customs.bugtrackers.opensolaris.create_bug_object_for_remote_bug_id_if_necessary(1)
        self.assertEquals(bug_result, False)

class BugzillaImporterOnlyPerformsAQueryOncePerDay(django.test.TestCase):
    def test_url_is_more_fresh_than_one_day(self):
        # What the heck, let's demo this function out with the Songbird documentation query.
        URL = 'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&component=Documentation&resolution=---' 
        originally_not_fresh = mysite.customs.bugtrackers.bugzilla.url_is_more_fresh_than_one_day(URL)
        self.assertFalse(originally_not_fresh)
        # But now it should be fresh!
        self.assert_(mysite.customs.bugtrackers.bugzilla.url_is_more_fresh_than_one_day(URL))

    def test_url_is_more_fresh_than_one_day_with_really_long_url(self):
        # What the heck, let's demo this function out with the Songbird documentation query.
        URL = 'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&component=Documentation&resolution=---&look=at_me_I_am_really_long_oh_no_what_will_we_do&really=long_very_long_yes_long_so_long_you_will_fall_asleep_of_boredom_reading_this&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong&really=veryverylong' 
        originally_not_fresh = mysite.customs.bugtrackers.bugzilla.url_is_more_fresh_than_one_day(URL)
        self.assertFalse(originally_not_fresh)
        # But now it should be fresh!
        self.assert_(mysite.customs.bugtrackers.bugzilla.url_is_more_fresh_than_one_day(URL))

    @mock.patch('mysite.customs.bugtrackers.bugzilla.url_is_more_fresh_than_one_day', mock.Mock(return_value=False))
    @mock.patch('mysite.customs.bugtrackers.bugzilla.url2bug_data')
    def test_bugzilla_importing_hits_network_if_urls_are_not_fresh(self, mock_xml_opener):
        # First, show that in the not-fresh case, we do hit the network.
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        bug_xml_gen = miro.generate_current_bug_xml()
        for bug_xml in bug_xml_gen:
            pass # Empty the generator
        self.assertTrue(mock_xml_opener.called)

    @mock.patch('mysite.customs.bugtrackers.bugzilla.url_is_more_fresh_than_one_day', mock.Mock(return_value=True))
    @mock.patch('mysite.customs.bugtrackers.bugzilla.url2bug_data')
    def test_bugzilla_importing_avoids_network_if_urls_are_fresh(self, mock_xml_opener):
        # Second, in the stale case, show that we do not hit the network!
        mock_xml_opener.return_value = lxml.etree.XML(open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')).read())

        miro = mysite.customs.bugtrackers.bugzilla.MiroBugzilla()
        bug_xml_gen = miro.generate_current_bug_xml()
        for bug_xml in bug_xml_gen:
            pass # Empty the generator
        self.assertFalse(mock_xml_opener.called)

class DailyBugImporter(django.test.TestCase):

    @mock.patch('mysite.customs.ohloh.mechanize_get')
    def test_roundup_http_error_408_does_not_break(self, mock_error):
        mock_error.side_effect = generate_408
        mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_roundup_trackers()

    @mock.patch('mysite.customs.ohloh.mechanize_get')
    def test_roundup_generic_error_does_break(self, mock_error):
        mock_error.side_effect = ValueError()
        self.assertRaises(ValueError, mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_roundup_trackers)

    @mock.patch('mysite.customs.ohloh.mechanize_get')
    def test_trac_http_error_408_does_not_break(self, mock_error):
        mock_error.side_effect = generate_408
        mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_trac_instances()

    @mock.patch('mysite.customs.ohloh.mechanize_get')
    def test_trac_generic_error_does_break(self, mock_error):
        mock_error.side_effect = ValueError()
        self.assertRaises(ValueError, mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_trac_instances)

    @mock.patch('mysite.customs.ohloh.mechanize_get')
    def test_bugzilla_http_error_504_does_not_break(self, mock_error):
        mock_error.side_effect = generate_504
        mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_bugzilla_instances()

    @mock.patch('mysite.customs.ohloh.mechanize_get')
    def test_bugzilla_generic_error_does_break(self, mock_error):
        mock_error.side_effect = ValueError()
        self.assertRaises(ValueError, mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_bugzilla_instances)

    @mock.patch('gdata.projecthosting.client.ProjectHostingClient.get_issues')
    def test_google_request_error_does_not_break(self, mock_error):
        mock_error.side_effect = gdata.client.RequestError()
        mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_google_instances()

    @mock.patch('gdata.projecthosting.client.ProjectHostingClient.get_issues')
    def test_google_generic_error_does_break(self, mock_error):
        mock_error.side_effect = ValueError()
        self.assertRaises(ValueError, mysite.customs.management.commands.customs_daily_tasks.Command().find_and_update_enabled_google_instances)

    @mock.patch('urllib2.urlopen')
    def test_opensolaris_http_error_408_does_not_break(self, mock_error):
        mock_error.side_effect = generate_408
        mysite.customs.management.commands.customs_daily_tasks.Command().update_opensolaris_osnet()

    @mock.patch('urllib2.urlopen')
    def test_opensolaris_generic_error_does_break(self, mock_error):
        mock_error.side_effect = ValueError()
        self.assertRaises(ValueError, mysite.customs.management.commands.customs_daily_tasks.Command().update_opensolaris_osnet)

def google_tests_sympy_extract_tracker_specific_data(issue, ret_dict):
    # Make modifications to ret_dict using provided atom data
    labels = [label.text for label in issue.label]
    ret_dict['good_for_newcomers'] = ('EasyToFix' in labels)
    ret_dict['bite_size_tag_name'] = 'EasyToFix'
    # Check whether documentation bug
    ret_dict['concerns_just_documentation'] = ('Documentation' in labels)
    # Then pass ret_dict back
    return ret_dict

class GoogleCodeBugTracker(django.test.TestCase):
    @mock.patch('mysite.customs.bugtrackers.google.GoogleBug.get_bug_atom_data')
    def test__bug_id_from_bug_data(self, mock_thing):
        mock_thing.return_value = mysite.base.helpers.ObjectFromDict({'id': {'text': 'http://whatever/3'}}, recursive = True)
        gb = mysite.customs.bugtrackers.google.GoogleBug(google_name='ok', client=None, bug_id=3)
        bug_id = gb._bug_id_from_bug_data()
        self.assertEqual(bug_id, 3)

    @mock.patch('mysite.customs.bugtrackers.google.GoogleBug.get_bug_atom_data')
    def test_create_google_data_dict_with_everything(self, mock_data):
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
        mock_data.return_value = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        client = mysite.customs.bugtrackers.google.get_client()
        gb = mysite.customs.bugtrackers.google.GoogleBug(
            google_name='sympy',
            client=client,
            bug_id=1215)

        got = gb.as_data_dict_for_bug_object(google_tests_sympy_extract_tracker_specific_data)
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
                  'bite_size_tag_name': 'EasyToFix',
                  'concerns_just_documentation': True,
                  }
        self.assertEqual(wanted, got)

    @mock.patch('mysite.customs.bugtrackers.google.GoogleBug.get_bug_atom_data')
    def test_create_google_data_dict_author_in_list(self, mock_data):
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
        mock_data.return_value = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        client = mysite.customs.bugtrackers.google.get_client()
        gb = mysite.customs.bugtrackers.google.GoogleBug(
            google_name='sympy',
            client=client,
            bug_id=1215)

        got = gb.as_data_dict_for_bug_object(google_tests_sympy_extract_tracker_specific_data)
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
                  'bite_size_tag_name': 'EasyToFix',
                  'concerns_just_documentation': True,
                  }
        self.assertEqual(wanted, got)

    @mock.patch('mysite.customs.bugtrackers.google.GoogleBug.get_bug_atom_data')
    def test_create_google_data_dict_owner_in_list(self, mock_data):
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
        mock_data.return_value = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        client = mysite.customs.bugtrackers.google.get_client()
        gb = mysite.customs.bugtrackers.google.GoogleBug(
            google_name='sympy',
            client=client,
            bug_id=1215)

        got = gb.as_data_dict_for_bug_object(google_tests_sympy_extract_tracker_specific_data)
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
                  'bite_size_tag_name': 'EasyToFix',
                  'concerns_just_documentation': True,
                  }
        self.assertEqual(wanted, got)

    @mock.patch('mysite.customs.bugtrackers.google.GoogleBug.get_bug_atom_data')
    def test_create_google_data_dict_without_status(self, mock_data):
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
        mock_data.return_value = mysite.base.helpers.ObjectFromDict(atom_dict, recursive=True)
        client = mysite.customs.bugtrackers.google.get_client()
        gb = mysite.customs.bugtrackers.google.GoogleBug(
            google_name='sympy',
            client=client,
            bug_id=1215)

        got = gb.as_data_dict_for_bug_object(google_tests_sympy_extract_tracker_specific_data)
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
                  'bite_size_tag_name': 'EasyToFix',
                  'concerns_just_documentation': True,
                  }
        self.assertEqual(wanted, got)

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
        p1 = Person.create_dummy(user=u1)

        u2 = django.contrib.auth.models.User.objects.create(username='publicguy', email='public@example.com')
        p2 = Person.create_dummy(user=u2, show_email=True)

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
		reincarnated_b = mysite.search.models.Bug.all_bugs.get(title='fire-ant')
		
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
        reincarnated_proj = mysite.search.models.Project.objects.get(name="karens-awesome-project")

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

        u = django.contrib.auth.models.User.objects.get(
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
        reincarnated_proj = mysite.search.models.Project.objects.get(name="karens-awesome-project")
        #self.assertEquals(icon_raw_path,
        #reincarnated_proj.icon_raw.path)

    def test_snapshot_person(self):
        fake_stdout=StringIO()
        # make fake Person who doesn't care if people know where he is
        zuckerberg = Person.create_dummy(first_name="mark",location_confirmed = True, location_display_name='Palo Alto')
        self.assertEquals(zuckerberg.get_public_location_or_default(), 'Palo Alto')

        # ...and make a fake Person who REALLY cares about his location being private
        munroe = Person.create_dummy(first_name="randall",location_confirmed = False, location_display_name='Cambridge')
        self.assertEquals(munroe.get_public_location_or_default(), 'Inaccessible Island')
        
        command = mysite.customs.management.commands.snapshot_public_data.Command()
        command.handle(output=fake_stdout)
        
        # now, delete fake people
        zuckerberg.delete()
        munroe.delete()
        # and delete any User objects too
        django.contrib.auth.models.User.objects.all().delete()
        
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

        # check that we display both as appropriate
        self.assertEquals(new_zuckerberg.get_public_location_or_default(), 'Palo Alto')
        self.assertEquals(new_munroe.get_public_location_or_default(), 'Inaccessible Island')
# vim: set nu:

