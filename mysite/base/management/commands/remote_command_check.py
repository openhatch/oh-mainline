# This file is part of OpenHatch.
# Copyright (C) 2015 OpenHatch, Inc.
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

import os
import subprocess

from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError


VALID_COMMANDS = (['milestone-a/manage.py', 'git_reset'], ['milestone-a/manage.py', 'git_exists'],
    ['milestone-a/manage.py', 'svn_reset'], ['milestone-a/manage.py', 'svn_exists'],
)


class Command(BaseCommand):
    args = '<username>'
    help = 'Initialize the git repository for a user'

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError, 'Command takes no arguments.'

        command = os.environ['SSH_ORIGINAL_COMMAND'].split()
        if command[:-1] not in VALID_COMMANDS:
            raise CommandError, 'Permission denied.'

        # Make sure the user exists.
        User.objects.get(username=command[-1])

        subprocess.check_call(command)
