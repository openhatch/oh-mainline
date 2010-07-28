from unittest import TestCase
from mysite.base.tests import TwillTests
from mysite.missions import views, controllers
from mysite.missions.models import StepCompletion, Step
from mysite.profile.models import Person
from mysite.base.helpers import subproc_check_output
from django.conf import settings
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.test import TestCase as DjangoTestCase

import mock
import os
import tarfile
from StringIO import StringIO
import tempfile
import subprocess
import difflib
import shutil
import random

def make_testdata_filename(filename):
    return os.path.join(os.path.dirname(__file__), 'testdata', filename)

class TarMissionTests(TestCase):
    def test_good_tarball(self):
        controllers.TarMission.check_tarfile(open(make_testdata_filename('good.tar.gz')).read())

    def test_bad_tarball_1(self):
        # should fail due to the tarball not containing a wrapper dir
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('bad-1.tar.gz')).read())
        except controllers.IncorrectTarFile, e:
            self.assert_('No wrapper directory is present' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_2(self):
        # should fail due to the tarball not being gzipped
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('bad-2.tar')).read())
        except controllers.IncorrectTarFile, e:
            self.assert_('not a valid gzipped tarball' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_3(self):
        # should fail due to one of the files not having the correct contents
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('bad-3.tar.gz')).read())
        except controllers.IncorrectTarFile, e:
            self.assert_('has incorrect contents' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_4(self):
        # should fail due to the wrapper dir not having the right name
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('bad-4.tar.gz')).read())
        except controllers.IncorrectTarFile, e:
            self.assert_('Wrapper directory name is incorrect' in e.args[0])
        else:
            self.fail('no exception raised')


class TarUploadTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_tar_file_downloads(self):
        for filename, content in controllers.TarMission.FILES.iteritems():
            response = self.client.get(reverse(views.tar_file_download, kwargs={'name': filename}))
            self.assertEqual(response['Content-Disposition'], 'attachment; filename=%s' % filename)
            self.assertEqual(response.content, content)

    def test_tar_file_download_404(self):
        response = self.client.get(reverse(views.tar_file_download, kwargs={'name': 'doesnotexist.c'}))
        self.assertEqual(response.status_code, 404)

    def test_tar_upload_good(self):
        response = self.client.post(reverse(views.tar_upload), {'tarfile': open(make_testdata_filename('good.tar.gz'))})
        self.assert_('create status: success' in response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 1)

        # Make sure that nothing weird happens if it is submitted again.
        response = self.client.post(reverse(views.tar_upload), {'tarfile': open(make_testdata_filename('good.tar.gz'))})
        self.assert_('create status: success' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 1)

    def test_tar_upload_bad(self):
        response = self.client.post(reverse(views.tar_upload), {'tarfile': open(make_testdata_filename('bad-1.tar.gz'))})
        self.assert_('create status: failure' in response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 0)


class MainPageTests(TwillTests):
    fixtures = ['person-paulproteus', 'user-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_mission_completion_list_display(self):
        response = self.client.get(reverse(views.main_page))
        self.assertEqual(response.context['completed_missions'], {})

        paulproteus = Person.objects.get(user__username='paulproteus')
        StepCompletion(person=paulproteus, step=Step.objects.get(name='tar')).save()

        response = self.client.get(reverse(views.main_page))
        self.assertEqual(response.context['completed_missions'], {'tar': True})


class UntarMissionTests(TestCase):

    def test_tarball_contains_file_we_want(self):
        tfile = tarfile.open(fileobj=StringIO(controllers.UntarMission.synthesize_tarball()), mode='r:gz')

        # Check the file we want contains the right thing.
        file_we_want = tfile.getmember(controllers.UntarMission.FILE_WE_WANT)
        self.assert_(file_we_want.isfile())
        self.assertEqual(tfile.extractfile(file_we_want).read(), controllers.UntarMission.get_contents_we_want())


class UntarViewTests(TwillTests):
    fixtures = ['person-paulproteus', 'user-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_download_headers(self):
        response = self.client.get(reverse(views.tar_download_tarball_for_extract_mission))
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=%s' % controllers.UntarMission.TARBALL_NAME)

    def test_do_mission_correctly(self):
        download_response = self.client.get(reverse(views.tar_download_tarball_for_extract_mission))
        tfile = tarfile.open(fileobj=StringIO(download_response.content), mode='r:gz')
        contents_it_wants = tfile.extractfile(tfile.getmember(controllers.UntarMission.FILE_WE_WANT))
        upload_response = self.client.post(reverse(views.tar_extract_mission_upload), {'extracted_file': contents_it_wants})
        self.assert_('unpack status: success' in upload_response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar_extract', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        bad_file = StringIO('This is certainly not what it wants!')
        bad_file.name = os.path.basename(controllers.UntarMission.FILE_WE_WANT)
        upload_response = self.client.post(reverse(views.tar_extract_mission_upload),
                                           {'extracted_file': bad_file})
        self.assert_('unpack status: failure' in upload_response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar_extract', person=paulproteus)), 0)


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

class SvnBackendTests(TestCase):

    def get_info(self, path):
        svninfo = subproc_check_output(['svn', 'info', 'file://'+path])
        info = {}
        for line in svninfo.splitlines():
            if ': ' in line:
                key, separator, value = line.partition(': ')
                info[key] = value
        return info

    def test_repo_reset(self):
        repo_path = tempfile.mkdtemp(dir=settings.SVN_REPO_PATH)
        random_name = os.path.basename(repo_path)
        os.rmdir(repo_path)
        try:
            # Check that we can run "svn info" on the created repository to get the UUID.
            controllers.SvnRepository(random_name).reset()
            old_uuid = self.get_info(repo_path)['Repository UUID']
            # Check that resetting the repository changes its UUID.
            controllers.SvnRepository(random_name).reset()
            new_uuid = self.get_info(repo_path)['Repository UUID']
            self.assertNotEqual(old_uuid, new_uuid)
        finally:
            if os.path.isdir(repo_path):
                shutil.rmtree(repo_path)

class SvnViewTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()
        self.repo_path = os.path.join(settings.SVN_REPO_PATH, 'paulproteus')
        # Make sure that our test user's svn repository does not exist.
        if os.path.isdir(self.repo_path):
            shutil.rmtree(self.repo_path)

    def test_resetrepo_returns_error_with_get(self):
        response = self.client.get(reverse(views.svn_resetrepo))
        self.assert_(response.status_code == 405)

    def test_resetrepo_creates_valid_repo(self):
        self.client.post(reverse(views.svn_resetrepo))
        subprocess.check_call(['svn', 'info', 'file://'+self.repo_path])

    def test_do_checkout_mission_correctly(self):
        self.client.post(reverse(views.svn_resetrepo))
        response = self.client.get(reverse(views.svn_checkout))
        checkoutdir = tempfile.mkdtemp()
        try:
            subprocess.check_call(['svn', 'checkout', response.context['checkout_url'], checkoutdir])
            word = open(os.path.join(checkoutdir, response.context['secret_word_file'])).read().strip()
            response = self.client.post(reverse(views.svn_checkout_submit), {'secret_word': word})
            self.assert_(response.context['svn_checkout_success'])
            paulproteus = Person.objects.get(user__username='paulproteus')
            self.assert_(controllers.mission_completed(paulproteus, 'svn_checkout'))
        finally:
            shutil.rmtree(checkoutdir)

    def test_do_checkout_mission_incorrectly(self):
        self.client.post(reverse(views.svn_resetrepo))
        response = self.client.post(reverse(views.svn_checkout_submit), {'secret_word': 'not_the_secret_word'})
        self.assertFalse(response.context['svn_checkout_success'])
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertFalse(controllers.mission_completed(paulproteus, 'svn_checkout'))

    def test_do_diff_mission_correctly(self):
        self.client.post(reverse(views.svn_resetrepo))
        response = self.client.get(reverse(views.svn_checkout))
        checkoutdir = tempfile.mkdtemp()
        try:
            # Check the repository out and make the required change.
            subprocess.check_call(['svn', 'checkout', response.context['checkout_url'], checkoutdir])
            new_contents = open(os.path.join(controllers.get_mission_data_path(), controllers.SvnDiffMission.NEW_CONTENT)).read()
            open(os.path.join(checkoutdir, controllers.SvnDiffMission.FILE_TO_BE_PATCHED), 'w').write(new_contents)

            # Make the diff.
            diff = subproc_check_output(['svn', 'diff'], cwd=checkoutdir)

            # Submit the diff.
            response = self.client.post(reverse(views.svn_diff_submit), {'diff': diff})
            self.assert_(response.context['svn_diff_success'])
            paulproteus = Person.objects.get(user__username='paulproteus')
            self.assert_(controllers.mission_completed(paulproteus, 'svn_diff'))

            # Check that there is a new commit that applies to the working copy cleanly.
            update_output = subproc_check_output(['svn', 'update'], cwd=checkoutdir)
            self.assert_('Updated to revision ' in update_output)
        finally:
            shutil.rmtree(checkoutdir)


# Mocked-up svnlook output for the pre-commit hook.
def mock_get_username(repo, txn):
    return 'paulproteus'

def mock_get_changes_good(repo, txn):
    return [('U', 'trunk/'+controllers.SvnCommitMission.SECRET_WORD_FILE),
            ('U', 'trunk/'+controllers.SvnCommitMission.FILE_TO_BE_PATCHED)]

def mock_get_changes_bad_modifies_extra_file(repo, txn):
    return mock_get_changes_good(repo, txn) + [('U', 'foo.txt')]

def mock_get_changes_bad_skips_file(repo, txn):
    return mock_get_changes_good(repo, txn)[:-1]

def mock_get_changes_bad_adds_file(repo, txn):
    return mock_get_changes_good(repo, txn) + [('A', 'foo.txt')]

def mock_get_changes_bad_removes_file(repo, txn):
    return [('D', filename) for action, filename in mock_get_changes_good(repo, txn)]

def mock_get_file_good(repo, txn, filename):
    if filename == 'trunk/'+controllers.SvnCommitMission.SECRET_WORD_FILE:
        return controllers.SvnCommitMission.NEW_SECRET_WORD+'\n'
    elif filename == 'trunk/'+controllers.SvnCommitMission.FILE_TO_BE_PATCHED:
        return open(controllers.SvnCommitMission.NEW_CONTENT).read()
    else:
        subproc_check_output(['false'])

def mock_get_file_bad_secret_word(repo, txn, filename):
    if filename == 'trunk/'+controllers.SvnCommitMission.SECRET_WORD_FILE:
        return 'bad-secret-word\n'
    return mock_get_file_good(repo, txn, filename)

def mock_get_file_bad_readme(repo, txn, filename):
    if filename == 'trunk/'+controllers.SvnCommitMission.FILE_TO_BE_PATCHED:
        return 'This substitute content is surely wrong.\n'
    return mock_get_file_good(repo, txn, filename)

def mock_get_log_good(repo, txn):
    return 'This test log message will be accepted.\n'

def mock_get_log_bad(repo, txn):
    return ''

class SvnCommitHookTests(DjangoTestCase):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        # We fully mock the svnlook output, so the hook doesn't try to inspect a repository at all during the tests.
        controllers.set_mission_completed(Person.objects.get(user__username='paulproteus'), 'svn_diff')

    def assert_commit_allowed(self):
        controllers.SvnCommitMission.pre_commit_hook('/fake/repository/path', 'fake-transaction-id')
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assert_(controllers.mission_completed(paulproteus, 'svn_commit'))

    def assert_commit_not_allowed(self):
        try:
            controllers.SvnCommitMission.pre_commit_hook('/fake/repository/path', 'fake-transaction-id')
            self.fail('No exception was raised.')
        except controllers.IncorrectPatch, e:
            pass
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertFalse(controllers.mission_completed(paulproteus, 'svn_commit'))

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_good_commit(self):
        self.assert_commit_allowed()

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_bad)
    def test_reject_commit_without_log_message(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_bad_secret_word)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_with_bad_secret_word(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_bad_readme)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_with_bad_readme(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_bad_modifies_extra_file)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_modifies_extra_file(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_bad_skips_file)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_skips_file(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_bad_adds_file)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_adds_file(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.controllers.get_changes_for_svn_txn', mock_get_changes_bad_removes_file)
    @mock.patch('mysite.missions.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_removes_file(self):
        self.assert_commit_not_allowed()
