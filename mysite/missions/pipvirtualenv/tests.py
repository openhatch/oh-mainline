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

from mysite.missions.base.tests import (
    TwillTests,
    Person,
    reverse,
    StepCompletion,
)
from mysite.missions.pipvirtualenv import views, view_helpers

# No need to include pip list output since the corresponding
# functions that validate the pip list or pip freeze output
# submitted by the user just look for the string "requests" in it.

pip_freeze_output_without_requests = "\nargparse==1.2.1\nwsgiref==0.1.2\n"
pip_freeze_output_with_requests = ("\nargparse==1.2.1\nwsgiref==0.1.2"
    "\nrequests==2.5.1\n")

class InstallingPackagesTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_do_mission_correctly(self):
        submit_response = self.client.post(
            reverse(views.pip_freeze_submit),
            {'pipfreeze_output': pip_freeze_output_with_requests}
        )
        self.assert_(submit_response.context['pipfreeze_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='pipvirtualenv_pipfreeze', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        submit_response = self.client.post(
            reverse(views.pip_freeze_submit),
            {'pipfreeze_output': pip_freeze_output_without_requests}
        )
        self.assertFalse(submit_response.context['pipfreeze_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='pipvirtualenv_pipfreeze', person=paulproteus)), 0)


class RemovingPackagesTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    
    def test_do_mission_correctly(self):
        submit_response = self.client.post(
            reverse(views.pip_list_submit),
            {'piplist_output': pip_freeze_output_without_requests}
        )
        self.assert_(submit_response.context['piplist_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='pipvirtualenv_piplist', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        submit_response = self.client.post(
            reverse(views.pip_list_submit),
            {'piplist_output': pip_freeze_output_with_requests}
        )
        self.assertFalse(submit_response.context['piplist_success'])

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='pipvirtualenv_piplist', person=paulproteus)), 0)


