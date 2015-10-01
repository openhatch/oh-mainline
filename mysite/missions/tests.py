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

import datetime

import django.db
import django.test
from django.utils.unittest import skipIf

from mysite.missions.base.view_helpers import *
from mysite.missions.models import Step, StepCompletion
from mysite.profile.models import Person

from mysite.missions.tar.tests import *
from mysite.missions.diffpatch.tests import *
from mysite.missions.svn.tests import *
from mysite.missions.git.tests import *
from mysite.missions.pipvirtualenv.tests import *
from mysite.missions.shell.tests import *


class MissionCompletionTestCase(django.test.TestCase):
    fixtures = ['user-paulproteus.json', 'person-paulproteus.json']

    def test_unset_mission_completed_sets_is_currently_completed_to_false(self):
        """Ensure unset mission completed if a step is not completed or reset"""
        # set up
        profile = Person.objects.all()[0]
        step = Step.objects.all()[0]
        set_mission_completed(profile, step.name)

        # execute test
        unset_mission_completed(profile, step.name)
        obj_after = StepCompletion.objects.get(person=profile, step=step)
        self.assertTrue(mission_completed_at_least_once(profile, step.name))
        self.assertFalse(mission_completed(profile, step.name))
        self.assertFalse(obj_after.is_currently_completed)

        # clean up
        obj_after.delete()

    def test_set_mission_completed_sets_is_currently_completed_to_true(self):
        """Ensure mission completed is set if all steps are completed"""
        profile = Person.objects.all()[0]
        step = Step.objects.all()[0]
        set_mission_completed(profile, step.name)
        unset_mission_completed(profile, step.name)
        set_mission_completed(profile, step.name)
        obj_after = StepCompletion.objects.get(person=profile, step=step)

        self.assertTrue(mission_completed(profile, step.name))
        self.assertTrue(obj_after.is_currently_completed)

    def test_set_mission_completed_records_first_completed_time(self):
        """
        Ensure that mission created time remains unchanged and modified time
        increases when a completed mission is unset and completed again.
        """
        # set up
        now = datetime.datetime.now()
        profile = Person.objects.all()[0]
        step = Step.objects.all()[0]

        # set mission completed. check if time completed greater than start time
        set_mission_completed(profile, step.name)
        obj_after = StepCompletion.objects.get(person=profile, step=step)
        self.assertGreater(obj_after.created_date, now)
        self.assertGreater(obj_after.modified_date, now)

        # store datetime before unsetting and reseting mission completed
        modified_date = obj_after.modified_date
        created_date = obj_after.created_date

        # unset and set mission completed again
        unset_mission_completed(profile, step.name)
        obj_after = StepCompletion.objects.get(person=profile, step=step)
        # ensure modified time is greater and created time unchanged
        self.assertGreater(obj_after.modified_date, modified_date)
        self.assertEqual(obj_after.created_date, created_date)
