# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2010 Jessica McKellar
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

import difflib
import os.path
from cStringIO import StringIO
import re
import tarfile

from mysite.missions.base.controllers import (
    IncorrectPatch,
    patch,
    get_mission_data_path)

class SingleFilePatch(object):
    @classmethod
    def get_patch(cls):
        oldlines = open(cls.OLD_FILE).readlines()
        newlines = open(cls.NEW_FILE).readlines()
        return ''.join(difflib.unified_diff(oldlines, newlines, os.path.basename(cls.OLD_FILE), os.path.basename(cls.NEW_FILE)))

    @classmethod
    def validate_patch(cls, patchdata):
        the_patch = patch.fromstring(patchdata)

        # If we couldn't create even 1 hunk, the patch headers are missing.
        if not the_patch.hunks:
            raise IncorrectPatch, 'The file resulting from patching does not have the correct contents. \
        Make sure you are including the diff headers (those --- and +++ and @@ lines).'

        # Check that it only patches one file.
        if len(the_patch.hunks) != 1:
            raise IncorrectPatch, 'The patch affects more than one file.'

        # Check if the diff is in the wrong order.
        if ''.join(the_patch.patch_stream(open(cls.NEW_FILE), the_patch.hunks[0])) == open(cls.OLD_FILE).read():
            raise IncorrectPatch, 'It looks like the order of files passed to diff was flipped. \
        To generate a diff representing the changes you made to originalfile.txt \
        to get to modifiedfile.txt, do "diff -u originalfile.txt modifiedfile.txt".'

        # Check that it will apply correctly to the file.
        #if not the_patch._match_file_hunks(cls.OLD_FILE, the_patch.hunks[0]):
        #   raise IncorrectPatch, 'The patch will not apply correctly to the original file.'


        # Check that the resulting file matches what is expected.
        if ''.join(the_patch.patch_stream(open(cls.OLD_FILE), the_patch.hunks[0])) == open(cls.NEW_FILE).read():
            # Sweet! Success.
            return True

        # Okay, at this point, we know the resulting contents are not good.

        # Maybe the problem is that the user accidentally removed
        # line-ending whitespace from the patch file. We detect that
        # by seeing if \n\n appears in the patch file.
        if '\n\n' in patchdata:
            raise IncorrectPatch, 'You seem to have removed the space (" ") characters at the end of some lines. Those are essential to the patch format'

        # Otherwise, we give a generic error message.
        raise IncorrectPatch, 'The file resulting from patching does not have the correct contents.'

class PatchSingleFileMission(SingleFilePatch):
    OLD_FILE = os.path.join(get_mission_data_path('diffpatch'), 'fib1.c')
    NEW_FILE = os.path.join(get_mission_data_path('diffpatch'), 'fib2.c')
    # This does not correspond to a real file but is merely the filename the download is presented as.
    PATCH_FILENAME = 'fib-linear-time.patch'

class DiffSingleFileMission(SingleFilePatch):
    OLD_FILE = os.path.join(get_mission_data_path('diffpatch'), 'diffsingle.txt')
    NEW_FILE = os.path.join(get_mission_data_path('diffpatch'), 'diffsingle_result.txt')

class DiffRecursiveMission(object):
    ORIG_DIR = 'recipes'
    TARBALL_NAME = ORIG_DIR + '.tar.gz'
    SUBSTITUTIONS = [('aubergine', 'eggplant'),
                     ('Aubergine', 'Eggplant')]
    ALTERNATE_FILENAMES = {'Skillet.txt': 'AubergineAndChickpeaSkillet.txt',
                           'Grilled.txt': 'GrilledAubergine.txt'}

    @staticmethod
    def name_new2old(s):
        for new_name in DiffRecursiveMission.ALTERNATE_FILENAMES:
            old_name = DiffRecursiveMission.ALTERNATE_FILENAMES[
                new_name]
            if s.endswith('/' + new_name):
                return s.replace('/' + new_name, '/' + old_name, 1)
            if s == new_name:
                return old_name
        return s

    @staticmethod
    def name_old2new(s):
        for new_name in DiffRecursiveMission.ALTERNATE_FILENAMES:
            old_name = DiffRecursiveMission.ALTERNATE_FILENAMES[
                new_name]
            if s.endswith('/' + old_name):
                return s.replace('/' + old_name, '/' + new_name, 1)
            if s == old_name:
                return new_name
        return s

    @classmethod
    def synthesize_tarball(cls):
        tdata = StringIO()
        tfile = tarfile.open(fileobj=tdata, mode='w:gz')
        tfile.add(os.path.join(get_mission_data_path('diffpatch'), cls.ORIG_DIR), cls.ORIG_DIR)
        tfile.close()
        return tdata.getvalue()

    @classmethod
    def validate_patch(cls, patchdata):
        the_patch = patch.fromstring(patchdata)

        # Strip one level of directories from the left of the filenames.
        for i, filename in enumerate(the_patch.source):

            if not '/' in filename:
                raise IncorrectPatch, 'Attempting to strip one level of slashes from header line "--- %s" left nothing.' % filename
            the_patch.source[i] = re.sub('^[^/]*/+', '', filename)
        for i, filename in enumerate(the_patch.target):
            if not '/' in filename:
                raise IncorrectPatch, 'Attempting to strip one level of slashes from header line "+++ %s" left nothing.' % filename
            the_patch.target[i] = re.sub('^[^/]*/+', '', filename)

        # Go through the files and check that ones that should be mentioned in the patch are so mentioned.
        path_to_mission_files = os.path.join(get_mission_data_path('diffpatch'), cls.ORIG_DIR)
        for filename in os.listdir(path_to_mission_files):
            old_style_filename = filename
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
                # Hmm. The user submitted some file with a filename
                # we didn't really recognize.
                #
                # We did rename a bunch of the files a little while ago.
                # Maybe we can process their submission anyway by looking for
                # the old filename in the patch header.
                old_style_filename = DiffRecursiveMission.name_new2old(filename)
                try:
                    index = the_patch.source.index(old_style_filename)
                except ValueError:
                    raise IncorrectPatch, 'Patch does not modify file "%s", which it should modify.' % filename

            if (the_patch.target[index] != filename and
                the_patch.target[index] != old_style_filename):
                raise IncorrectPatch, 'Patch headers for file "%s" have inconsistent filenames.' % filename

            hunks = the_patch.hunks[index]
            del the_patch.source[index]
            del the_patch.target[index]
            del the_patch.hunks[index]
            del the_patch.hunkends[index]

            # Check that it will apply correctly to the file.
            if not the_patch._match_file_hunks(full_filename, hunks):

                # Check for reverse patch by seeing if there is "-firstSubstitute" and "+firstOriginal" in the diff.
                # (If they did everything perfectly and reversed the patch, there will be two lines following these conditions)
                if patchdata.find('-'+ cls.SUBSTITUTIONS[1][1]) != -1 and patchdata.find('+'+ cls.SUBSTITUTIONS[1][0]) != -1:
                    raise IncorrectPatch, 'You submitted a patch that would revert the correct changes back to the originals.  You may have mixed the parameters for diff, or performed a reverse patch.'
                else:
                    raise IncorrectPatch, 'The modifications to "%s" will not apply correctly to the original file.' % filename

            # Check for BOM issues.  Likely a Windows-only issue, and only when using a text editor that
            # includes UTF-8 BOM markers when saving files.
            if '\xef\xbb\xbf' in ''.join(the_patch.patch_stream(StringIO(old_contents),hunks)):
                raise IncorrectPatch, 'It appears the text editor you used to modify "%s" leaves UTF-8 BOM characters.  Try an editor like Notepad++ or something similar.' % filename

            # Check that the resulting file matches what is expected.
            if ''.join(the_patch.patch_stream(StringIO(old_contents), hunks)) != new_contents:
                raise IncorrectPatch, 'The modifications to "%s" do not result in the correct contents. Make sure you replaced "Aubergine", too!' % filename

        if len(the_patch.source) != 0:
            raise IncorrectPatch, 'The patch modifies files that it should not modify: %s' % ', '.join(the_patch.source)

class PatchRecursiveMission(object):
    OLD_DIR = os.path.join(get_mission_data_path('diffpatch'), 'hats', 'before')
    NEW_DIR = os.path.join(get_mission_data_path('diffpatch'), 'hats', 'after')
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
            patchfile.writelines(difflib.unified_diff(oldlines, newlines, 'a/%s/%s' % (cls.BASE_NAME, name), 'b/%s/%s' % (cls.BASE_NAME, name)))

        return patchfile.getvalue()
