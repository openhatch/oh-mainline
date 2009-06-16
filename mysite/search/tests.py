import django.test
from search.models import Project, Bug
import search.views
import datetime

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

class AutoCompleteTests(django.test.TestCase):
    """
    Test whether the autocomplete can handle
     - a field-specific query
     - a non-field-specific (fulltext) query
    """

    def setUp(self):
        self.project_chat = Project.objects.create(name='ComicChat', language='C++')
        self.project_kazaa = Project.objects.create(name='Kazaa', language='Vogon')
        self.bug_in_chat = Bug.objects.create(project=self.project_chat,
                people_involved=2,
                date_reported=datetime.date(2009, 4, 1),
                last_touched=datetime.date(2009, 4, 2),
                last_polled=datetime.date(2009, 4, 2),
                submitter_realname="Zaphod Beeblebrox",
                submitter_username="zb",
                canonical_bug_link="http://example.com/",
                )

    def testInstantiateSuggestions(self):
        suggestions = search.views.get_autocompletion_suggestions('')
        self.assert_("lang:Vogon" in suggestions)

    def testQueryNotFieldSpecific(self):
        c_suggestions = search.views.get_autocompletion_suggestions('C')
        self.assert_('lang:C++' in c_suggestions)
        self.assert_('project:ComicChat' in c_suggestions)

    def testQueryFieldSpecific(self):
        lang_C_suggestions = search.views.get_autocompletion_suggestions(
                'lang:C')
        self.assert_('lang:C++' in lang_C_suggestions)
        self.assert_('lang:Python' not in lang_C_suggestions)
        self.assert_('project:ComicChat' not in lang_C_suggestions)

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

# vim: set ai et ts=4 sw=4 columns=80:
