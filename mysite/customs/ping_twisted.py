# We use Twisted to get pages from the web.
# The point of this file is to make it easy to tell Twisted,
# "Hey, you have more work to do."

from django.conf import settings
import os

def directory():
    return os.path.join(settings.MEDIA_ROOT, 'twisted-ping-dir')

def filename():
    return os.path.join(directory(), 'twisted-ping-file')

def ping_it():
    fd = open(filename(), 'a')
    fd.close()
