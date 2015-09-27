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

import sys

from django.core.management import BaseCommand, CommandError
from mysite.missions.git import view_helpers


class Command(BaseCommand):
    args = '<username>'
    help = 'Determine whether the git repository for a user exists'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError, 'Exactly one argument expected.'
        username, = args

        if not view_helpers.GitRepository(username).exists():
            sys.exit(1)
