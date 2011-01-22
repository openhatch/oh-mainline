# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch
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
import logging
import sys

from django.core.management.base import BaseCommand

import mysite.profile.models

class Command(BaseCommand):
    help = "Reads a session ID on stdin, and prints an email address for the person."

    def handle(self, *args, **options):
        for session_id in sys.stdin:
            p = mysite.profile.models.Person.get_from_session_key(session_id.strip())
            print '"' + p.get_full_name_or_username() + '"',
            print '<' + p.user.email + '>'
