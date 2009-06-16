import django.test
from search.models import Project

import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
from django.test import TestCase
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler
from StringIO import StringIO

# FIXME: Later look into http://stackoverflow.com/questions/343622/how-do-i-submit-a-form-given-only-the-html-source

# Functions you'll need:

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

class ProfileTests(django.test.TestCase):
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testSlash(self):
        response = self.client.get('/profile/')

    def testAddContribution(self):
        url = 'http://openhatch.org/profile/'
        tc.go(make_twill_url(url))
        tc.fv('add_contrib', 'project', 'Babel')
        tc.fv('add_contrib', 'contrib_text', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        # Assert that we are not in some weird GET place with
        # CGI args
        tc.url(r'^[^?]*$')

        tc.find('Babel')
        tc.fv('add_contrib', 'project', 'Baber')
        tc.fv('add_contrib', 'contrib_text', 'msgctxt support')
        tc.fv('add_contrib', 'url', 'http://babel.edgewall.org/ticket/54')
        tc.submit()

        # Verify that leaving and coming back has it still
        # there
        tc.go(make_twill_url(url))
        tc.find('Babel')
        tc.find('Baber')

class OmanTests(django.test.TestCase):
    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testFormEnterYourUsername(self):
        url = 'http://openhatch.org/profile/'
        tc.go(make_twill_url(url))
        tc.fv('enter_free_software_username', 'username', 'paulproteus')
        tc.submit()

        tc.find('ccHost')

import ohloh
class OhlohTests(django.test.TestCase):
    def testContributorFactToProject(self):
        oh = ohloh.get_ohloh()
        self.assertEqual('ccHost', oh.project_id2projectname(15329))
        
#    def testContributorFactToProject(self):
#        oh = ohloh.get_ohloh()
#        self.assertEqual('ccHost', oh.analysis2projectname(603185))

#    def testFindByUsername(self):
#        oh = ohloh.get_ohloh()
        #projects = oh.get_project_list_by_username('paulproteus')
        #self.assert_('ccHost' in projects)

# vim: set ai et ts=4 sw=4:
