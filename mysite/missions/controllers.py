from django import forms

import tarfile
from StringIO import StringIO
import os
import sys

def remove_slash_that_python_two_point_five_might_have_added(some_string):
    if sys.version_info[:2] == (2, 5):
        # zomg, geez. Let's ditch Python 2.5 real soon now.
        # Not because it's busted necessarily, but just because we could
        # stop wasting time on inter-Python-version compatibility code like...
        if some_string[-1] == '/':
            return some_string[:-1]
    return some_string

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
            name_as_if_this_were_python_two_point_six = remove_slash_that_python_two_point_five_might_have_added(member.name)

            if '/' not in name_as_if_this_were_python_two_point_six:
                if name_as_if_this_were_python_two_point_six in cls.FILES.keys():
                    raise IncorrectTarFile, 'No wrapper directory is present'
                elif member.isdir() and name_as_if_this_were_python_two_point_six != cls.WRAPPER_DIR_NAME:
                    raise IncorrectTarFile, 'Wrapper directory name is incorrect: "%s"' % name_as_if_this_were_python_two_point_six
            if name_as_if_this_were_python_two_point_six not in filenames_wanted:
                raise IncorrectTarFile, 'An unexpected entry "%s" is present' % name_as_if_this_were_python_two_point_six
            filenames_wanted.remove(name_as_if_this_were_python_two_point_six)
            if name_as_if_this_were_python_two_point_six == cls.WRAPPER_DIR_NAME:
                if not member.isdir():
                    raise IncorrectTarFile, '"%s" should be a directory but is not' % name_as_if_this_were_python_two_point_six
            else:
                if not member.isfile():
                    raise IncorrectTarFile, 'Entry "%s" is not a file' % name_as_if_this_were_python_two_point_six
                if tfile.extractfile(member).read() != cls.FILES[name_as_if_this_were_python_two_point_six.split('/')[-1]]:
                    raise IncorrectTarFile, 'File "%s" has incorrect contents' % name_as_if_this_were_python_two_point_six
        if len(filenames_wanted) != 0:
            raise IncorrectTarFile, 'Archive does not contain all expected files (missing %s)' % (', '.join('"%s"' % f for f in filenames_wanted))

class TarUploadForm(forms.Form):
    tarfile = forms.FileField(error_messages={'required': 'No file was uploaded.'})

class UntarMission(object):
    TARBALL_NAME = 'ghello-0.4.tar.gz'
    FILE_WE_WANT = 'ghello-0.4/ghello.c'

    @classmethod
    def get_tar_path(cls):
        return os.path.join(os.path.dirname(__file__), 'data', cls.TARBALL_NAME)

    @classmethod
    def get_contents_we_want(cls):
        '''Get the data for the file we want from the tarball.'''
        tfile = tarfile.open(cls.get_tar_path(), mode='r:gz')
        return tfile.extractfile(tfile.getmember(cls.FILE_WE_WANT)).read()
