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
        twill_setup()
        twill_quiet()

    def tearDown(self):
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

    def login_with_client(self):
        client = Client()
        username='paulproteus'
        password="paulproteus's unbreakable password"
        client.login(username=username,
                     password=password)
        return client

    def signup_with_twill(self, username, email, password):
        tc.go(make_twill_url('http://openhatch.org/'))
        tc.fv('create_profile', 'username',
                username)
        tc.fv('create_profile', 'email',
                email)
        tc.fv('create_profile', 'password',
                password)
        tc.submit()

    # }}}

# vim: set ai et ts=4 sw=4 nu:
