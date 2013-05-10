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

from mysite.missions.base.view_helpers import (
    IncorrectPatch,
    patch,
    get_mission_data_path)

class SingleFilePatch(object):
    @classmethod
    def get_patch(cls):
        oldlines = open(cls.OLD_FILE).readlines()
        newlines = open(cls.NEW_FILE).readlines()
        return ''.join(difflib.unified_diff(oldlines, newlines, os.path.basename(cls.OLD_FILE), os.path.basename(cls.NEW_FILE)))

    @staticmethod
    def apply_patch(patch_obj, hunks, base_filename):
        with open(base_filename, 'rb') as f:
            lines = patch_obj.patch_stream(f, hunks)
            return ''.join(lines)

    @classmethod
    def validate_patch(cls, patchdata):
        CORRECT_CONTENTS = open(cls.NEW_FILE).read()
        the_patch = patch.fromstring(patchdata)

        # the_patch.hunks now contains a list of lists.

        # For each file that appears in the patch file, there is a
        # list of hunks (patch changesets) that apply to that file.

        # If patch.fromstring() indicates that the patch affects zero files,
        # then the_patch.hunks will be a zero-length list.
        if not the_patch.hunks:
            raise IncorrectPatch, 'The file resulting from patching does not have the correct contents. \
        Make sure you are including the diff headers (those --- and +++ and @@ lines; You might want to look at the "Medium" hint.)'

        # If it affects more than one file, then that would be a
        # mistake as well.
        if len(the_patch.hunks) > 1:
            raise IncorrectPatch, 'The patch affects more than one file.'

        # So now we can grab just the relevant hunks.
        hunks = the_patch.hunks[0]

        # Is the diff reversed?
        text_when_patch_applied_in_reverse = SingleFilePatch.apply_patch(
            the_patch, hunks, cls.NEW_FILE)
        if text_when_patch_applied_in_reverse == open(cls.OLD_FILE).read():
            raise IncorrectPatch, 'It looks like the order of files passed to diff was flipped. \
        To generate a diff representing the changes you made to originalfile.txt \
        to get to modifiedfile.txt, do "diff -u originalfile.txt modifiedfile.txt".'

        # Check that it will apply correctly to the file.
        #if not the_patch._match_file_hunks(cls.OLD_FILE, the_patch.hunks[0]):
        #   raise IncorrectPatch, 'The patch will not apply correctly to the original file.'

        resulting_contents = SingleFilePatch.apply_patch(
            the_patch, hunks, cls.OLD_FILE)
        # Are the results just totally perfect?
        if resulting_contents == CORRECT_CONTENTS:
            # Sweet! Success.
            return True

        # Okay, at this point, we know the resulting contents are not good.

        # Maybe the problem is that the user accidentally removed
        # line-ending whitespace from the patch file. We detect that
        # by seeing if \n\n appears in the patch file.
        if '\n\n' in patchdata or '\r\n\r\n' in patchdata:
            raise IncorrectPatch, 'You seem to have removed the space (" ") characters at the end of some lines. Those are essential to the patch format. If you are a Windows user, check the hints on how to copy and paste from the terminal.'

        # Otherwise, we give a generic error message.
        raise IncorrectPatch, 'The file resulting from patching does not have the correct contents.'

class PatchSingleFileMission(SingleFilePatch):
    OLD_FILE = os.path.join(get_mission_data_path('diffpatch'), 'oven-pancake.txt')
    NEW_FILE = os.path.join(get_mission_data_path('diffpatch'), 'oven-pancake_result.txt')
    # This does not correspond to a real file but is merely the filename the download is presented as.
    PATCH_FILENAME = 'add-oven-temp.patch'

class DiffSingleFileMission(SingleFilePatch):
    OLD_FILE = os.path.join(get_mission_data_path('diffpatch'), 'nutty-pancake.txt')
    NEW_FILE = os.path.join(get_mission_data_path('diffpatch'), 'nutty-pancake_result.txt')

class DiffRecursiveMission(object):
    ORIG_DIR = 'recipes'
    TARBALL_NAME = ORIG_DIR + '.tar.gz'
    SUBSTITUTIONS = [('aubergine', 'eggplant'),
                     ('Aubergine', 'Eggplant')]
    ALTERNATE_FILENAMES = {'Skillet.txt': 'AubergineAndChickpeaSkillet.txt'}

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

    @staticmethod
    def strip_filename_one_path_level(filename):
        if not '/' in filename:
            raise IncorrectPatch, 'Attempting to strip one level of slashes from "%s" left nothing.' % filename
        return re.sub('^[^/]*/+', '', filename)

    @staticmethod
    def check_for_leading_dot_slash_in_filename(filename):
        if filename.startswith("./"):
            raise IncorrectPatch, 'The diff you submitted will not apply properly because it has filename(s) starting with "./". Make sure that when you run the diff command, you do not add unnecessary "./" path prefixes. This is important because it affects the arguments needed to run the patch command for whoever applies the patch.'

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
            cls.check_for_leading_dot_slash_in_filename(filename)
            the_patch.source[i] = cls.strip_filename_one_path_level(filename)
        for i, filename in enumerate(the_patch.target):
            cls.check_for_leading_dot_slash_in_filename(filename)
            the_patch.target[i] = cls.strip_filename_one_path_level(filename)

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
                # A file the user was supposed to modify was not included in
                # the patch.
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
    OLD_DIR = os.path.join(get_mission_data_path('diffpatch'), 'recipes')
    NEW_DIR = os.path.join(get_mission_data_path('diffpatch'), 'recipes.more-garlic')
    BASE_NAME = 'recipes'
    ANSWERS = {'amount_of_garlic': 3}

    # NOTE: You should rely on the DiffRecursiveMission for the tarball.

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
