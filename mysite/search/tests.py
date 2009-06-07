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
    return url.replace("http://openhatch.org/",
                       "http://127.0.0.1:8080/")

def twill_quiet():
    # suppress normal output of twill.. You don't want to
    # call this if you want an interactive session
    twill.set_output(StringIO())

class NonJavascriptSearch(django.test.TestCase):
    fixtures = ['bugs-for-two-projects.json']

    def setUp(self):
        twill_setup()

    def tearDown(self):
        twill_teardown()

    def testSearch(self):
        response = self.client.get('/search/')
        for n in range(1, 11):
            self.assertContains(response, 'Title #%d' % n)
            self.assertContains(response, 'Description #%d' % n)

    def testMatchingBugsFromMtoN(self):
        response = self.client.get('/search/')
        self.failUnlessEqual(response.context['start'], 1)
        self.failUnlessEqual(response.context['end'], 10)

    def testSearchWithArgs(self):
        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()
        for n in range(1, 11):
            tc.find('Description #%d' % n)
        
        tc.fv('search_opps', 'language', 'c#')
        tc.submit()
        for n in range(717, 727):
            tc.find('Description #%d' % n)
        
    def testPagination(self):
        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()
        for n in range(1, 11):
            tc.find('Description #%d' % n)

        tc.follow('Next')
        for n in range(11, 21):
            tc.find('Description #%d' % n)

    def testPaginationAndChangingSearchQuery(self):
        
        url = 'http://openhatch.org/search/'
        tc.go(make_twill_url(url))
        tc.fv('search_opps', 'language', 'python')
        tc.submit()
        for n in range(1, 11):
            tc.find('Description #%d' % n)

        tc.follow('Next')
        for n in range(11, 21):
            tc.find('Description #%d' % n)

        tc.fv('search_opps', 'language', 'c#')
        tc.submit()
        for n in range(717, 727):
            tc.find('Description #%d' % n)
        tc.follow('Next')
        for n in range(727, 737):
            tc.find('Description #%d' % n)
