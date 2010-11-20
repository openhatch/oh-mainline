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
