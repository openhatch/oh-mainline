# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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

from mysite.missions.tar.tests import *
from mysite.missions.diffpatch.tests import *
from mysite.missions.svn.tests import *
from mysite.missions.git.tests import *
import datetime


import django.test
from mysite.missions.base.view_helpers import *
from mysite.missions.models import Step, StepCompletion
from mysite.profile.models import Person


class MissionCompletionTestCase(django.test.TestCase):
    fixtures = ['user-paulproteus.json', 'person-paulproteus.json']

    def test_unset_mission_completed_sets_is_currently_completed_to_false(self):
        """When user unsets step completion
        'StepCompletion' object 'is_currently_completed' param becomes true"""
        profile = Person.objects.all()[0]
        step = Step.objects.all()[0]
        # creates StepCompletion object
        set_mission_completed(profile, step.name)

        unset_mission_completed(profile, step.name)
        obj_after = StepCompletion.objects.get(person=profile, step=step)

        self.assertTrue(mission_completed_at_least_once(profile, step.name))
        self.assertFalse(mission_completed(profile, step.name))
        self.assertFalse(obj_after.is_currently_completed)

        obj_after.delete()

    def test_set_mission_completed_sets_is_currently_completed_to_true(self):
        profile = Person.objects.all()[0]
        step = Step.objects.all()[0]

        set_mission_completed(profile, step.name)
        # sets StepCompletion.is_currently_completed to True
        unset_mission_completed(profile, step.name)
        # should make StepCompletion.is_currently_completed False again
        set_mission_completed(profile, step.name)
        obj_after = StepCompletion.objects.get(person=profile, step=step)

        self.assertTrue(mission_completed(profile, step.name))
        self.assertTrue(obj_after.is_currently_completed)

    def test_set_mission_completed_records_first_completed_time(self):
        now = datetime.datetime.now()
        profile = Person.objects.all()[0]
        step = Step.objects.all()[0]

        set_mission_completed(profile, step.name)
        # sets StepCompletion.is_currently_completed to True

        # Simulate the user resetting the mission
        obj_after = StepCompletion.objects.get(person=profile, step=step)

        self.assertGreater(obj_after.created_date, now)
        self.assertGreater(obj_after.modified_date, now)

        modified_date = obj_after.modified_date
        created_date = obj_after.created_date

        # And if we set it again... modified_date should increase,
        # but not created_date.
        unset_mission_completed(profile, step.name)
        obj_after = StepCompletion.objects.get(person=profile, step=step)
        self.assertGreater(obj_after.modified_date, modified_date)
        self.assertEqual(obj_after.created_date, created_date)
