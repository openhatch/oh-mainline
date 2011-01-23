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
from mysite.missions.tar import views, controllers

class TarMissionTests(TestCase):
    def test_good_tarball(self):
        controllers.TarMission.check_tarfile(open(make_testdata_filename('tar', 'good.tar.gz')).read())

    def test_bad_tarball_1(self):
        # should fail due to the tarball not containing a wrapper dir
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('tar', 'bad-1.tar.gz')).read())
        except controllers.IncorrectTarFile, e:
            self.assert_('No wrapper directory is present' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_2(self):
        # should fail due to the tarball not being gzipped
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('tar', 'bad-2.tar')).read())
        except controllers.IncorrectTarFile, e:
            self.assert_('not a valid gzipped tarball' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_3(self):
        # should fail due to one of the files not having the correct contents
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('tar', 'bad-3.tar.gz')).read())
        except controllers.IncorrectTarFile, e:
            self.assert_('has incorrect contents' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_4(self):
        # should fail due to the wrapper dir not having the right name
        try:
            controllers.TarMission.check_tarfile(open(make_testdata_filename('tar', 'bad-4.tar.gz')).read())
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
            response = self.client.get(reverse(views.file_download, kwargs={'name': filename}))
            self.assertEqual(response['Content-Disposition'], 'attachment; filename=%s' % filename)
            self.assertEqual(response.content, content)

    def test_tar_file_download_404(self):
        response = self.client.get(reverse(views.file_download, kwargs={'name': 'doesnotexist.c'}))
        self.assertEqual(response.status_code, 404)

    def test_tar_upload_good(self):
        response = self.client.post(reverse(views.upload), {'tarfile': open(make_testdata_filename('tar', 'good.tar.gz'))})
        self.assert_('create status: success' in response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 1)

        # Make sure that nothing weird happens if it is submitted again.
        response = self.client.post(reverse(views.upload), {'tarfile': open(make_testdata_filename('tar', 'good.tar.gz'))})
        self.assert_('create status: success' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 1)

    def test_tar_upload_bad(self):
        response = self.client.post(reverse(views.upload), {'tarfile': open(make_testdata_filename('tar', 'bad-1.tar.gz'))})
        self.assert_('create status: failure' in response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 0)


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
        response = self.client.get(reverse(views.download_tarball_for_extract_mission))
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=%s' % controllers.UntarMission.TARBALL_NAME)

    def test_do_mission_correctly(self):
        download_response = self.client.get(reverse(views.download_tarball_for_extract_mission))
        tfile = tarfile.open(fileobj=StringIO(download_response.content), mode='r:gz')
        contents_it_wants = tfile.extractfile(tfile.getmember(controllers.UntarMission.FILE_WE_WANT))
        upload_response = self.client.post(reverse(views.extract_mission_upload), {'extracted_file': contents_it_wants})
        self.assert_('unpack status: success' in upload_response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar_extract', person=paulproteus)), 1)

    def test_do_mission_incorrectly(self):
        bad_file = StringIO('This is certainly not what it wants!')
        bad_file.name = os.path.basename(controllers.UntarMission.FILE_WE_WANT)
        upload_response = self.client.post(reverse(views.extract_mission_upload),
                                           {'extracted_file': bad_file})
        self.assert_('unpack status: failure' in upload_response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar_extract', person=paulproteus)), 0)

