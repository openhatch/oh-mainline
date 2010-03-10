# Imports {{{
from mysite.base.tests import make_twill_url, TwillTests
import mysite.project.controllers
from mysite.base.helpers import ObjectFromDict
import mysite.account.tests

from mysite.search.models import Project
from mysite.profile.models import Person, Tag, TagType, Link_Person_Tag, DataImportAttempt, PortfolioEntry, Citation, Forwarder
import mysite.project.views

import mysite.profile.views
import mysite.profile.models
import mysite.profile.controllers

from mysite.profile import views

from django.conf import settings

from mysite.customs import ohloh 

from mysite.base.tests import better_make_twill_url

import re
from StringIO import StringIO
import urllib
import simplejson
import BeautifulSoup
import time
import datetime
import tasks 
import mock
import UserList

import django.test
from django.test.client import Client
from django.core import management, serializers
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
# }}}

class ProjectNameSearch(TwillTests):
    def test_search_for_similar_project_names_backend(self):
        # Create one relevant, one irrelevant project
        relevant = mysite.search.models.Project.create_dummy(name='Twisted System')
        irrelevant = mysite.search.models.Project.create_dummy(name='Irrelevant')

        # Call out function, hoping to find Twisted System
        starts_with_twisted = mysite.project.controllers.similar_project_names(
            'Twisted')
        self.assertEqual(['Twisted System'], [p.name for p in starts_with_twisted])

        # Same with lowercase name
        starts_with_twisted = mysite.project.controllers.similar_project_names(
            'twistEd')
        self.assertEqual(['Twisted System'], [p.name for p in starts_with_twisted])

    def test_search_for_one_matching_project_name(self):
        # If there's an exactly-matching project name, we redirect to that project's page
        # (instead of showing search results).
        relevant = mysite.search.models.Project.create_dummy(name='Twisted System')
        response = self.client.get('/+projects/',
                                   {'q': 'twiSted SysTem'},
                                   follow=True)
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/+projects/Twisted%20System', 302)])

    def test_form_sends_data_to_get(self):
        # This test will fail if a query that selects one project but doesn't
        # equal the project's name causes a redirect.
        relevant = mysite.search.models.Project.create_dummy(name='Twisted System')
        tc.go(better_make_twill_url('http://openhatch.org/+projects'))
        query = 'Twisted'
        tc.fv(1, 'search_q', query)
        tc.submit()
        tc.url('\?q=Twisted') # Assert that URL contains this substring.
        tc.find(query)

    def test_template_get_matching_projects(self):
        mysite.search.models.Project.create_dummy(name='Twisted System')
        mysite.search.models.Project.create_dummy(name='Twisted Orange Drinks')
        response = self.client.get('/+projects/',
                                   {'q': 'Twisted'},
                                   follow=True)
        matching_projects = response.context[0]['matching_projects']
        self.assertEqual(
            sorted([p.name for p in matching_projects]),
            sorted(['Twisted Orange Drinks', 'Twisted System']))
        
class ProjectList(TwillTests):
    def test_it_generally_works(self):
        response = self.client.get('/+projects/')

class ProjectPageCreation(TwillTests):

    @mock.patch('mysite.search.models.Project.populate_icon_from_ohloh')
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def test_post_handler(self, mock_populate_icon, mock_populate_language):
        # Show that it works
        project_name = 'Something novel'
        self.assertFalse(mysite.search.models.Project.objects.filter(name=project_name))
        
        response = self.client.post('/+projects/create_project_page_do/',
                                    {'page_name': project_name}, follow=True)

        # We successfully made the project...
        self.assert_(mysite.search.models.Project.objects.filter(name=project_name))

        #  and redirected.
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/+projects/Something%20novel', 302)])
                
        # FIXME: Enqueue a job into the session to have this user take ownership
        # of this Project.
        # This could easily be a log for edits.

    @mock.patch('mysite.search.models.Project.populate_icon_from_ohloh')
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def test_post_handler_does_nothing_when_project_exists(
        self, mock_populate_icon, mock_populate_language):
        # Show that it works
        project_name = 'Something novel'
        Project.create_dummy(name=project_name.lower())

        # See? We have our project in the database.
        self.assertEqual(1,
                         len(mysite.search.models.Project.objects.all()))
        
        response = self.client.post('/+projects/create_project_page_do/',
                                    {'page_name': project_name}, follow=True)

        # And we still have exactly that one project in the database.
        self.assertEqual(1,
                         len(mysite.search.models.Project.objects.all()))
        
        #  and redirected.
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/+projects/something%20novel', 302)])
        
