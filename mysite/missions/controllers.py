from django import forms

import tarfile
from StringIO import StringIO
import os

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
        filenames_wanted = [cls.WRAPPER_DIR_NAME] + [cls.WRAPPER_DIR_NAME+'/'+filename for filename in cls.FILES.keys()]
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

class TarUploadForm(forms.Form):
    tarfile = forms.FileField(error_messages={'required': 'No file was uploaded.'})
