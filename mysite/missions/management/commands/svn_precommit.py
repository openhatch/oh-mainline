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

from django.core.management import BaseCommand, CommandError
from mysite.missions.svn import view_helpers
from mysite.base.unicode_sanity import utf8
import sys

class Command(BaseCommand):
    args = '<repo_path> <txn_id>'
    help = 'SVN pre-commit hook for mission repositories'

    def handle(self, *args, **options):
        # This management command is called from the mission svn repositories
        # as the pre-commit hook.  It receives the repository path and transaction
        # ID as arguments, and it receives a description of applicable lock
        # tokens on stdin.  Its environment and current directory are undefined.
        if len(args) != 2:
            raise CommandError, 'Exactly two arguments are expected.'
        repo_path, txn_id = args

        try:
            view_helpers.SvnCommitMission.pre_commit_hook(repo_path, txn_id)
        except view_helpers.IncorrectPatch, e:
            sys.stderr.write('\n    ' + utf8(e) + '\n\n')
            raise CommandError, 'The commit failed to validate.'
