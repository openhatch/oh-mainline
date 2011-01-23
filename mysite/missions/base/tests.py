# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
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
