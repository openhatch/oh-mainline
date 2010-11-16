from mysite.missions.base.tests import *
from mysite.missions.svn import views, controllers

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
        response = self.client.get(reverse(views.resetrepo))
        self.assert_(response.status_code == 405)

    def test_resetrepo_creates_valid_repo(self):
        self.client.post(reverse(views.resetrepo))
        subprocess.check_call(['svn', 'info', 'file://'+self.repo_path])

    def test_do_checkout_mission_correctly(self):
        self.client.post(reverse(views.resetrepo))
        response = self.client.get(reverse(views.checkout))
        checkoutdir = tempfile.mkdtemp()
        try:
            subprocess.check_call(['svn', 'checkout', response.context['checkout_url'], checkoutdir])
            word = open(os.path.join(checkoutdir, response.context['secret_word_file'])).read().strip()
            response = self.client.post(reverse(views.checkout_submit), {'secret_word': word})
            paulproteus = Person.objects.get(user__username='paulproteus')
            self.assert_(controllers.mission_completed(paulproteus, 'svn_checkout'))
        finally:
            shutil.rmtree(checkoutdir)

    def test_do_checkout_mission_incorrectly(self):
        self.client.post(reverse(views.resetrepo))
        response = self.client.post(reverse(views.checkout_submit), {'secret_word': 'not_the_secret_word'})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertFalse(controllers.mission_completed(paulproteus, 'svn_checkout'))

    def test_do_diff_mission_correctly(self):
        self.client.post(reverse(views.resetrepo))
        response = self.client.get(reverse(views.checkout))
        checkoutdir = tempfile.mkdtemp()
        try:
            # Check the repository out and make the required change.
            subprocess.check_call(['svn', 'checkout', response.context['checkout_url'], checkoutdir])
            new_contents = open(os.path.join(controllers.get_mission_data_path('svn'), controllers.SvnDiffMission.NEW_CONTENT)).read()
            open(os.path.join(checkoutdir, controllers.SvnDiffMission.FILE_TO_BE_PATCHED), 'w').write(new_contents)

            # Make the diff.
            diff = subproc_check_output(['svn', 'diff'], cwd=checkoutdir)

            # Submit the diff.
            response = self.client.post(reverse(views.diff_submit), {'diff': diff})
            paulproteus = Person.objects.get(user__username='paulproteus')
            self.assert_(controllers.mission_completed(paulproteus, 'svn_diff'))

            # Check that there is a new commit that applies to the working copy cleanly.
            update_output = subproc_check_output(['svn', 'update'], cwd=checkoutdir)
            self.assert_('Updated to revision ' in update_output)
        finally:
            shutil.rmtree(checkoutdir)

    def test_diff_without_spaces_works(self):
        self.client.post(reverse(views.resetrepo))
        self.client.post(reverse(views.diff_submit), {'diff': open(make_testdata_filename('svn', 'svn-diff-without-spaces-on-blank-context-lines.patch')).read()})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assert_(controllers.mission_completed(paulproteus, 'svn_diff'))


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

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_good_commit(self):
        self.assert_commit_allowed()

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_bad)
    def test_reject_commit_without_log_message(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_bad_secret_word)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_with_bad_secret_word(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_good)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_bad_readme)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_with_bad_readme(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_bad_modifies_extra_file)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_modifies_extra_file(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_bad_skips_file)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_skips_file(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_bad_adds_file)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_adds_file(self):
        self.assert_commit_not_allowed()

    @mock.patch('mysite.missions.svn.controllers.get_username_for_svn_txn', mock_get_username)
    @mock.patch('mysite.missions.svn.controllers.get_changes_for_svn_txn', mock_get_changes_bad_removes_file)
    @mock.patch('mysite.missions.svn.controllers.get_file_for_svn_txn', mock_get_file_good)
    @mock.patch('mysite.missions.svn.controllers.get_log_for_svn_txn', mock_get_log_good)
    def test_reject_commit_that_removes_file(self):
        self.assert_commit_not_allowed()
