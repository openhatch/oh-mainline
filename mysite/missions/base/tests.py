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

import mock
import os
import tarfile
from StringIO import StringIO
import tempfile
import subprocess
import difflib
import shutil
import random
from unittest import TestCase

from django.conf import settings
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.test import TestCase as DjangoTestCase

from mysite.base.tests import TwillTests
from mysite.missions.base import views
import mysite.missions.base.view_helpers
from mysite.missions.models import StepCompletion, Step
from mysite.profile.models import Person
from mysite.base.view_helpers import subproc_check_output


def get_mission_test_data_path(mission_type):
    """ Returns an absolute path to test data """
    base_path = os.path.abspath(os.path.dirname(__file__))
    new_path = os.path.join(base_path, '..', mission_type, 'test_data')
    absolute_ified = os.path.abspath(new_path)
    return absolute_ified

def make_testdata_filename(mission_type, filename):
    """ Create a filename for test data and join to path """
    return os.path.join(os.path.dirname(__file__), '..', mission_type,
                        'testdata', filename)

def list_of_true_keys(d):
    """ Maintain a list of valid true keys """
    ret = []
    for key in d:
        if d[key]:
            ret.append(key)
    return ret


class MainPageTests(TwillTests):
    """ Tests for the main mission landing and status page """

    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_mission_completion_list_display(self):
        """
        Ensure mission completion states match the actual state
        of mission states displayed
        """
        response = self.client.get(reverse(views.main_page))
        self.assertFalse(
            list_of_true_keys(response.context['completed_missions']))

        # Set the individual tar mission to completed
        paulproteus = Person.objects.get(user__username='paulproteus')
        StepCompletion(person=paulproteus,
                       step=Step.objects.get(name='tar')).save()

        # Return to main mission view and check if tar is completed
        response = self.client.get(reverse(views.main_page))
        self.assertEqual(['tar'], list_of_true_keys(
            response.context['completed_missions']))
