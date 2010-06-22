from unittest import TestCase
from mysite.base.tests import TwillTests
from mysite.missions.controllers import TarMission, IncorrectTarFile, UntarMission
from mysite.missions.views import tar_upload, tar_file_download, main_page
from mysite.missions.models import StepCompletion, Step
from mysite.profile.models import Person
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.test import TestCase as DjangoTestCase

import os
import tarfile

def make_testdata_filename(filename):
    return os.path.join(os.path.dirname(__file__), 'testdata', filename)

class TarMissionTests(TestCase):
    def test_good_tarball(self):
        TarMission.check_tarfile(open(make_testdata_filename('good.tar.gz')).read())

    def test_bad_tarball_1(self):
        # should fail due to the tarball not containing a wrapper dir
        try:
            TarMission.check_tarfile(open(make_testdata_filename('bad-1.tar.gz')).read())
        except IncorrectTarFile, e:
            self.assert_('No wrapper directory is present' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_2(self):
        # should fail due to the tarball not being gzipped
        try:
            TarMission.check_tarfile(open(make_testdata_filename('bad-2.tar')).read())
        except IncorrectTarFile, e:
            self.assert_('not a valid gzipped tarball' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_3(self):
        # should fail due to one of the files not having the correct contents
        try:
            TarMission.check_tarfile(open(make_testdata_filename('bad-3.tar.gz')).read())
        except IncorrectTarFile, e:
            self.assert_('has incorrect contents' in e.args[0])
        else:
            self.fail('no exception raised')

    def test_bad_tarball_4(self):
        # should fail due to the wrapper dir not having the right name
        try:
            TarMission.check_tarfile(open(make_testdata_filename('bad-4.tar.gz')).read())
        except IncorrectTarFile, e:
            self.assert_('Wrapper directory name is incorrect' in e.args[0])
        else:
            self.fail('no exception raised')


class TarUploadTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_tar_file_downloads(self):
        for filename, content in TarMission.FILES.iteritems():
            response = self.client.get(reverse(tar_file_download, kwargs={'name': filename}))
            self.assertEqual(response['Content-Disposition'], 'attachment; filename=%s' % filename)
            self.assertEqual(response.content, content)

    def test_tar_file_download_404(self):
        response = self.client.get(reverse(tar_file_download, kwargs={'name': 'doesnotexist.c'}))
        self.assertEqual(response.status_code, 404)

    def test_tar_upload_good(self):
        response = self.client.post(reverse(tar_upload), {'tarfile': open(make_testdata_filename('good.tar.gz'))})
        self.assert_('status: success' in response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 1)

        # Make sure that nothing weird happens if it is submitted again.
        response = self.client.post(reverse(tar_upload), {'tarfile': open(make_testdata_filename('good.tar.gz'))})
        self.assert_('status: success' in response.content)
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 1)

    def test_tar_upload_bad(self):
        response = self.client.post(reverse(tar_upload), {'tarfile': open(make_testdata_filename('bad-1.tar.gz'))})
        self.assert_('status: failure' in response.content)

        paulproteus = Person.objects.get(user__username='paulproteus')
        self.assertEqual(len(StepCompletion.objects.filter(step__name='tar', person=paulproteus)), 0)


class MainPageTests(TwillTests):
    fixtures = ['person-paulproteus', 'user-paulproteus']

    def setUp(self):
        TwillTests.setUp(self)
        self.client = self.login_with_client()

    def test_mission_completion_list_display(self):
        response = self.client.get(reverse(main_page))
        self.assertEqual(response.context['completed_missions'], {})

        paulproteus = Person.objects.get(user__username='paulproteus')
        StepCompletion(person=paulproteus, step=Step.objects.get(name='tar')).save()

        response = self.client.get(reverse(main_page))
        self.assertEqual(response.context['completed_missions'], {'tar': True})


class UntarMissionTests(TestCase):

    def test_tarball_contains_file_we_want(self):
        tfile = tarfile.open(UntarMission.get_tar_path(), mode='r:gz')

        # Check the file we want contains the right thing.
        file_we_want = tfile.getmember(UntarMission.FILE_WE_WANT)
        self.assert_(file_we_want.isfile())
        self.assertEqual(tfile.extractfile(file_we_want).read(), UntarMission.get_contents_we_want())
