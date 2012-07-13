# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 Jessica McKellar
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

import tempfile
import os
import subprocess
from StringIO import StringIO
import difflib
import tarfile
import shutil

from mysite.missions.base.tests import (
    TwillTests,
    Person,
    reverse,
    StepCompletion,
    )
from mysite.base.unicode_sanity import utf8
from mysite.missions.diffpatch import views, controllers

class PatchSingleFileTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_generated_patch(self):
        oldfile = tempfile.NamedTemporaryFile(delete=False)
        file_to_patch = oldfile.name

        try:
            oldfile.write(open(controllers.PatchSingleFileMission.OLD_FILE).read())
            oldfile.close()

            patch_process = subprocess.Popen(['patch', file_to_patch], stdin=subprocess.PIPE)
            patch_process.communicate(controllers.PatchSingleFileMission.get_patch())
            self.assertEqual(patch_process.returncode, 0)

            self.assertEqual(open(file_to_patch).read(), open(controllers.PatchSingleFileMission.NEW_FILE).read())

        finally:
            os.unlink(file_to_patch)


    def test_downloads_of_needed_files(self):
        orig_response = self.client.get(reverse(views.patchsingle_get_original_file))
        self.assert_(orig_response['Content-Disposition'].startswith('attachment'))
        patch_response = self.client.get(reverse(views.patchsingle_get_patch))
        self.assert_(patch_response['Content-Disposition'].startswith('attachment'))

    def test_do_mission_correctly(self):
        oldfile = tempfile.NamedTemporaryFile(delete=False)
        file_to_patch = oldfile.name

        try:
            orig_response = self.client.get(reverse(views.patchsingle_get_original_file))
            oldfile.write(orig_response.content)
            oldfile.close()

            patch_response = self.client.get(reverse(views.patchsingle_get_patch))
            patch_process = subprocess.Popen(['patch', file_to_patch], stdin=subprocess.PIPE)
            patch_process.communicate(patch_response.content)
            self.assertEqual(patch_process.returncode, 0)

            submit_response = self.client.post(reverse(views.patchsingle_submit), {'patched_file': open(file_to_patch)})
            self.assert_(submit_response.context['patchsingle_success'])

            paulproteus = Person.objects.get(user__username='paulproteus')
            self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchsingle', person=paulproteus)), 1)

        finally:
            os.unlink(file_to_patch)

    def test_do_mission_incorrectly(self):
        patched_file = StringIO('Some arbitrary contents so the file is incorrect.')
        patched_file.name = 'foo.c'
        submit_response = self.client.post(reverse(views.patchsingle_submit), {'patched_file': patched_file})
        self.assertFalse(submit_response.context['patchsingle_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchsingle', person=paulproteus)), 0)


class DiffSingleFileTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def make_good_patch(self):
        oldlines = open(controllers.DiffSingleFileMission.OLD_FILE).readlines()
        newlines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()
        return ''.join(difflib.unified_diff(oldlines, newlines, 'old.txt', 'new.txt'))

    def make_wrong_src_patch(self):
        # Make a patch that will not apply correctly.
        oldlines = open(controllers.DiffSingleFileMission.OLD_FILE).readlines()
        newlines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()
        del oldlines[0]
        return ''.join(difflib.unified_diff(oldlines, newlines, 'old.txt', 'new.txt'))

    def make_patch_without_trailing_whitespace(self):
        # Make a patch that will not apply correctly.
        good_patch = self.make_good_patch()
        lines = good_patch.split('\n')
        output_lines = []
        for line in lines:
            output_lines.append(line.rstrip())
        return '\n'.join(output_lines)

    def make_wrong_dest_patch(self):
        # Make a patch that will apply correctly but does not result in the right file.
        oldlines = open(controllers.DiffSingleFileMission.OLD_FILE).readlines()
        newlines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()
        del newlines[0]
        return ''.join(difflib.unified_diff(oldlines, newlines, 'old.txt', 'new.txt'))

    def make_swapped_patch(self):
        # make a backwards diff.
        oldlines = open(controllers.DiffSingleFileMission.OLD_FILE).readlines()
        newlines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()
        return ''.join(difflib.unified_diff(newlines, oldlines, 'new.txt', 'old.txt'))

    def test_good_patch(self):
        controllers.DiffSingleFileMission.validate_patch(self.make_good_patch())

    def test_not_single_file(self):
        try:
            controllers.DiffSingleFileMission.validate_patch(self.make_good_patch() * 2)
        except controllers.IncorrectPatch, e:
            self.assert_('affects more than one file' in utf8(e))
        else:
            self.fail('no exception raised')

    #def test_does_not_apply_correctly(self):
    #    try:
    #        controllers.DiffSingleFileMission.validate_patch(self.make_wrong_src_patch())
    #    except controllers.IncorrectPatch, e:
    #        self.assert_('will not apply' in utf8(e))
    #    else:
    #        self.fail('no exception raised')

    def test_produces_wrong_file(self):
        try:
            controllers.DiffSingleFileMission.validate_patch(self.make_wrong_dest_patch())
        except controllers.IncorrectPatch, e:
            self.assert_('does not have the correct contents' in utf8(e))
        else:
            self.fail('no exception raised')

    def test_backwards_diff(self):
        """
        A backwards diff generates a special IncorrectPatch exception.
        """
        try:
            controllers.DiffSingleFileMission.validate_patch(self.make_swapped_patch())
        except controllers.IncorrectPatch, e:
            self.assert_('order of files passed to diff was flipped' in utf8(e))
        else:
            self.fail('no exception raised')

    def test_remove_trailing_whitespace(self):
        """
        A diff that is corrupted by the removal of line-end whitespace
        generates a special IncorrectPatch exception.
        """
        try:
            controllers.DiffSingleFileMission.validate_patch(self.make_patch_without_trailing_whitespace())
        except controllers.IncorrectPatch, e:
            self.assert_('removed the space' in utf8(e))
        else:
            self.fail('no exception raised')

    def test_diff_missing_headers(self):
        """
        If a diff submission lacks headers, raise a special IncorrectPatch
        exception with a hint that the headers should be included.
        """
        try:
            controllers.DiffSingleFileMission.validate_patch("I lack headers.")
        except controllers.IncorrectPatch, e:
            self.assert_('Make sure you are including the diff headers' in utf8(e))
        else:
            self.fail('no exception raised')

    def test_do_mission_correctly(self):
        orig_response = self.client.get(reverse(views.diffsingle_get_original_file))
        orig_lines = StringIO(orig_response.content).readlines()
        result_lines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()

        diff = ''.join(difflib.unified_diff(orig_lines, result_lines))

        submit_response = self.client.post(reverse(views.diffsingle_submit), {'diff': diff})
        self.assert_(submit_response.context['diffsingle_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffsingle', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        """
        Submitting a generically incorrect diff generates a generic failure message.
        """
        submit_response = self.client.post(reverse(views.diffsingle_submit), {'diff': self.make_wrong_dest_patch()})
        self.assert_('does not have the correct contents' in submit_response.content)
        self.assertFalse(submit_response.context['diffsingle_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffsingle', person=paulproteus)), 0)

    def test_do_mission_backwards_diff(self):
        """
        Submitting a backwards diff generates a special failure message.
        """
        submit_response = self.client.post(reverse(views.diffsingle_submit), {'diff': self.make_swapped_patch()})
        self.assert_('order of files passed to diff was flipped' in submit_response.content)
        self.assertFalse(submit_response.context['diffsingle_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffsingle', person=paulproteus)), 0)

class DiffRecursiveTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def _calculate_correct_recursive_diff(self, dos_line_endings=False):
        orig_response = self.client.get(reverse(views.diffrecursive_get_original_tarball))
        tfile = tarfile.open(fileobj=StringIO(orig_response.content), mode='r:gz')
        diff = StringIO()
        for fileinfo in tfile:
            if not fileinfo.isfile():
                continue
            oldlines = tfile.extractfile(fileinfo).readlines()
            newlines = []
            for line in oldlines:
                for old, new in controllers.DiffRecursiveMission.SUBSTITUTIONS:
                    line = line.replace(old, new)
                newlines.append(line)
            lines_for_output = list(difflib.unified_diff(oldlines, newlines, 'orig-'+fileinfo.name, fileinfo.name))
            bytes_for_output = ''.join(lines_for_output)
            if dos_line_endings:
                bytes_for_output = bytes_for_output.replace('\n', '\r\n')
            diff.write(bytes_for_output)

        diff.seek(0)
        diff.name = 'foo.patch'
        return diff

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_do_mission_correctly(self):
        correct_diff = self._calculate_correct_recursive_diff()
        submit_response = self.client.post(reverse(views.diffrecursive_submit), {'diff': correct_diff})
        self.assert_(submit_response.context['diffrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 1)

    def test_do_mission_correctly_with_dos_line_endings(self):
        correct_diff = self._calculate_correct_recursive_diff(dos_line_endings=True)
        self.assertTrue('\r\n' in correct_diff.getvalue())
        submit_response = self.client.post(reverse(views.diffrecursive_submit), {'diff': correct_diff})
        self.assert_(submit_response.context['diffrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 1)

    def test_do_mission_correctly_with_extra_slashes(self):
        # If you pass weird-looking directory names to diff, with extra slashes
        # (for example: diff -urN old_dir/// new_dir// )
        # you should still be able to pass the mission.

        # First we calculcate a normal diff.
        correct_diff = self._calculate_correct_recursive_diff()

        # Then we mutate it to have extra slashes.
        as_string = correct_diff.getvalue()
        as_string = as_string.replace('recipes/', 'recipes//')
        as_stringio = StringIO(as_string)
        as_stringio.name = 'foo.patch'
        submit_response = self.client.post(reverse(views.diffrecursive_submit), {'diff': as_stringio})
        self.assert_(submit_response.context['diffrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 1)

    def test_do_mission_correctly_with_old_filenames(self):
        orig_response = self.client.get(reverse(views.diffrecursive_get_original_tarball))
        tfile = tarfile.open(fileobj=StringIO(orig_response.content), mode='r:gz')
        diff = StringIO()
        for fileinfo in tfile:
            if not fileinfo.isfile():
                continue

            # calcualate the old name
            transformed_name = controllers.DiffRecursiveMission.name_new2old(
                fileinfo.name)

            oldlines = tfile.extractfile(fileinfo).readlines()
            newlines = []
            for line in oldlines:
                for old, new in controllers.DiffRecursiveMission.SUBSTITUTIONS:
                    line = line.replace(old, new)
                newlines.append(line)

            diff.writelines(difflib.unified_diff(oldlines, newlines,
                                                 'orig-'+transformed_name,
                                                 transformed_name))

        diff.seek(0)
        diff.name = 'foo.patch'
        submit_response = self.client.post(reverse(views.diffrecursive_submit), {'diff': diff})
        self.assert_(submit_response.context['diffrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        diff = StringIO('--- a/foo.txt\n+++ b/foo.txt\n@@ -0,0 +0,1 @@\n+Hello World\n')
        diff.name = 'foo.patch'
        submit_response = self.client.post(reverse(views.diffrecursive_submit), {'diff': diff})
        self.assertFalse(submit_response.context['diffrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 0)

    def test_do_mission_incorrectly_revdiff(self):
        orig_response = self.client.get(reverse(views.diffrecursive_get_original_tarball))
        tfile = tarfile.open(fileobj=StringIO(orig_response.content), mode='r:gz')
        diff = StringIO()
        for fileinfo in tfile:
            if not fileinfo.isfile():
                continue
            oldlines = tfile.extractfile(fileinfo).readlines()
            newlines = []
            for line in oldlines:
                for old, new in controllers.DiffRecursiveMission.SUBSTITUTIONS:
                    line = line.replace(old, new)
                newlines.append(line)

            # We're very similar to test_do_mission-correctly, but here we switch newlines and oldlines, to create a reverse patch
            diff.writelines(difflib.unified_diff(newlines, oldlines, 'orig-'+fileinfo.name, fileinfo.name))
        diff.seek(0)
        diff.name = 'foo.patch'

        # Submit, and see if we get the same error message we expect.
        error = self.client.post(reverse(views.diffrecursive_submit), {'diff': diff})
        self.assert_('You submitted a patch that would revert the correct changes back to the originals.  You may have mixed the parameters for diff, or performed a reverse patch.' in utf8(error))
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 0)

    def test_do_mission_incorrectly_BOM(self):
        diff = StringIO('--- a/foo.txt\n+++ b/foo.txt\n@@ -0,0 +0,1 @@\n+\xef\xbb\xbfHello World\n')
        diff.name = 'foo.patch'
        submit_response = self.client.post(reverse(views.diffrecursive_submit), {'diff': diff})
        self.assertFalse(submit_response.context['diffrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 0)


class PatchRecursiveTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_patch_applies_correctly(self):
        tempdir = tempfile.mkdtemp()

        try:
            tar_process = subprocess.Popen(['tar', '-C', tempdir, '-zxv'], stdin=subprocess.PIPE)
            tar_process.communicate(controllers.DiffRecursiveMission.synthesize_tarball())
            self.assertEqual(tar_process.returncode, 0)

            patch_process = subprocess.Popen(['patch', '-d', tempdir, '-p1'], stdin=subprocess.PIPE)
            patch_process.communicate(controllers.PatchRecursiveMission.get_patch())
            self.assertEqual(patch_process.returncode, 0)

        finally:
            shutil.rmtree(tempdir)

    def test_do_mission_correctly(self):
        response = self.client.post(reverse(views.patchrecursive_submit), controllers.PatchRecursiveMission.ANSWERS)
        self.assert_(response.status_code, 302)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchrecursive', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        answers = {}
        for key, value in controllers.PatchRecursiveMission.ANSWERS.iteritems():
            answers[key] = value + 1
        response = self.client.post(reverse(views.patchrecursive_submit), answers)
        self.assertFalse(response.context['patchrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchrecursive', person=paulproteus)), 0)
