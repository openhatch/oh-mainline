from unittest import TestCase
from mysite.base.tests import TwillTests
from mysite.missions.base import views, controllers
from mysite.missions.models import StepCompletion, Step
from mysite.profile.models import Person
from mysite.base.helpers import subproc_check_output
from django.conf import settings
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.test import TestCase as DjangoTestCase

import mock
import os
import tarfile
from StringIO import StringIO
import tempfile
import subprocess
import difflib
import shutil
import random

def make_testdata_filename(mission_type, filename):
    return os.path.join(os.path.dirname(__file__), '..', mission_type, 'testdata', filename)


class MainPageTests(TwillTests):
    fixtures = ['person-paulproteus', 'user-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_mission_completion_list_display(self):
        response = self.client.get(reverse(views.main_page))
        self.assertEqual(response.context['completed_missions'], {})

        paulproteus = Person.objects.get(user__username='paulproteus')
        StepCompletion(person=paulproteus, step=Step.objects.get(name='tar')).save()

        response = self.client.get(reverse(views.main_page))
        self.assertEqual(response.context['completed_missions'], {'tar': True})
