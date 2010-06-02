from unittest import TestCase
from mysite.missions.controllers import TarMission, IncorrectTarFile

import os

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

