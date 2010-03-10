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
            'Twisted')
        self.assertEqual(['Twisted System'], [p.name for p in starts_with_twisted])

    def test_search_for_one_matching_project_name(self):
        relevant = mysite.search.models.Project.create_dummy(name='Twisted System')
        response = self.client.get('/+projects/',
                                   {'q': 'Twisted System'},
                                   follow=True)
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/+projects/Twisted%20System', 302)])

    def test_search_when_two_projects_match(self):
        relevant1 = mysite.search.models.Project.create_dummy(name='Twisted System')
        relevant2 = mysite.search.models.Project.create_dummy(name='Twisted Orange Drinks')
        response = self.client.get('/+projects/',
                                   {'q': 'Twisted'},
                                   follow=True)
        project_options = response.context[0]['project_options']
        self.assertEqual(
            sorted([p.name for p in project_options]),
            sorted(['Twisted Orange Drinks', 'Twisted System']))
        
class ProjectList(TwillTests):
    def test_it_generally_works(self):
        response = self.client.get('/+projects/')

class ProjectPagesForProjectsWeDoNotHave(TwillTests):
    def test_for_page_we_do_have(self):
        # For a project that exists, we can render its page...
        project = mysite.search.models.Project.create_dummy(name='Twisted System')
        response = self.client.get('/+projects/Twisted%20System')
        self.assertContains(response, "Twisted System")

        # For a project that does not exist, we get a 404...
        response = self.client.get('/+projects/Nonexistent')
        self.assertEqual(response.status_code, 404)

        # For a project that does not exist, if we pass in ?creating=true,
        # then the page renders.
        response = self.client.get('/+projects/Nonexistent', {'creating': 'true'})
        self.assertContains(response, "Nonexistent")
