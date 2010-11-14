from mysite.missions.base.tests import *
from mysite.missions.diffpatch import views, controllers

class PatchSingleFileTests(TwillTests):
    fixtures = ['person-paulproteus', 'user-paulproteus']

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
        orig_response = self.client.get(reverse(views.diffpatch_patchsingle_get_original_file))
        self.assert_(orig_response['Content-Disposition'].startswith('attachment'))
        patch_response = self.client.get(reverse(views.diffpatch_patchsingle_get_patch))
        self.assert_(patch_response['Content-Disposition'].startswith('attachment'))

    def test_do_mission_correctly(self):
        oldfile = tempfile.NamedTemporaryFile(delete=False)
        file_to_patch = oldfile.name

        try:
            orig_response = self.client.get(reverse(views.diffpatch_patchsingle_get_original_file))
            oldfile.write(orig_response.content)
            oldfile.close()

            patch_response = self.client.get(reverse(views.diffpatch_patchsingle_get_patch))
            patch_process = subprocess.Popen(['patch', file_to_patch], stdin=subprocess.PIPE)
            patch_process.communicate(patch_response.content)
            self.assertEqual(patch_process.returncode, 0)

            submit_response = self.client.post(reverse(views.diffpatch_patchsingle_submit), {'patched_file': open(file_to_patch)})
            self.assert_(submit_response.context['patchsingle_success'])

            paulproteus = Person.objects.get(user__username='paulproteus')
            self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchsingle', person=paulproteus)), 1)

        finally:
            os.unlink(file_to_patch)

    def test_do_mission_incorrectly(self):
        patched_file = StringIO('Some arbitrary contents so the file is incorrect.')
        patched_file.name = 'foo.c'
        submit_response = self.client.post(reverse(views.diffpatch_patchsingle_submit), {'patched_file': patched_file})
        self.assertFalse(submit_response.context['patchsingle_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchsingle', person=paulproteus)), 0)


class DiffSingleFileTests(TwillTests):
    fixtures = ['person-paulproteus', 'user-paulproteus']

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

    def make_wrong_dest_patch(self):
        # Make a patch that will apply correctly but does not result in the right file.
        oldlines = open(controllers.DiffSingleFileMission.OLD_FILE).readlines()
        newlines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()
        del newlines[0]
        return ''.join(difflib.unified_diff(oldlines, newlines, 'old.txt', 'new.txt'))

    def make_swapped_patch(self):
        oldlines = open(controllers.DiffSingleFileMission.OLD_FILE).readlines()
        newlines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()
        return ''.join(difflib.unified_diff(newlines, oldlines, 'new.txt', 'old.txt'))

    def test_good_patch(self):
        controllers.DiffSingleFileMission.validate_patch(self.make_good_patch())

    def test_not_single_file(self):
        try:
            controllers.DiffSingleFileMission.validate_patch(self.make_good_patch() * 2)
        except controllers.IncorrectPatch, e:
            self.assert_('affects more than one file' in str(e))
        else:
            self.fail('no exception raised')

    def test_does_not_apply_correctly(self):
        try:
            controllers.DiffSingleFileMission.validate_patch(self.make_wrong_src_patch())
        except controllers.IncorrectPatch, e:
            self.assert_('will not apply' in str(e))
        else:
            self.fail('no exception raised')

    def test_produces_wrong_file(self):
        try:
            controllers.DiffSingleFileMission.validate_patch(self.make_wrong_dest_patch())
        except controllers.IncorrectPatch, e:
            self.assert_('does not have the correct contents' in str(e))
        else:
            self.fail('no exception raised')

    def test_do_mission_correctly(self):
        orig_response = self.client.get(reverse(views.diffpatch_diffsingle_get_original_file))
        orig_lines = StringIO(orig_response.content).readlines()
        result_lines = open(controllers.DiffSingleFileMission.NEW_FILE).readlines()

        diff = ''.join(difflib.unified_diff(orig_lines, result_lines))

        submit_response = self.client.post(reverse(views.diffpatch_diffsingle_submit), {'diff': diff})
        self.assert_(submit_response.context['diffsingle_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffsingle', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        submit_response = self.client.post(reverse(views.diffpatch_diffsingle_submit), {'diff': self.make_swapped_patch()})
        self.assertFalse(submit_response.context['diffsingle_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffsingle', person=paulproteus)), 0)

class DiffRecursiveTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_do_mission_correctly(self):
        orig_response = self.client.get(reverse(views.diffpatch_diffrecursive_get_original_tarball))
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
            diff.writelines(difflib.unified_diff(oldlines, newlines, 'orig-'+fileinfo.name, fileinfo.name))

        diff.seek(0)
        diff.name = 'foo.patch'
        submit_response = self.client.post(reverse(views.diffpatch_diffrecursive_submit), {'diff': diff})
        self.assert_(submit_response.context['diffrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_diffrecursive', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        diff = StringIO('--- a/foo.txt\n+++ b/foo.txt\n@@ -0,0 +0,1 @@\n+Hello World\n')
        diff.name = 'foo.patch'
        submit_response = self.client.post(reverse(views.diffpatch_diffrecursive_submit), {'diff': diff})
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
            tar_process.communicate(controllers.PatchRecursiveMission.synthesize_tarball())
            self.assertEqual(tar_process.returncode, 0)

            patch_process = subprocess.Popen(['patch', '-d', os.path.join(tempdir, controllers.PatchRecursiveMission.BASE_NAME), '-p1'], stdin=subprocess.PIPE)
            patch_process.communicate(controllers.PatchRecursiveMission.get_patch())
            self.assertEqual(patch_process.returncode, 0)

        finally:
            shutil.rmtree(tempdir)

    def test_do_mission_correctly(self):
        response = self.client.post(reverse(views.diffpatch_patchrecursive_submit), controllers.PatchRecursiveMission.ANSWERS)
        self.assert_(response.context['patchrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchrecursive', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        answers = {}
        for key, value in controllers.PatchRecursiveMission.ANSWERS.iteritems():
            answers[key] = value + 1
        response = self.client.post(reverse(views.diffpatch_patchrecursive_submit), answers)
        self.assertFalse(response.context['patchrecursive_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='diffpatch_patchrecursive', person=paulproteus)), 0)
