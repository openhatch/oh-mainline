# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:

# Imports {{{
from mysite.search.models import Project, Bug
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag
import mysite.profile.views
from mysite.profile.tests import MockFetchPersonDataFromOhloh

import mock
import os
import re
import twill
import lxml
from twill import commands as tc
from twill.shell import TwillCommandLoop

import django.test
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
import ohloh
import lp_grabber

from mysite.profile.tasks import FetchPersonDataFromOhloh
import mysite.customs.miro
import mysite.customs.feed
import mysite.customs.github

import mysite.customs.models
import mysite.customs.lp_grabber
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

    def testFindByUsername(self, do_contents_check=True):
        # {{{
        oh = ohloh.get_ohloh()
        projects, web_response = oh.get_contribution_info_by_username('paulproteus')
        # We test the web_response elsewhere
        should_have = {'project': u'ccHost',
                       'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                       'man_months': 1,
                       'primary_language': 'shell script'}

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
        
        assert {'project': u'ccHost',
                'project_homepage_url': 'http://wiki.creativecommons.org/CcHost',
                'man_months': 1,
                'primary_language': 'shell script'} in projects
        # }}}

    def testFindContributionsInOhlohAccountByEmail(self):
        oh = ohloh.get_ohloh()
        username = oh.email_address_to_ohloh_username('paulproteus.ohloh@asheesh.org')
        projects, web_response = oh.get_contribution_info_by_ohloh_username(username)
        
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

class MiroTests(django.test.TestCase):
    def test_miro_bug_object(self):
        # Parse XML document as if we got it from the web
        f = os.path.join(settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml')
        xml_fd = file(f)
        bug = mysite.customs.miro.xml2bug_object(xml_fd)

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

    def test_csv_parsing(self):
        csv_fd = StringIO('''some_header,whatever
1,silly bug
2,other silly bug''')
        bugs = mysite.customs.miro.bugzilla_query_to_bug_ids(
            csv_fd)
        self.assertEqual(bugs, [1, 2])

    @mock.patch("mysite.customs.miro.open_xml_url")
    @mock.patch("mysite.customs.miro.bitesized_bugs_csv_fd")
    def test_full_grab_miro_bugs(self, mock_csv_maker, mock_xml_opener):
        mock_xml_opener.return_value = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml'))

        mock_csv_maker.return_value = StringIO("""bug_id,useless
1,useless""")
        mysite.customs.miro.grab_miro_bugs()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assertFalse(bug.looks_closed)

        # And the new manager does find it
        self.assertEqual(Bug.open_ones.all().count(), 1)


    @mock.patch("mysite.customs.miro.open_xml_url")
    @mock.patch("mysite.customs.miro.bitesized_bugs_csv_fd")
    def test_full_grab_resolved_miro_bug(self, mock_csv_maker, mock_xml_opener):
        mock_xml_opener.return_value = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06-RESOLVED.xml'))

        mock_csv_maker.return_value = StringIO("""bug_id,useless
1,useless""")
        mysite.customs.miro.grab_miro_bugs()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

    @mock.patch("mysite.customs.miro.open_xml_url")
    @mock.patch("mysite.customs.miro.bitesized_bugs_csv_fd")
    def test_full_grab_miro_bugs_refreshes_older_bugs(self, mock_csv_maker, mock_xml_opener):
        mock_xml_opener.return_value = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml'))

        mock_csv_maker.return_value = StringIO("""bug_id,useless
2294,useless""")
        mysite.customs.miro.grab_miro_bugs()

        # Pretend there's old data lying around:
        bug = Bug.all_bugs.get()
        bug.people_involved = 1
        bug.save()

        mock_xml_opener.return_value = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml'))

        # Now refresh
        mysite.customs.miro.grab_miro_bugs()

        # Now verify there is only one bug, and its people_involved is 5
        bug = Bug.all_bugs.get()
        self.assertEqual(bug.people_involved, 5)


    @mock.patch("mysite.customs.miro.open_xml_url")
    @mock.patch("mysite.customs.miro.bitesized_bugs_csv_fd")
    def test_regrab_miro_bugs_refreshes_older_bugs_even_when_missing_from_csv(self, mock_csv_maker, mock_xml_opener):
        mock_xml_opener.return_value = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'miro-2294-2009-08-06.xml'))

        # Situation: Assume there are zero bitesized bugs today.
        # Desire: We re-get old bugs that don't show up in the CSV.

        # Prereq: We have some bug with lame data:
        bug = Bug()
        bug.people_involved = 1
        bug.canonical_bug_link = 'http://bugzilla.pculture.org/show_bug.cgi?id=2294'
        bug.date_reported = datetime.datetime.now()
        bug.last_touched = datetime.datetime.now()
        bug.last_polled = datetime.datetime.now()
        bug.project, _ = Project.objects.get_or_create(name='Miro')
        bug.save()

        # Prepare a fake CSV that is empty
        mock_csv_maker.return_value = StringIO('')

        # Now, do a crawl and notice that we updated the bug even though the CSV is empty
        
        mysite.customs.miro.grab_miro_bugs() # refreshes no bugs since CSV is empty!
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

mock_browser_open = mock.Mock()
mock_browser_open.side_effect = HTTPError(url="http://theurl.com/", code=504, msg="", hdrs="", fp=open("/dev/null")) 
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

class RoundupGrab(django.test.TestCase):

    closed_bug_filename = os.path.join(settings.MEDIA_ROOT, 'sample-data',
            "closed-python-bug.html")

    # When we query for bugs, we'll always get bugs with Status=closed.
    # That's because we're patching out the method that returns a dictionary
    # of the bug's metadata. That dictionary will always contain 'closed' at 'Status'.
    @mock.patch('urllib2.urlopen',
            mock.Mock(return_value=open(closed_bug_filename)))
    def test_scrape_bug_status_and_mark_as_closed(self):
        roundup_project = Project.create_dummy()
        tracker = mysite.customs.models.RoundupBugTracker(
                project=roundup_project,
                roundup_root_url="http://example.org")
        tracker.save()

        bug = tracker.create_bug_object_for_remote_bug_id(1)
        self.assert_(bug.looks_closed)

class LaunchpadImportByEmail(django.test.TestCase):

    def test_get_asheesh(self):
        u = mysite.customs.lp_grabber.get_launchpad_username_by_email('asheesh@asheesh.org')
        self.assertEqual(u, "paulproteus")

class SlowGithubTest(django.test.TestCase):
    def test_get_language(self):
        top_lang = mysite.customs.github.find_primary_language_of_repo(
            github_username='phinze',
            github_reponame='tircd')
        self.assertEqual(top_lang, 'Perl')

# vim: set nu:
