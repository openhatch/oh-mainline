import django.test
import twill
from twill import commands as tc
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import AdminMediaHandler 
from StringIO import StringIO
from django.test.client import Client

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

def twill_quiet():
    # suppress normal output of twill.. You don't want to
    # call this if you want an interactive session
    twill.set_output(StringIO())

class TwillTests(django.test.TestCase):
    '''Some basic methods needed by other testing classes.'''
    # {{{
    def setUp(self):
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

    def login_with_twill(self):
        # Visit login page
        login_url = 'http://openhatch.org/'
        tc.go(make_twill_url(login_url))

        # Log in
        username = "paulproteus"
        password = "paulproteus's unbreakable password"
        try:
            tc.fv('login', 'login_username', username)
            tc.fv('login', 'login_password', password)
            tc.submit()
        except:
            pass # lol fixme

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

    # }}}

class LandingPage(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def test_show_landing_page_iff_logged_in(self):
        # {{{
        client = Client()
        response = client.get('/')
        self.assertTemplateUsed(response, 'base/homepage.html')

        client2 = self.login_with_client()
        response2 = client2.get('/')
        self.assertTemplateUsed(response2, 'base/landing.html')
        # }}}

    # }}}

# vim: set ai et ts=4 sw=4 nu:
