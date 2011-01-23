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

from mysite.missions.base.controllers import *

class IncorrectTarFile(Exception):
    pass

class TarMission(object):
    WRAPPER_DIR_NAME = 'myproject-0.1'
    FILES = {
      'hello.c': '''#include <stdio.h>

int main(void)
{
  printf("Hello World\\n");
  return 0;
}
''',
      'Makefile': 'hello : hello.o\n'
    }

    @classmethod
    def check_tarfile(cls, tardata):
        """
        Validate that tardata is gzipped and contains the correct files in a wrapper directory.
        """
        try:
            tfile = tarfile.open(fileobj=StringIO(tardata), mode='r:gz')
        except tarfile.ReadError:
            raise IncorrectTarFile, 'Archive is not a valid gzipped tarball'

        # Check the filename list.
        filenames_wanted = [cls.WRAPPER_DIR_NAME] + [os.path.join(cls.WRAPPER_DIR_NAME, filename) for filename in cls.FILES.keys()]
        for member in tfile.getmembers():
            if '/' not in member.name:
                if member.name in cls.FILES.keys():
                    raise IncorrectTarFile, 'No wrapper directory is present'
                elif member.isdir() and member.name != cls.WRAPPER_DIR_NAME:
                    raise IncorrectTarFile, 'Wrapper directory name is incorrect: "%s"' % member.name
            if member.name not in filenames_wanted:
                raise IncorrectTarFile, 'An unexpected entry "%s" is present' % member.name
            filenames_wanted.remove(member.name)
            if member.name == cls.WRAPPER_DIR_NAME:
                if not member.isdir():
                    raise IncorrectTarFile, '"%s" should be a directory but is not' % member.name
            else:
                if not member.isfile():
                    raise IncorrectTarFile, 'Entry "%s" is not a file' % member.name
                if tfile.extractfile(member).read() != cls.FILES[member.name.split('/')[-1]]:
                    raise IncorrectTarFile, 'File "%s" has incorrect contents' % member.name
        if len(filenames_wanted) != 0:
            raise IncorrectTarFile, 'Archive does not contain all expected files (missing %s)' % (', '.join('"%s"' % f for f in filenames_wanted))

class UntarMission(object):
    TARBALL_DIR_NAME = 'ghello-0.4'
    TARBALL_NAME = TARBALL_DIR_NAME + '.tar.gz'
    FILE_WE_WANT = TARBALL_DIR_NAME + '/ghello.c'

    @classmethod
    def synthesize_tarball(cls):
        tdata = StringIO()
        tfile = tarfile.open(fileobj=tdata, mode='w:gz')
        tfile.add(os.path.join(get_mission_data_path('tar'), cls.TARBALL_DIR_NAME), cls.TARBALL_DIR_NAME)
        tfile.close()
        return tdata.getvalue()

    @classmethod
    def get_contents_we_want(cls):
        '''Get the data for the file we want from the tarball.'''
        return open(os.path.join(get_mission_data_path('tar'), cls.FILE_WE_WANT)).read()

