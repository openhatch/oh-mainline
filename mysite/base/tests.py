import django.test
import twill
from twill import commands as tc
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import AdminMediaHandler 
from StringIO import StringIO
from django.test.client import Client
import urllib

import mock

import mysite.base.helpers
import mysite.base.controllers
import mysite.base.decorators
import mysite.search.models
import mysite.base.templatetags.base_extras

def twill_setup():
    app = AdminMediaHandler(WSGIHandler())
    twill.add_wsgi_intercept("127.0.0.1", 8080, lambda: app)

def twill_teardown():
    twill.remove_wsgi_intercept('127.0.0.1', 8080)
    tc.reset_browser()

def make_twill_url(url):
    # modify this
    return url.replace("http://openhatch.org/",
            "http://127.0.0.1:8080/")

def better_make_twill_url(url):
    return make_twill_url(url.replace('+','%2B'))

def twill_quiet():
    # suppress normal output of twill.. You don't want to
    # call this if you want an interactive session
    twill.set_output(StringIO())

mock_get = mock.Mock()
mock_get.return_value = None

class TwillTests(django.test.TestCase):
    '''Some basic methods needed by other testing classes.'''
    # {{{
    def setUp(self):
        self.real_get = django.core.cache.cache.get
        django.core.cache.cache.get = mock_get
        from django.conf import settings
        self.old_dbe = settings.DEBUG_PROPAGATE_EXCEPTIONS
        settings.DEBUG_PROPAGATE_EXCEPTIONS = True
        twill_setup()
        twill_quiet()

    def tearDown(self):
        # If you get an error on one of these lines,
        # maybe you didn't run base.TwillTests.setUp?
        from django.conf import settings
        settings.DEBUG_PROPAGATE_EXCEPTIONS = self.old_dbe
        twill_teardown()
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
        self.assert_(success)
        return client

    def login_with_client_as_barry(self):
        return self.login_with_client(username='barry', password='parallelism')

    def signup_with_twill(self, username, email, password):
        """ Used by account.tests.Signup, which is omitted while we use invite codes. """
        pass

class MySQLRegex(TwillTests):
    def test_escape(self):
        before2after = {
                'n': '[n]',
                ']': ']',
                '[n': '[[][n]'
                }
        for before, after in before2after.items():
            self.assertEqual(
                    mysite.base.controllers.mysql_regex_escape(before), 
                    after)

class TestUriDataHelper(TwillTests):
    def test(self):
        request = mysite.base.helpers.ObjectFromDict({
            'is_secure': lambda : True,
            'META': {'SERVER_PORT': '443',
                     'SERVER_NAME': 'name'}})
        data = mysite.base.controllers.get_uri_metadata_for_generating_absolute_links(request)
        self.assertEqual(data, {'uri_scheme': 'https',
                                'url_prefix': 'name'})

class GeocoderCanGeocode(TwillTests):

    def get_geocoding_in_json_for_unicode_string(self):
        unicode_str = u'Bark\xe5ker, T\xf8nsberg, Vestfold, Norway'

        # Just exercise the geocoder and ensure it doesn't blow up.
        return mysite.base.controllers.cached_geocoding_in_json(unicode_str)

    def test_unicode_string(self):
        self.get_geocoding_in_json_for_unicode_string()

class GeocoderCanCache(django.test.TestCase):

    def get_geocoding_in_json_for_unicode_string(self):
        unicode_str = u'Bark\xe5ker, T\xf8nsberg, Vestfold, Norway'

        # Just exercise the geocoder and ensure it doesn't blow up.
        return mysite.base.controllers.cached_geocoding_in_json(unicode_str)

    mock_geocoder = mock.Mock()
    @mock.patch("mysite.base.controllers._geocode", mock_geocoder)
    def test_unicode_strings_get_cached(self):
        ### NOTE This test uses django.tests.TestCase to skip our monkey-patching of the cache framework
        # When the geocoder's results are being cached properly, 
        # the base controller named '_geocode' will not run more than once.
        original_json = "{'key': 'original value'}"
        different_json = "{'key': 'if caching works we should never get this value'}"
        self.mock_geocoder.return_value = eval(original_json)
        self.assert_('original value' in self.get_geocoding_in_json_for_unicode_string()) 
        self.mock_geocoder.return_value = eval(different_json)
        try:
            json = self.get_geocoding_in_json_for_unicode_string()
            self.assert_('original value' in json) 
        except AssertionError:
            raise AssertionError, "Geocoded location in json was not cached; it now equals " + json

class TestUnicodifyDecorator(TwillTests):
    def test(self):
        utf8_data = u'\xc3\xa9'.encode('utf-8') # &eacute;

        @mysite.base.decorators.unicodify_strings_when_inputted
        def sample_thing(arg):
            self.assertEqual(type(arg), unicode)

        sample_thing(utf8_data)

class Feed(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_feed_shows_recent_answers(self):

        # Visit the homepage, notice that there are no answers in the context.

        def get_answers_from_homepage():
            homepage_response = self.client.get('/')
            return homepage_response.context[0]['recent_answers']
        
        self.assertFalse(get_answers_from_homepage())

        # Create a few answers on the project discussion page.
        for x in range(4):
            mysite.search.models.Answer.create_dummy()

        recent_answers = mysite.search.models.Answer.objects.all().order_by('-modified_date')

        # Visit the homepage, assert that the feed item data is on the page,
        # ordered by date descending.
        actual_answer_pks = list(get_answers_from_homepage().values_list('pk', flat=True))
        expected_answer_pks = list(recent_answers.values_list('pk', flat=True))
        self.assertEqual(actual_answer_pks, expected_answer_pks)

class CacheMethod(TwillTests):

    @mock.patch('django.core.cache.cache')
    def test(self, mock_cache):
        # Step 0: mock_cache.get() needs to return None
        mock_cache.get.return_value = None
        
        # Step 1: Create a method where we can test if it was cached (+ cache it)
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
        mock_cache.set.assert_called_with('doodles', '{"value": "1"}', 86400 * 10)

class EnhanceNextWithNewUserMetadata(TwillTests):
    def test_easy(self):
        sample_input = '/'
        wanted = '/?newuser=true'
        got = mysite.base.templatetags.base_extras.enhance_next_to_annotate_it_with_newuser_is_true(sample_input)
        self.assertEqual(wanted, got)

    def test_with_existing_query_string(self):
        sample_input = '/?a=b'
        wanted = '/?a=b&newuser=true'
        got = mysite.base.templatetags.base_extras.enhance_next_to_annotate_it_with_newuser_is_true(sample_input)
        self.assertEqual(wanted, got)

    def test_with_existing_newuser_equals_true(self):
        sample_input = '/?a=b&newuser=true'
        wanted = sample_input
        got = mysite.base.templatetags.base_extras.enhance_next_to_annotate_it_with_newuser_is_true(sample_input)
        self.assertEqual(wanted, got)

# vim: set ai et ts=4 sw=4 nu:
