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

from mysite.missions.base.view_helpers import *

class SvnRepository(object):
    INITIAL_CONTENT = os.path.join(
        get_mission_data_path('svn'), 'svn-initial.svndump')

    def __init__(self, username):
        self.username = username
        self.repo_path = os.path.join(settings.SVN_REPO_PATH, username)

        self.file_url = 'file://' + self.repo_path
        self.public_url = settings.SVN_REPO_URL_PREFIX + username

    def reset(self):
        if os.path.isdir(self.repo_path):
            shutil.rmtree(self.repo_path)
        subprocess.check_call(
            ['svnadmin', 'create', '--fs-type', 'fsfs', self.repo_path])

        # Configure the repository so svnserve uses a password file stored
        # within it.
        svnserve_conf_path = os.path.join(
            self.repo_path, 'conf', 'svnserve.conf')
        svnserve_conf = RawConfigParser()
        svnserve_conf.read(svnserve_conf_path)
        svnserve_conf.set('general', 'anon-access', 'read')
        svnserve_conf.set('general', 'auth-access', 'write')
        svnserve_conf.set('general', 'password-db', 'passwd')
        svnserve_conf.write(open(svnserve_conf_path, 'w'))

        # Assign a password for the user.
        password = ' '.join(otp.OTP().reformat(binascii.hexlify(os.urandom(8)),
                            format='words').lower().split()[:3])
        passwd_path = os.path.join(self.repo_path, 'conf', 'passwd')
        passwd_file = RawConfigParser()
        passwd_file.read(passwd_path)
        passwd_file.set('users', self.username, password)
        passwd_file.write(open(passwd_path, 'w'))

        dumploader = subprocess.Popen(
            ['svnadmin', 'load', '--ignore-uuid', self.repo_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        dumploader.communicate(open(self.INITIAL_CONTENT).read())
        if dumploader.returncode != 0:
            raise RuntimeError, 'svnadmin load failed'

        # Install the pre-commit hook.
        precommit_hook_path = os.path.join(self.repo_path, 'hooks', 'pre-commit')
        open(precommit_hook_path, 'w').write('''#!/bin/sh -e
export PATH=%s
exec %s -W ignore %s svn_precommit "$@"
''' % (pipes.quote(os.environ['PATH']), pipes.quote(sys.executable), pipes.quote(settings.PATH_TO_MANAGEMENT_SCRIPT)))
        os.chmod(precommit_hook_path, 0755)

    def exists(self):
        return os.path.isdir(self.repo_path)

    def file_trunk_url(self):
        return self.file_url + '/trunk'

    def public_trunk_url(self):
        return self.public_url + '/trunk'

    def get_password(self):
        passwd_path = os.path.join(self.repo_path, 'conf', 'passwd')
        passwd_file = RawConfigParser()
        passwd_file.read(passwd_path)
        return passwd_file.get('users', self.username)

    def cat(self, path):
        return subproc_check_output(['svn', 'cat', self.file_url + path])


def get_username_for_svn_txn(repo_path, txn_id):
    """
    Returns username for an svn transaction.
    Helper function for hook scripts in the svn commit mission.
    This function may be mocked in the tests.
    """
    return subproc_check_output(['svnlook', 'author', repo_path, '-t', txn_id]).strip()


def get_changes_for_svn_txn(repo_path, txn_id):
    """
    Returns changes made in an svn transaction.
    Helper function for hook scripts in the svn commit mission.
    This function may be mocked in the tests.
    """
    changes = subproc_check_output(['svnlook', 'changed', repo_path, '-t', txn_id])

    # Formatting note for the svn change syntax
    # Lines are in the form:
    # <one letter for operation> <three spaces> <path in repository> <newline>
    # as in:
    #     "U    trunk/README\n"
    for line in StringIO(changes):
        yield line[0], line[4:-1]


def get_file_for_svn_txn(repo_path, txn_id, filename):
    """
    Returns file in an svn transaction.
    Helper function for hook scripts in the svn commit mission.
    This function may be mocked in the tests.
    """
    return subproc_check_output(['svnlook', 'cat', repo_path, '-t', txn_id, filename])


def get_log_for_svn_txn(repo_path, txn_id):
    """
    Returns svn log for an svn transaction.
    Helper function for hook scripts in the svn commit mission.
    This function may be mocked in the tests.
    """
    return subproc_check_output(['svnlook', 'log', repo_path, '-t', txn_id])


class SvnCommitMission(object):
    SECRET_WORD_FILE = 'word.txt'
    NEW_SECRET_WORD = 'plenipotentiary'
    FILE_TO_BE_PATCHED = 'README'
    NEW_CONTENT = os.path.join(get_mission_data_path('svn'),
                               'README-new-for-svn-commit')

    @classmethod
    def pre_commit_hook(cls, repo_path, txn_id):
        """
        This method performs checks to see if a proposed changes are correct
        and ready to commit into svn
        :param repo_path:
        :param txn_id:
        :return:
        """
        username = get_username_for_svn_txn(repo_path, txn_id)

        # If 'mr_bad' is the username for the commit, then return successful
        # pre-commit hook which will then allow auto-commit the diff mission
        if username == 'mr_bad':
            return

        # Checks if a user has completed the svn diff mission
        person = Person.objects.get(user__username=username)
        if not mission_completed(person, 'svn_diff'):
            raise IncorrectPatch, 'The svn diff mission must be completed before the svn commit mission.'

        # Checks if the correct files are modified for svn commit mission
        paths_that_should_be_modified = ['trunk/' + cls.SECRET_WORD_FILE,
                                         'trunk/' + cls.FILE_TO_BE_PATCHED]
        for action, path in get_changes_for_svn_txn(repo_path, txn_id):
            if action != 'U':
                raise IncorrectPatch, 'No files should have been added or removed.'
            if path not in paths_that_should_be_modified:
                raise IncorrectPatch, 'File "%s" should not have been modified.' % path
            paths_that_should_be_modified.remove(path)

        if len(paths_that_should_be_modified):
            raise IncorrectPatch, 'File "%s" should have been modified.' % paths_that_should_be_modified[0]

        # Checks if the secret word is correctly changed in commit mission
        if get_file_for_svn_txn(repo_path, txn_id, 'trunk/' + cls.SECRET_WORD_FILE).strip() != cls.NEW_SECRET_WORD:
            raise IncorrectPatch, 'The new secret word is incorrect.'

        # Checks if the other patched file's content is correct
        if get_file_for_svn_txn(repo_path, txn_id, 'trunk/' + cls.FILE_TO_BE_PATCHED) != open(cls.NEW_CONTENT).read():
            raise IncorrectPatch, 'The new content of %s is incorrect.' % cls.FILE_TO_BE_PATCHED

        # Checks if there is a log message for a successful commit
        if get_log_for_svn_txn(repo_path, txn_id).strip() == '':
            raise IncorrectPatch, 'No log message was provided.'

        # After all checks have passed, set the commit mission to completed
        set_mission_completed(person, 'svn_commit')
