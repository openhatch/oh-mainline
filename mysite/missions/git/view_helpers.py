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

import mysite.base.unicode_sanity
from mysite.missions.base.view_helpers import *


class GitRepository(object):

    def __init__(self, username):
        self.username = username
        self.repo_path = os.path.join(settings.GIT_REPO_PATH, username)
        self.file_url = 'file://' + self.repo_path
        self.public_url = settings.GIT_REPO_URL_PREFIX + username

    def reset(self):
        if os.path.isdir(self.repo_path):
            shutil.rmtree(self.repo_path)
        subprocess.check_call(['git', 'init', self.repo_path])
        subprocess.check_call(
            ['git', 'config', 'user.name', '"The Brain"'], cwd=self.repo_path)
        subprocess.check_call(
            ['cp', '../../../missions/git/data/hello.py', '.'], cwd=self.repo_path)
        subprocess.check_call(['git', 'add', '.'], cwd=self.repo_path)
        subprocess.check_call(
            ['git', 'commit', '-m', '"Initial commit"'], cwd=self.repo_path)

        # Touch the git-daemon-export-ok file
        file_obj = file(
            os.path.join(self.repo_path, '.git', 'git-daemon-export-ok'), 'w')
        file_obj.close()

        person = Person.objects.get(user__username=self.username)

    def exists(self):
        return os.path.isdir(self.repo_path)


class GitDiffMission(object):

    @classmethod
    def commit_if_ok(cls, username, diff):
        repo = GitRepository(username)
        commit_diff = subprocess.Popen(
            ['git', 'am'], cwd=repo.repo_path, stdin=subprocess.PIPE)
        commit_diff.communicate(mysite.base.unicode_sanity.utf8(diff))
        if commit_diff.returncode == 0:  # for shell commands, success is 0
            commit_msg = """Fixed a terrible mistake. Thanks for reporting this %s.

         Come to my house for a dinner party.
         Knock 3 times and give the secret password: Pinky.""" % username
            subprocess.Popen(
                ['git', 'commit', '--allow-empty', '-m', commit_msg], cwd=repo.repo_path)
            return True
        else:
            subprocess.check_call(['git', 'am', '--abort'], cwd=repo.repo_path)
            return False
