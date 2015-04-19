# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2011 Jairo E. Lopez
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


import django.test
from django.core.urlresolvers import reverse

import twill
from twill import commands as tc
from django.core.handlers.wsgi import WSGIHandler
from django.contrib.staticfiles.handlers import StaticFilesHandler
from StringIO import StringIO
from django.test.client import Client
import os
import os.path
import subprocess

from django.core.cache import cache
from django.conf import settings

import mock
import datetime
import logging
from django.utils import unittest
from django.utils.unittest import expectedFailure

import mysite.base.view_helpers
import mysite.base.decorators
import mysite.search.models
import mysite.base.templatetags.base_extras
import mysite.base.unicode_sanity
import mysite.profile.views
import mysite.base.views
import mysite.project.views
import mysite.settings

import mysite.base.management.commands.nagios
import mysite.profile.management.commands.send_emails

logger = logging.getLogger(__name__)


def make_twill_url(url):
    # modify this
    return url.replace("http://openhatch.org/",
                       "http://127.0.0.1:8080/")


def better_make_twill_url(url):
    return make_twill_url(url.replace('+', '%2B'))


def twill_goto_view(view_name, kwargs):
    url = "http://openhatch.org" + reverse(view_name, kwargs=kwargs)
    tc.go(better_make_twill_url(url))

mock_get = mock.Mock()
mock_get.return_value = None


class TwillTests(django.test.TestCase):

    @staticmethod
    def _twill_setup():
        app = StaticFilesHandler(WSGIHandler())
        twill.add_wsgi_intercept("127.0.0.1", 8080, lambda: app)

    @staticmethod
    def _twill_quiet():
        # suppress normal output of twill.. You don't want to
        # call this if you want an interactive session
        twill.set_output(StringIO())

    '''Some basic methods needed by other testing classes.'''

    def setUp(self):
        self.real_get = django.core.cache.cache.get
        django.core.cache.cache.get = mock_get
        self.old_dbe = settings.DEBUG_PROPAGATE_EXCEPTIONS
        settings.DEBUG_PROPAGATE_EXCEPTIONS = True
        TwillTests._twill_setup()
        TwillTests._twill_quiet()

    def tearDown(self):
        # If you get an error on one of these lines,
        # maybe you didn't run base.TwillTests.setUp?
        settings.DEBUG_PROPAGATE_EXCEPTIONS = self.old_dbe
        twill.remove_wsgi_intercept('127.0.0.1', 8080)
        tc.reset_browser()
        django.core.cache.cache.get = self.real_get

    def login_with_twill(self):
        # Visit login page
        login_url = 'http://openhatch.org/account/login/old'
        tc.go(make_twill_url(login_url))

        # Log in
        username = "paulproteus"
        password = "paulproteus's unbreakable password"
        tc.fv('login', 'username', username)
        tc.fv('login', 'password', password)
        tc.submit()

    def login_with_client(self, username='paulproteus',
                          password="paulproteus's unbreakable password"):
        client = Client()
        success = client.login(username=username,
                               password=password)
        self.assertTrue(success)
        return client

    def login_with_client_as_barry(self):
        return self.login_with_client(username='barry', password='parallelism')


class MySQLRegex(TwillTests):

    def test_escape(self):
        before2after = {
            'n': '[n]',
            ']': ']',
            '[n': '[[][n]'
        }
        for before, after in before2after.items():
            self.assertEqual(
                mysite.base.view_helpers.mysql_regex_escape(before),
                after)


class TestUriDataHelper(TwillTests):

    def test(self):
        request = mysite.base.view_helpers.ObjectFromDict({
            'is_secure': lambda: True,
            'META': {'SERVER_PORT': '443',
                     'SERVER_NAME': 'name'}})
        data = ((mysite.base.view_helpers.
                 get_uri_metadata_for_generating_absolute_links(request)))
        self.assertEqual(data, {'uri_scheme': 'https',
                                'url_prefix': 'name'})


class GeocoderCanGeocode(TwillTests):

    def get_geocoding_in_json_for_unicode_string(self):
        unicode_str = u'Bark\xe5ker, T\xf8nsberg, Vestfold, Norway'

        # Just exercise the geocoder and ensure it doesn't blow up.
        return mysite.base.view_helpers.cached_geocoding_in_json(unicode_str)

    def test_unicode_string(self):
        self.get_geocoding_in_json_for_unicode_string()


class RemoveByteOrderMarker(unittest.TestCase):

    def test(self):
        sample_bytes = '\xef\xbb\xbf' + 'hi'
        as_fd = StringIO(sample_bytes)
        self.assertNotEqual('hi', as_fd.read())
        as_fd = StringIO(sample_bytes)
        cleaned_up_fd = (
            mysite.base.unicode_sanity.wrap_file_object_in_utf8_check(as_fd))
        result = cleaned_up_fd.read()
        self.assertEqual(type(result), str)  # not unicode
        self.assertEqual(result, 'hi')


class GeocoderCanCache(django.test.TestCase):

    unicode_address = u'Bark\xe5ker, T\xf8nsberg, Vestfold, Norway'

    def get_geocoding_in_json_for_unicode_string(self):
        # Just exercise the geocoder and ensure it doesn't blow up.
        return mysite.base.view_helpers.cached_geocoding_in_json(
            self.unicode_address)

    mock_geocoder = mock.Mock()

    @mock.patch("mysite.base.view_helpers._geocode", mock_geocoder)
    def test_unicode_strings_get_cached(self):

        # Let's make sure that the first time, this runs with original_json,
        # that the cache is empty, and we populate it with original_json.
        cache.delete(
            mysite.base.view_helpers.address2cache_key_name(
                self.unicode_address))

        # NOTE This test uses django.tests.TestCase to skip our
        # monkey-patching of the cache framework
        # When the geocoder's results are being cached properly,
        # the base controller named '_geocode' will not run more than once.
        original_json = "{'key': 'original value'}"
        different_json = (
            "{'key': 'if caching works we should never get this value'}")
        self.mock_geocoder.return_value = eval(original_json)
        self.assertTrue(
            'original value' in
            self.get_geocoding_in_json_for_unicode_string())
        self.mock_geocoder.return_value = eval(different_json)
        try:
            json = self.get_geocoding_in_json_for_unicode_string()
            self.assertTrue('original value' in json)
        except AssertionError:
            raise AssertionError(
                "Geocoded location in json was not cached; it now equals "
                + json)


class TestUnicodifyDecorator(TwillTests):

    def test(self):
        utf8_data = u'\xc3\xa9'.encode('utf-8')  # &eacute;

        @mysite.base.decorators.unicodify_strings_when_inputted
        def sample_thing(arg):
            self.assertEqual(type(arg), unicode)

        sample_thing(utf8_data)


class Feed(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_feed_shows_answers(self):

        # Visit the homepage, notice that there are no answers in the context.

        def get_answers_from_homepage():
            homepage_response = self.client.get('/')
            return homepage_response.context[0]['recent_feed_items']

        self.assertFalse(get_answers_from_homepage())

        # Create a few answers on the project discussion page.
        for x in range(4):
            mysite.search.models.Answer.create_dummy()

        recent_feed_items = (
            mysite.search.models.Answer.objects.all().order_by(
                '-modified_date'))

        # Visit the homepage, assert that the feed item data is on the page,
        # ordered by date descending.
        actual_answer_pks = [
            answer.pk for answer in get_answers_from_homepage()]
        expected_answer_pks = [answer.pk for answer in recent_feed_items]
        self.assertEqual(actual_answer_pks, expected_answer_pks)

    def test_feed_shows_wanna_help(self):
        # set things up so there was a wanna help button click
        person = mysite.profile.models.Person.objects.get(
            user__username='paulproteus')
        p_before = mysite.search.models.Project.create_dummy()
        client = self.login_with_client()
        post_to = reverse(mysite.project.views.wanna_help_do)
        response = client.post(post_to, {u'project': unicode(p_before.pk)})

        # Now when we GET the home page, we see a Note
        # to that effect in the feed
        response = client.get('/')
        items = response.context[0]['recent_feed_items']
        note_we_want_to_see = (
            mysite.search.models.WannaHelperNote.objects.get(
                person=person, project=p_before))
        self.assertTrue(note_we_want_to_see in items)


class CacheMethod(TwillTests):

    @mock.patch('django.core.cache.cache')
    def test(self, mock_cache):
        # Step 0: mock_cache.get() needs to return None
        mock_cache.get.return_value = None

        # Step 1: Create a method where we can test if it was cached (+ cache
        # it)
        class SomeClass:

            def __init__(self):
                self.call_counter = 0

            def cache_key_getter_name(self):
                return 'doodles'

            @mysite.base.decorators.cache_method('cache_key_getter_name')
            def some_method(self):
                self.call_counter += 1
                return str(self.call_counter)

        # Step 2: Call it once to fill the cache
        sc = SomeClass()
        self.assertEqual(sc.some_method(), '1')

        # Step 3: See if the cache has it now
        mock_cache.set.assert_called_with(
            'doodles', '{"value": "1"}', 86400 * 10)


class EnhanceNextWithNewUserMetadata(TwillTests):

    def test_easy(self):
        sample_input = '/'
        wanted = '/?newuser=true'
        got = (
            mysite.base.templatetags.base_extras.
            enhance_next_to_annotate_it_with_newuser_is_true(sample_input))
        self.assertEqual(wanted, got)

    def test_with_existing_query_string(self):
        sample_input = '/?a=b'
        wanted = '/?a=b&newuser=true'
        got = (
            mysite.base.templatetags.base_extras.
            enhance_next_to_annotate_it_with_newuser_is_true(sample_input))
        self.assertEqual(wanted, got)

    def test_with_existing_newuser_equals_true(self):
        sample_input = '/?a=b&newuser=true'
        wanted = sample_input
        got = (mysite.base.templatetags.base_extras.
               enhance_next_to_annotate_it_with_newuser_is_true(sample_input))
        self.assertEqual(wanted, got)


class Unsubscribe(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_verify_unsubscribe_token(self):
        """Generate a valid unsubscribe token. Use it. See that it works. Use
        an invalid one. See that it doesn't work."""
        dude = mysite.profile.models.Person.objects.get(user__username='paulproteus')

        # Generate an invalid token (easiest to do this first)
        plausible_but_invalid_token_string = dude.generate_new_unsubscribe_token().string
        # Make that token invalid by nuking the UnsubscribeToken table
        mysite.profile.models.UnsubscribeToken.objects.all().delete()

        # Generate a once-valid but now-expired token
        expired_token = dude.generate_new_unsubscribe_token()
        just_over_three_months_ago = datetime.datetime.utcnow() - datetime.timedelta(days=91)
        expired_token.created_date = just_over_three_months_ago
        expired_token.save()

        # Generate a valid token
        valid_token_string = dude.generate_new_unsubscribe_token().string
        owner = mysite.profile.models.UnsubscribeToken.whose_token_string_is_this(valid_token_string)
        self.assertEqual(owner, dude)

        # This should definitely be false
        self.assertNotEqual(valid_token_string, plausible_but_invalid_token_string)

        # The invalid token should fail
        self.assertFalse(mysite.profile.models.UnsubscribeToken.whose_token_string_is_this(plausible_but_invalid_token_string))

        self.assertFalse(mysite.profile.models.UnsubscribeToken.whose_token_string_is_this(expired_token.string))

    def test_unsubscribe_view(self):
        dude = mysite.profile.models.Person.objects.get(user__username='paulproteus')
        # Generate a valid token
        valid_token_string = dude.generate_new_unsubscribe_token().string
        # Test that the unsubscribe view's context contains the owner
        url = reverse(mysite.profile.views.unsubscribe, kwargs={'token_string': valid_token_string})
        logger.debug("url %s", url)
        response = self.client.get(url)
        logger.debug("response %s", response)
        self.assertEqual(
            mysite.profile.models.Person.objects.get(),
            response.context['unsubscribe_this_user'])

    def test_unsubscribe_post_handler(self):
        def get_dude():
            return mysite.profile.models.Person.objects.get(user__username='paulproteus')

        dude = get_dude()
        self.assertTrue(get_dude().email_me_re_projects)

        # Generate a valid token
        valid_token_string = dude.generate_new_unsubscribe_token().string
        self.client.post(reverse(mysite.profile.views.unsubscribe_do), {'token_string': valid_token_string})
        self.assertFalse(get_dude().email_me_re_projects)

    @expectedFailure
    def test_submit_form(self):
        def get_dude():
            return mysite.profile.models.Person.objects.get(user__username='paulproteus')
            
        dude = get_dude()
        self.assertTrue(get_dude().email_me_re_projects)

        # Generate a valid token
        valid_token_string = dude.generate_new_unsubscribe_token().string
        self.assertIsNone(twill_goto_view(mysite.profile.views.unsubscribe, kwargs={'token_string': valid_token_string}))
        #TODO Figure out why tc.submit() returns a NoneType and fails
        #A couple of ideas:
        #  South migration on MySQL
        #  submit is broken
        #  twill should leave the code base for WebTest
        self.assertIsNone(tc.submit())
        self.assertIsNotNone(get_dude().email_me_re_projects)

class TimestampTests(django.test.TestCase):

    def test_bugzilla_urls_get_and_update_timestamp_without_errors(self):
        # List of URLs to test (from Bugzila trackers)
        urls = {
            'Miro bitesized':
            'http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
            'KDE bitesized':
            'https://bugs.kde.org/buglist.cgi?query_format=advanced&keywords=junior-jobs&resolution=---',
            'KDE documentation':
            'https://bugs.kde.org/buglist.cgi?query_format=advanced&product=docs&resolution=---',
            'MediaWiki bitesized':
            'https://bugzilla.wikimedia.org/buglist.cgi?keywords=easy&query_format=advanced&resolution=LATER&resolution=---',
            'MediaWiki documentation':
            'https://bugzilla.wikimedia.org/buglist.cgi?query_format=advanced&component=Documentation&resolution=---',
            'Gnome bitesized':
            'https://bugzilla.gnome.org/buglist.cgi?columnlist=id&keywords=gnome-love&query_format=advanced&resolution=---',
            'Mozilla bitesized':
            'https://bugzilla.mozilla.org/buglist.cgi?resolution=---;status_whiteboard_type=substring;query_format=advanced;status_whiteboard=[good%20first%20bug]',
            'Songbird helpwanted':
            'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&resolution=---&keywords=helpwanted',
            'Songbird documentation':
            'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&component=Documentation&resolution=---',
            'Apertium':
            'http://bugs.apertium.org/cgi-bin/bugzilla/buglist.cgi?query_format=advanced&resolution=---',
            'RTEMS':
            'https://www.rtems.org/bugzilla/buglist.cgi?query_format=advanced&resolution=---',
            'XOrg bitesized':
            'https://bugs.freedesktop.org/buglist.cgi?query_format=advanced&keywords=janitor&resolution=---&product=xorg',
            'XOrg documentation':
            'https://bugs.freedesktop.org/buglist.cgi?query_format=advanced&component=Docs%2Fother&component=Documentation&component=Fonts%2Fdoc&resolution=---&product=xorg',
            'Locamotion':
            'http://bugs.locamotion.org/buglist.cgi?query_format=advanced&resolution=---',
            'Hypertriton':
            'https://hypertriton.com/bugzilla/buglist.cgi?query_format=advanced&resolution=---&product=Agar&product=EDAcious&product=FabBSD&product=FreeSG',
            'pygame':
            'http://pygame.motherhamster.org/bugzilla/buglist.cgi?query_format=advanced&resolution=---'
        }
        for url_name in urls:
            logger.info('Testing %s bugs URL.' % url_name)
            url = urls[url_name]
            # Check there is no timestamp i.e. get zero o'clock
            first_timestamp = (
                mysite.base.models.Timestamp.get_timestamp_for_string(url))
            self.assertEqual(first_timestamp,
                             mysite.base.models.Timestamp.ZERO_O_CLOCK)
            # Check the timestamp of the URL can be updated
            mysite.base.models.Timestamp.update_timestamp_for_string(url)
            # Check the new timestamp is after zero o'clock
            new_timestamp = (
                mysite.base.models.Timestamp.get_timestamp_for_string(url))
            self.assertTrue(new_timestamp >
                            mysite.base.models.Timestamp.ZERO_O_CLOCK)


# Test cases for Nagios integration
class NagiosTests(django.test.TestCase):
    # Test for OK Nagios meta data return (0)
    def test_nagios_meta_return_ok(self):
        data = {}
        data['bug_diagnostics'] = {}

        my = data['bug_diagnostics']

        my['Bugs last polled more than than two days + one hour ago'] = 0
        my['Bugs last polled more than three days ago'] = 0
        my['Bugs last polled more than three days ago (in percent)'] = 0.0

        self.assertEqual(0, mysite.base.views.meta_exit_code(data))

    # Test for WARNING Nagios meta data return (1)
    def test_nagios_meta_return_warning(self):
        data = {}
        data['bug_diagnostics'] = {}

        my = data['bug_diagnostics']

        my['Bugs last polled more than than two days + one hour ago'] = 1
        my['Bugs last polled more than three days ago'] = 0
        my['Bugs last polled more than three days ago (in percent)'] = 0.0

        self.assertEqual(1, mysite.base.views.meta_exit_code(data))

    # Test for CRITICAL Nagios meta data return (2)
    def test_nagios_meta_return_critical(self):
        data = {}
        data['bug_diagnostics'] = {}

        my = data['bug_diagnostics']

        my['Bugs last polled more than than two days + one hour ago'] = 0
        my['Bugs last polled more than three days ago'] = 1
        my['Bugs last polled more than three days ago (in percent)'] = 0.0

        self.assertEqual(2, mysite.base.views.meta_exit_code(data))

    # Test for OK Nagios weekly mail return (0)
    def test_nagios_weeklymail_return_ok(self):
        newtime = datetime.datetime.utcnow() - datetime.timedelta(days=4)

        self.assertEqual(0, mysite.base.management.commands.nagios.Command.
                         send_weekly_exit_code(newtime))

    # Test for OK Nagios weekly mail return (0) after send_emails is
    # run as a management command
    def test_nagios_weeklymail_return_ok_after_send(self):
        # Run the send_mail
        command = mysite.profile.management.commands.send_emails.Command()
        command.handle()

        # Now run to see if the function sees things are ok in the
        # database
        self.assertEqual(0, mysite.base.management.commands.nagios.Command.
                         send_weekly_exit_code())

    # Test for CRITICAL Nagios weekly mail return (2)
    def test_nagios_weeklymail_return_critical(self):
        newtime = datetime.datetime.utcnow() - datetime.timedelta(days=8)

        self.assertEqual(2, mysite.base.management.commands.nagios.Command.
                         send_weekly_exit_code(newtime))

    # Test for CRITICAL Nagios weekly mail return (2) on new database
    def test_nagios_weeklymail_return_critical_newdb(self):
        self.assertEqual(2, mysite.base.management.commands.nagios.Command.
                         send_weekly_exit_code())


# Test cases for meta data generation
class MetaDataTests(django.test.TestCase):

    def test_meta_data_zero_div(self):
        mysite.base.views.meta_data()


def find_git_path():
    maybe_git_dir = os.path.abspath(os.getcwd())
    while not os.path.exists(os.path.join(maybe_git_dir, '.git')):
        maybe_git_dir = os.path.abspath(os.path.join(maybe_git_dir, '..'))

    if os.path.exists(os.path.join(maybe_git_dir, '.git')):
        return maybe_git_dir
    raise ValueError("Could not find git directory path.")


# Test that the git repository has no files that conflict with Windows
class WindowsFilesystemCompatibilityTests(unittest.TestCase):

    def test(self):
        # Find the base directory
        dir_with_git = find_git_path()
        # Get a list of files from git
        files = subprocess.Popen(
            ['git', 'ls-files'],
            shell=False,
            stdout=subprocess.PIPE,
            cwd=dir_with_git)
        stdout, stderr = files.communicate()
        file_set = set(stdout.rstrip().split('\n'))

        # Filter that file set down by constraints that would
        # apply on Windows. To that end:
        # Unify files based on case-insensitivity
        files_filtered = set(
            [x.lower() for x in file_set])
        # Filter out any files with '?' in their names, because that is an
        # invalid character for filenames on Windows.
        files_filtered = set(
            [x for x in file_set
             if ('?' not in x)])
        self.assertEqual(file_set, files_filtered)


class GoogleApiTests(unittest.TestCase):

    def test_google_api(self):
        """ Test to see if the google api is returning what we expect """
        response_file_path = os.path.join(settings.MEDIA_ROOT, 'sample-data',
                                          'google_api', 'sample_response')
        with open(response_file_path, 'r') as f:
            response = f.read()

        # Check that latitude and longitude are returned and status is 'OK'
        geocode = mysite.base.view_helpers._geocode(response_data=response)
        self.assertNotEqual(geocode, None)


# Test cases for robots generation
class RenderLiveRobotsTest(django.test.TestCase):
    def test_robots_with_debug_false(self):
        '''Verify that robots.txt returns render_robots_live_site.txt with
        DEBUG set to False
        '''
        response = self.client.get('/robots.txt')
        robots_text = ""
        with open('mysite/base/templates/robots_for_live_site.txt', 'rU') as f:
            robots_text += f.read()
        self.assertEqual(response.content, robots_text)

class RenderDevRobotsTest(django.test.TestCase):
    def setUp(self):
        self.original_value = settings.DEBUG
        settings.DEBUG = True

    def test_robots_with_debug_true(self):
        '''Verify that robots.txt contains text identical to that seen in
         render_robots_for_dev_env.txt with DEBUG set to True
        '''
        response = self.client.get('/robots.txt')
        robots_text = ""
        with open('mysite/base/templates/robots_for_dev_env.txt', 'rU') as f:
            robots_text += f.read()
        settings.DEBUG = False
        self.assertEqual(response.content, robots_text)

    def tearDown(self):
        settings.DEBUG = self.original_value
