# This file is part of OpenHatch.
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

from django_webtest import WebTest
from mysite.missions.base.tests import (
    Person,
    reverse,
    StepCompletion,
)
from mysite.missions.shell import views


class Testcd(WebTest):
    """ Tests for 'cd' command's mission """
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_do_mission_incorrectly(self):
        """ mission should not be completed when done incorrectly """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/cd')
        form = mission_page.form
        wrong_answer = '1'
        form['option'] = wrong_answer
        response = form.submit()
        self.assertFalse(response.context['command_cd_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_cd', person=paulproteus)), 0)

    def test_do_mission_correctly(self):
        """ completed cd mission if answer is correct """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/cd')
        form = mission_page.form
        correct_answer = '3'
        form['option'] = correct_answer
        response = form.submit()
        self.assert_(response.context['command_cd_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_cd', person=paulproteus)), 1)


class Testls(WebTest):
    """ Tests for 'ls' command's mission """
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_do_mission_incorrectly(self):
        """ mission should not be completed when done incorrectly """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/ls')
        form = mission_page.form
        wrong_answer = '2'
        form['option'] = wrong_answer
        response = form.submit()
        self.assertFalse(response.context['command_ls_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_ls', person=paulproteus)), 0)

    def test_do_mission_correctly(self):
        """ completed ls mission if answer is correct """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/ls')
        form = mission_page.form
        correct_answer = '1'
        form['option'] = correct_answer
        response = form.submit()
        self.assert_(response.context['command_ls_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_ls', person=paulproteus)), 1)


class Test_mkdir_rm(WebTest):
    """ Tests for 'mkdir' and 'rm' command mission """
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_do_mission_incorrectly(self):
        """ mission should not be completed when done incorrectly """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/create-and-remove')
        form = mission_page.form
        wrong_answer = '2'
        form['option'] = wrong_answer
        response = form.submit()
        self.assertFalse(response.context['command_mkdir_rm_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_mkdir_rm', person=paulproteus)), 0)

    def test_do_mission_correctly(self):
        """ completed create and remove mission if answer is correct """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/create-and-remove')
        form = mission_page.form
        correct_answer = '3'
        form['option'] = correct_answer
        response = form.submit()
        self.assert_(response.context['command_mkdir_rm_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_mkdir_rm', person=paulproteus)), 1)


class Test_cp_mv(WebTest):
    """ Tests for 'cp' and 'mv' command mission """
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_do_mission_incorrectly(self):
        """ mission should not be completed when done incorrectly """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/copy-and-move')
        form = mission_page.form
        wrong_answer = '2'
        form['option'] = wrong_answer
        response = form.submit()
        self.assertFalse(response.context['command_cp_mv_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_cp_mv', person=paulproteus)), 0)

    def test_do_mission_correctly(self):
        """ completed copy and move mission if answer is correct """
        username = 'paulproteus'
        password = "paulproteus's unbreakable password"

        # Login before submitting answer
        login_page = self.app.get('/account/login/')
        login_page_old = login_page.click('Log in with a password')
        login_page_form = login_page_old.form
        login_page_form['username'] = username
        login_page_form['password'] = password
        login_page_form.submit()

        # Mission page
        mission_page = self.app.get('/missions/shell/copy-and-move')
        form = mission_page.form
        correct_answer = '4'
        form['option'] = correct_answer
        response = form.submit()
        self.assert_(response.context['command_cp_mv_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='command_cp_mv', person=paulproteus)), 1)
