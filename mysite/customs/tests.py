# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:

# Imports {{{
from mysite.search.models import Project, Bug
from mysite.profile.models import Person, Tag, TagType
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
from dateutil.tz import tzutc
import ohloh
import lp_grabber

from mysite.profile.tasks import FetchPersonDataFromOhloh
import mysite.customs.miro
import mysite.customs.debianqa
import mysite.customs.cia
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

def generate_403(self):
    import urllib2
    raise urllib2.HTTPError('', 403, {}, {}, None)

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

class ImportFromDebianQAReally(django.test.TestCase):
    def test_asheesh(self):
        source_package_names = mysite.customs.debianqa.source_packages_maintained_by('asheesh@asheesh.org')
        self.assertEqual(set(source_package_names),
                         set([('ccd2iso', 'Converter from CloneCD disc image format to standard ISO'), ('alpine', 'Text-based email client, friendly for novices but powerful'), ('cue2toc', "converts CUE files to cdrdao's TOC format"), ('liblicense', 'Stores and retrieves license information in media files'), ('exempi', 'library to parse XMP metadata (Library)')]))

    def test_mister_404(self):
        source_package_names = mysite.customs.debianqa.source_packages_maintained_by('http://mister.404/dummy')
        self.assertEqual(list(source_package_names), [])

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
    def test_kde(self):
        p = Project.create_dummy(name='KDE')
        f = os.path.join(settings.MEDIA_ROOT, 'sample-data', 'kde-117760-2010-04-09.xml')
        xml_fd = file(f)
        bug = mysite.customs.miro.xml2bug_object(xml_fd)
        self.assertEqual(bug.submitter_username, 'hasso kde org')
        self.assertEqual(bug.submitter_realname, 'Hasso Tepper')

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
    def test_miro_bugzilla_detects_closedness(self, mock_csv_maker, mock_xml_opener):
        cooked_xml = open(os.path.join(
            settings.MEDIA_ROOT, 'sample-data',
            'miro-2294-2009-08-06.xml')).read().replace(
            'NEW', 'CLOSED')
        mock_xml_opener.return_value = StringIO(cooked_xml)
        
        mock_csv_maker.return_value = StringIO("""bug_id,useless
1,useless""")
        mysite.customs.miro.grab_miro_bugs()
        all_bugs = Bug.all_bugs.all()
        self.assertEqual(len(all_bugs), 1)
        bug = all_bugs[0]
        self.assertEqual(bug.canonical_bug_link,
                         'http://bugzilla.pculture.org/show_bug.cgi?id=2294')
        self.assert_(bug.looks_closed)

        # And the new manager successfully does NOT find it!
        self.assertEqual(Bug.open_ones.all().count(), 0)

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

class TracBug(django.test.TestCase):
    def test_eval_in_description(self):
        four_chars = r'\r\n'
        self.assertEqual(len(four_chars), 4)
        two_chars = mysite.customs.bugtrackers.trac.TracBug.string_un_csv(
            four_chars)
        self.assertEqual(len(two_chars), 2)
        self.assertEqual(two_chars, '\r\n')

    def test_unicodify_in_the_face_of_junk(self):
        weird_chars = u'\x01'
        unicoded = mysite.customs.bugtrackers.trac.TracBug.string_un_csv(
            weird_chars)
        self.assertEqual(unicoded, '')
        

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

        got = tb.as_data_dict_for_bug_object()
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

        got = tb.as_data_dict_for_bug_object()
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

        got = tb.as_data_dict_for_bug_object()
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

        got = tb.as_data_dict_for_bug_object()
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

    def test_ohloh_assemble_url(self):
        project = 'ccHOST'
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
        
# vim: set nu:
