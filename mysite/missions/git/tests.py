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

from mysite.missions.base.tests import *
from mysite.missions.git import views, view_helpers


class GitViewTestsWhileLoggedOut(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()
        self.client.logout()

    def test_main_page_does_not_complain_about_prereqs_even_if_logged_out(self):
        response = self.client.get(reverse(views.main_page))
        self.assertTrue(response.context[0]
                        ['mission_step_prerequisites_passed'])


class GitViewTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()
        self.repo_path = os.path.join(settings.GIT_REPO_PATH, 'paulproteus')
        # Make sure that our test user's git repository does not exist.
        if os.path.isdir(self.repo_path):
            shutil.rmtree(self.repo_path)

    def test_main_page_does_not_complain_about_prereqs(self):
        response = self.client.get(reverse(views.main_page))
        self.assertTrue(response.context[0]
                        ['mission_step_prerequisites_passed'])

    def test_resetrepo_returns_error_with_get(self):
        response = self.client.get(reverse(views.resetrepo))
        self.assert_(response.status_code == 405)

    def test_resetrepo_creates_valid_repo(self):
        self.client.post(reverse(views.resetrepo))
        self.assertTrue(os.path.exists(self.repo_path + "/.git"))

    def test_do_checkout_mission_correctly(self):
        word = 'the brain'
        response = self.client.post(
            reverse(views.checkout_submit), {'secret_word': word})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assert_(
            view_helpers.mission_completed(paulproteus, 'git_checkout'))

    def test_do_checkout_mission_incorrectly(self):
        word = 'the wrong word'
        response = self.client.post(
            reverse(views.checkout_submit), {'secret_word': word})

    def email_address_is_rejected(self, email_address):
        response = self.client.post(
            reverse(views.long_description_submit), {'user_email': email_address})
        self.assertEqual(200, response.status_code)

    def test_do_git_description_mission_incorrectly(self):
        self.assertFalse(
            self.email_address_is_rejected('paulproteus@pathi.local'))
        self.assertFalse(
            self.email_address_is_rejected('filipovskii_off@Puppo.(none)'))
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertFalse(
            view_helpers.mission_completed(paulproteus, 'git_config'))

    def test_do_git_description_mission_correctly(self):
        correct_email = 'paulproteus@openhatch.org'
        response = self.client.post(
            reverse(views.long_description_submit), {'user_email': correct_email})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertTrue(
            view_helpers.mission_completed(paulproteus, 'git_config'))

    def test_do_git_description_mission_correctly_with_weird_email_address(self):
        correct_email = 'paulproteus@localhost.com'
        response = self.client.post(
            reverse(views.long_description_submit), {'user_email': correct_email})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertTrue(
            view_helpers.mission_completed(paulproteus, 'git_config'))

    def test_do_rebase_mission_incorrectly(self):
        word = 'the wrong word'
        response = self.client.post(
            reverse(views.rebase_submit), {'secret_word': word})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertFalse(
            view_helpers.mission_completed(paulproteus, 'git_rebase'))

    def test_do_diff_mission_correctly(self):
        self.client.post(reverse(views.resetrepo))
        cwd = self.repo_path
        with open(os.path.join(cwd, '../../../missions/git/data/hello.patch'), 'r') as expected_diff_file:
            expected_diff = expected_diff_file.read()
        response = self.client.post(reverse(views.resetrepo))
        response = self.client.post(
            reverse(views.diff_submit), {'diff': expected_diff})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assert_(view_helpers.mission_completed(paulproteus, 'git_diff'))

    def test_do_diff_mission_correctly_in_swedish(self):
        self.client.post(reverse(views.resetrepo))
        cwd = self.repo_path
        with open(
            os.path.join(cwd, '../../../missions/git/data/swedish-patch'),
                'r') as expected_diff_file:
            expected_diff = expected_diff_file.read()
        self.client.post(reverse(views.resetrepo))
        self.client.post(reverse(views.diff_submit), {'diff': expected_diff})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assert_(view_helpers.mission_completed(paulproteus, 'git_diff'))

    def test_do_diff_mission_incorrectly(self):
        self.client.post(reverse(views.resetrepo))
        cwd = self.repo_path
        with open(os.path.join(cwd, '../../../missions/git/data/hello.patch'), 'r') as expected_diff_file:
            expected_diff = expected_diff_file.read()
        unexpected_diff = expected_diff.replace('Hello', 'Goodbye')
        response = self.client.post(reverse(views.resetrepo))
        response = self.client.post(
            reverse(views.diff_submit), {'diff': unexpected_diff})
        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertFalse(
            view_helpers.mission_completed(paulproteus, 'git_diff'))
