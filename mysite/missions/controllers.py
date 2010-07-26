from mysite.missions.models import Step, StepCompletion
from django.conf import settings

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

def get_mission_data_path():
    return os.path.join(os.path.dirname(__file__), 'data')

def set_mission_completed(profile, mission_name):
    StepCompletion.objects.get_or_create(person=profile, step=Step.objects.get(name=mission_name))

def mission_completed(profile, mission_name):
    return len(StepCompletion.objects.filter(step__name=mission_name, person=profile)) != 0


def remove_slash_that_python_two_point_five_might_have_added(some_string):
    if sys.version_info[:2] == (2, 5):
        # zomg, geez. Let's ditch Python 2.5 real soon now.
        # Not because it's busted necessarily, but just because we could
        # stop wasting time on inter-Python-version compatibility code like...
        if some_string[-1] == '/':
            return some_string[:-1]
    return some_string

class IncorrectTarFile(Exception):
    pass

class TarMission(object):
    WRAPPER_DIR_NAME = 'myproject-0.1'
    FILES = {
      'hello.c': '''#include <stdio.h>

int main(void)
{
  printf("Hello World\\n");
  return 0;
}
''',
      'Makefile': 'hello : hello.o\n'
    }

    @classmethod
    def check_tarfile(cls, tardata):
        """
        Validate that tardata is gzipped and contains the correct files in a wrapper directory.
        """
        try:
            tfile = tarfile.open(fileobj=StringIO(tardata), mode='r:gz')
        except tarfile.ReadError:
            raise IncorrectTarFile, 'Archive is not a valid gzipped tarball'

        # Check the filename list.
        filenames_wanted = [cls.WRAPPER_DIR_NAME] + [os.path.join(cls.WRAPPER_DIR_NAME, filename) for filename in cls.FILES.keys()]
        for member in tfile.getmembers():
            name_as_if_this_were_python_two_point_six = remove_slash_that_python_two_point_five_might_have_added(member.name)

            if '/' not in name_as_if_this_were_python_two_point_six:
                if name_as_if_this_were_python_two_point_six in cls.FILES.keys():
                    raise IncorrectTarFile, 'No wrapper directory is present'
                elif member.isdir() and name_as_if_this_were_python_two_point_six != cls.WRAPPER_DIR_NAME:
                    raise IncorrectTarFile, 'Wrapper directory name is incorrect: "%s"' % name_as_if_this_were_python_two_point_six
            if name_as_if_this_were_python_two_point_six not in filenames_wanted:
                raise IncorrectTarFile, 'An unexpected entry "%s" is present' % name_as_if_this_were_python_two_point_six
            filenames_wanted.remove(name_as_if_this_were_python_two_point_six)
            if name_as_if_this_were_python_two_point_six == cls.WRAPPER_DIR_NAME:
                if not member.isdir():
                    raise IncorrectTarFile, '"%s" should be a directory but is not' % name_as_if_this_were_python_two_point_six
            else:
                if not member.isfile():
                    raise IncorrectTarFile, 'Entry "%s" is not a file' % name_as_if_this_were_python_two_point_six
                if tfile.extractfile(member).read() != cls.FILES[name_as_if_this_were_python_two_point_six.split('/')[-1]]:
                    raise IncorrectTarFile, 'File "%s" has incorrect contents' % name_as_if_this_were_python_two_point_six
        if len(filenames_wanted) != 0:
            raise IncorrectTarFile, 'Archive does not contain all expected files (missing %s)' % (', '.join('"%s"' % f for f in filenames_wanted))

class UntarMission(object):
    TARBALL_DIR_NAME = 'ghello-0.4'
    TARBALL_NAME = TARBALL_DIR_NAME + '.tar.gz'
    FILE_WE_WANT = TARBALL_DIR_NAME + '/ghello.c'

    @classmethod
    def synthesize_tarball(cls):
        tdata = StringIO()
        tfile = tarfile.open(fileobj=tdata, mode='w:gz')
        tfile.add(os.path.join(get_mission_data_path(), cls.TARBALL_DIR_NAME), cls.TARBALL_DIR_NAME)
        tfile.close()
        return tdata.getvalue()

    @classmethod
    def get_contents_we_want(cls):
        '''Get the data for the file we want from the tarball.'''
        return open(os.path.join(get_mission_data_path(), cls.FILE_WE_WANT)).read()

class IncorrectPatch(Exception):
    pass

class SingleFilePatch(object):
    @classmethod
    def get_patch(cls):
        oldlines = open(cls.OLD_FILE).readlines()
        newlines = open(cls.NEW_FILE).readlines()
        return ''.join(difflib.unified_diff(oldlines, newlines, os.path.basename(cls.OLD_FILE), os.path.basename(cls.NEW_FILE)))

    @classmethod
    def validate_patch(cls, patchdata):
        the_patch = patch.fromstring(patchdata)
        # Check that it only patches one file.
        if len(the_patch.hunks) != 1:
            raise IncorrectPatch, 'The patch affects more than one file.'

        # Check that it will apply correctly to the file.
        if not the_patch._match_file_hunks(cls.OLD_FILE, the_patch.hunks[0]):
            raise IncorrectPatch, 'The patch will not apply correctly to the original file.'

        # Check that the resulting file matches what is expected.
        if ''.join(the_patch.patch_stream(open(cls.OLD_FILE), the_patch.hunks[0])) != open(cls.NEW_FILE).read():
            raise IncorrectPatch, 'The file resulting from patching does not have the correct contents.'

class PatchSingleFileMission(SingleFilePatch):
    OLD_FILE = os.path.join(get_mission_data_path(), 'fib1.c')
    NEW_FILE = os.path.join(get_mission_data_path(), 'fib2.c')
    # This does not correspond to a real file but is merely the filename the download is presented as.
    PATCH_FILENAME = 'fib-linear-time.patch'

class DiffSingleFileMission(SingleFilePatch):
    OLD_FILE = os.path.join(get_mission_data_path(), 'diffsingle.txt')
    NEW_FILE = os.path.join(get_mission_data_path(), 'diffsingle_result.txt')

class DiffRecursiveMission(object):
    ORIG_DIR = 'recipes'
    TARBALL_NAME = ORIG_DIR + '.tar.gz'
    SUBSTITUTIONS = [('aubergine', 'eggplant'),
                     ('Aubergine', 'Eggplant')]

    @classmethod
    def synthesize_tarball(cls):
        tdata = StringIO()
        tfile = tarfile.open(fileobj=tdata, mode='w:gz')
        tfile.add(os.path.join(get_mission_data_path(), cls.ORIG_DIR), cls.ORIG_DIR)
        tfile.close()
        return tdata.getvalue()

    @classmethod
    def validate_patch(cls, patchdata):
        the_patch = patch.fromstring(patchdata)

        # Strip one level of directories from the left of the filenames.
        for i, filename in enumerate(the_patch.source):
            if not '/' in filename:
                raise IncorrectPatch, 'Attempting to strip one level of slashes from header line "--- %s" left nothing.' % filename
            the_patch.source[i] = re.sub('^[^/]*/', '', filename)
        for i, filename in enumerate(the_patch.target):
            if not '/' in filename:
                raise IncorrectPatch, 'Attempting to strip one level of slashes from header line "+++ %s" left nothing.' % filename
            the_patch.target[i] = re.sub('^[^/]*/', '', filename)

        # Go through the files and check that ones that should be mentioned in the patch are so mentioned.
        path_to_mission_files = os.path.join(get_mission_data_path(), cls.ORIG_DIR)
        for filename in os.listdir(path_to_mission_files):
            full_filename = os.path.join(path_to_mission_files, filename)
            if not os.path.isfile(full_filename):
                continue

            old_contents = open(full_filename).read()
            new_contents = old_contents
            for old, new in cls.SUBSTITUTIONS:
                new_contents = new_contents.replace(old, new)
            if old_contents == new_contents:
                continue

            # So it's a file that the patch should modify.
            try:
                index = the_patch.source.index(filename)
            except ValueError:
                raise IncorrectPatch, 'Patch does not modify file "%s", which it should modify.' % filename
            if the_patch.target[index] != filename:
                raise IncorrectPatch, 'Patch headers for file "%s" have inconsistent filenames.' % filename

            hunks = the_patch.hunks[index]
            del the_patch.source[index]
            del the_patch.target[index]
            del the_patch.hunks[index]
            del the_patch.hunkends[index]

            # Check that it will apply correctly to the file.
            if not the_patch._match_file_hunks(full_filename, hunks):
                raise IncorrectPatch, 'The modifications to "%s" will not apply correctly to the original file.' % filename

            # Check that the resulting file matches what is expected.
            if ''.join(the_patch.patch_stream(StringIO(old_contents), hunks)) != new_contents:
                raise IncorrectPatch, 'The modifications to "%s" do not result in the correct contents. Make sure you replaced "Aubergine", too!' % filename

        if len(the_patch.source) != 0:
            raise IncorrectPatch, 'The patch modifies files that it should not modify: %s' % ', '.join(the_patch.source)

class PatchRecursiveMission(object):
    OLD_DIR = os.path.join(get_mission_data_path(), 'hats', 'before')
    NEW_DIR = os.path.join(get_mission_data_path(), 'hats', 'after')
    BASE_NAME = 'hats'
    ANSWERS = {'children_hats': 4, 'lizards_hats': 5}

    @classmethod
    def synthesize_tarball(cls):
        tdata = StringIO()
        tfile = tarfile.open(fileobj=tdata, mode='w:gz')
        tfile.add(cls.OLD_DIR, cls.BASE_NAME)
        tfile.close()
        return tdata.getvalue()

    @classmethod
    def get_patch(cls):
        patchfile = StringIO()
        for name in os.listdir(cls.OLD_DIR):
            oldname = os.path.join(cls.OLD_DIR, name)
            newname = os.path.join(cls.NEW_DIR, name)
            if not os.path.isfile(oldname):
                continue

            oldlines = open(oldname).readlines()
            newlines = open(newname).readlines()
            patchfile.writelines(difflib.unified_diff(oldlines, newlines, '%s-orig/%s' % (cls.BASE_NAME, name), '%s/%s' % (cls.BASE_NAME, name)))

        return patchfile.getvalue()

class SvnRepositoryManager(object):
    INITIAL_CONTENT = 'svn-initial.svndump'
    SECRET_WORD_FILE = 'word.txt'
    FILE_TO_BE_PATCHED_FOR_DIFF_MISSION = 'README'
    NEW_CONTENT_FOR_DIFF_MISSION = os.path.join(get_mission_data_path(), 'README-new-for-svn-diff')

    @classmethod
    def reset_repository(cls, username):
        repo_path = os.path.join(settings.SVN_REPO_PATH, username)
        if os.path.isdir(repo_path):
            shutil.rmtree(repo_path)
        subprocess.check_call(['svnadmin', 'create', '--fs-type', 'fsfs', repo_path])

        # Configure the repository so svnserve uses a password file stored within it.
        svnserve_conf_path = os.path.join(repo_path, 'conf', 'svnserve.conf')
        svnserve_conf = RawConfigParser()
        svnserve_conf.read(svnserve_conf_path)
        svnserve_conf.set('general', 'anon-access', 'read')
        svnserve_conf.set('general', 'auth-access', 'write')
        svnserve_conf.set('general', 'password-db', 'passwd')
        svnserve_conf.write(open(svnserve_conf_path, 'w'))

        # Assign a password for the user.
        password = otp.OTP().reformat(binascii.hexlify(os.urandom(8)), format='words').lower()
        passwd_path = os.path.join(repo_path, 'conf', 'passwd')
        passwd_file = RawConfigParser()
        passwd_file.read(passwd_path)
        passwd_file.set('users', username, password)
        passwd_file.write(open(passwd_path, 'w'))

        dumploader = subprocess.Popen(['svnadmin', 'load', '--ignore-uuid', repo_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        dumploader.communicate(open(os.path.join(get_mission_data_path(), cls.INITIAL_CONTENT)).read())
        if dumploader.returncode != 0:
            raise RuntimeError, 'svnadmin load failed'

    @classmethod
    def repository_exists(cls, username):
        return os.path.isdir(os.path.join(settings.SVN_REPO_PATH, username))

    @classmethod
    def repository_trunk_url(cls, username):
        return settings.SVN_REPO_URL_PREFIX + username + '/trunk'

    @classmethod
    def get_secret_word(cls, username):
        svn_path = 'file://' + os.path.join(settings.SVN_REPO_PATH, username, 'trunk', cls.SECRET_WORD_FILE)
        svn_cat = subprocess.Popen(['svn', 'cat', svn_path], stdout=subprocess.PIPE)
        word = svn_cat.stdout.read().strip()
        if svn_cat.wait() != 0:
            raise RuntimeError, 'svn cat failed'
        return word

    @classmethod
    def validate_diff_and_commit_if_ok(cls, username, diff):
        the_patch = patch.fromstring(diff)

        # Check that it only patches one file.
        if len(the_patch.hunks) != 1:
            raise IncorrectPatch, 'The patch affects more than one file.'

        # Check that the filename it patches is correct.
        if the_patch.source[0] != cls.FILE_TO_BE_PATCHED_FOR_DIFF_MISSION or the_patch.target[0] != cls.FILE_TO_BE_PATCHED_FOR_DIFF_MISSION:
            raise IncorrectPatch, 'The patch affects the wrong file.'

        # Now we need to generate a working copy to apply the patch to.
        # We can also use this working copy to commit the patch if it's OK.
        wcdir = tempfile.mkdtemp()
        try:
            trunk_file_url = 'file://' + os.path.join(settings.SVN_REPO_PATH, username, 'trunk')
            svncheckout = subprocess.Popen(['svn', 'co', trunk_file_url, wcdir], stdout=subprocess.PIPE)
            svncheckout.stdout.read()  # throw output on the floor
            if svncheckout.wait() != 0:
                raise RuntimeError, 'svn checkout of temporary working copy failed'
            file_to_patch = os.path.join(wcdir, cls.FILE_TO_BE_PATCHED_FOR_DIFF_MISSION)

            # Check that it will apply correctly to the working copy.
            if not the_patch._match_file_hunks(file_to_patch, the_patch.hunks[0]):
                raise IncorrectPatch, 'The patch will not apply correctly to the latest revision.'

            # Check that the resulting file matches what is expected.
            new_content = ''.join(the_patch.patch_stream(open(file_to_patch), the_patch.hunks[0]))
            if new_content != open(cls.NEW_CONTENT_FOR_DIFF_MISSION).read():
                raise IncorrectPatch, 'The file resulting from patching does not have the correct contents.'

            # Commit the patch.
            open(file_to_patch, 'w').write(new_content)
            svncommit = subprocess.Popen(['svn', 'commit', '-m', '''Fix a typo in %s.

Thanks for reporting this, %s!''' % (cls.FILE_TO_BE_PATCHED_FOR_DIFF_MISSION, username), '--username', 'mr_bad', wcdir], stdout=subprocess.PIPE)
            svncommit.stdout.read()  # throw output on the floor
            if svncommit.wait() != 0:
                raise RuntimeError, 'svn commit of patch failed'

        finally:
            shutil.rmtree(wcdir)
