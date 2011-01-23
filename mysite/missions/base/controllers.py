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

from mysite.missions.models import Step, StepCompletion
from mysite.profile.models import Person
from django.conf import settings
from mysite.base.helpers import subproc_check_output

import tarfile
from StringIO import StringIO
import os
import sys
import difflib
import patch
import re
from ConfigParser import RawConfigParser
import subprocess
import shutil
import binascii
import otp
import tempfile
import pipes

def get_mission_data_path(mission_type):
    return os.path.join(os.path.dirname(__file__), '..', mission_type, 'data')

def set_mission_completed(profile, mission_name):
    StepCompletion.objects.get_or_create(person=profile, step=Step.objects.get(name=mission_name))

def unset_mission_completed(profile, mission_name):
    StepCompletion.objects.filter(person=profile, step=Step.objects.get(name=mission_name)).delete()

def mission_completed(profile, mission_name):
    return len(StepCompletion.objects.filter(step__name=mission_name, person=profile)) != 0


class IncorrectPatch(Exception):
    pass
