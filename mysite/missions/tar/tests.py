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

from mysite.base.tests import TwillTests
from mysite.missions.base.tests import *
from mysite.missions.tar import views
from mysite.missions.tar import view_helpers


class TarUploadTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_tar_file_downloads(self):
        for filename, content in view_helpers.TarMission.FILES.iteritems():
            response = self.client.get(
                reverse(views.file_download, kwargs={'name': filename}))
            self.assertEqual(response['Content-Disposition'],
                             'attachment; filename=%s' % filename)
            self.assertEqual(response.content, content)

    def test_tar_file_download_404(self):
        response = self.client.get(
            reverse(views.file_download, kwargs={'name': 'doesnotexist.c'}))
        self.assertEqual(response.status_code, 404)


class UntarViewTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_download_headers(self):
        response = self.client.get(
            reverse(views.download_tarball_for_extract_mission))
        self.assertEqual(
            response['Content-Disposition'], 'attachment; filename=%s' %
            view_helpers.UntarMission.TARBALL_NAME)


class MissionPageStateTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus', ]

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_mission_completion_full_reset(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        StepCompletion(person=paulproteus,
                       step=Step.objects.get(name='tar')).save()

        response = self.client.post(
            reverse(views.reset), {'mission_parts': 'tar'})
        self.assert_('Operation successful' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar', person=paulproteus, is_currently_completed=True)), 0)

    def test_mission_completion_partial_reset(self):
        paulproteus = Person.objects.get(user__username='paulproteus')
        StepCompletion(person=paulproteus,
                       step=Step.objects.get(name='tar')).save()
        StepCompletion(person=paulproteus,
                       step=Step.objects.get(name='tar_extract')).save()

        response = self.client.post(
            reverse(views.reset), {'mission_parts': 'tar,tar_extract'})
        self.assert_('Operation successful' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar', person=paulproteus, is_currently_completed=True)), 0)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar_extract', person=paulproteus, is_currently_completed=True)), 0)

    def get_extracted_tarball(self):
        """
        Get and extract a tar_extract misssion tarball.
        """
        download_response = self.client.get(
            reverse(views.download_tarball_for_extract_mission))
        tfile = tarfile.open(
            fileobj=StringIO(download_response.content), mode='r:gz')
        return tfile.extractfile(tfile.getmember(view_helpers.UntarMission.FILE_WE_WANT))

    def test_extract_mission_reset_redo(self):
        """
        Once the tar_extract mission has been reset, it can be completed again.
        """
        paulproteus = Person.objects.get(user__username='paulproteus')

        # Complete the tar_extract mission the first time.
        upload_response = self.client.post(
            reverse(views.extract_mission_success), {'unpack_success': True})
        self.assert_('Step successfully completed' in upload_response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar_extract', person=paulproteus,
            is_currently_completed=True)), 1)

        # Reset the mission.
        response = self.client.post(
            reverse(views.reset), {'mission_parts': 'tar_extract'})
        self.assert_('Operation successful' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar_extract', person=paulproteus,
            is_currently_completed=False)), 1)

        # Complete the tar_extract missions a second time
        upload_response = self.client.post(
            reverse(views.extract_mission_success), {'unpack_success': True})
        self.assert_('Step successfully completed' in upload_response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar_extract', person=paulproteus,
            is_currently_completed=True)), 1)

    def test_upload_mission_reset_redo(self):
        """
        Once the tar (upload) mission has been reset, it can be completed again.
        """
        paulproteus = Person.objects.get(user__username='paulproteus')

        # Complete the tar mission the first time.
        response = self.client.post(
            reverse(views.create_mission_success), {'create_success': True})
        self.assert_('Step successfully completed' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar', person=paulproteus,
            is_currently_completed=True)), 1)

        # Reset the mission.
        response = self.client.post(
            reverse(views.reset), {'mission_parts': 'tar'})
        self.assert_('Operation successful' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar', person=paulproteus,
            is_currently_completed=False)), 1)

        # Complete the tar missions a second time.
        response = self.client.post(
            reverse(views.create_mission_success), {'create_success': True})
        self.assert_('Step successfully completed' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(
            step__name='tar', person=paulproteus,
            is_currently_completed=True)), 1)
