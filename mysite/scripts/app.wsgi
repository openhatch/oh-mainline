#!/usr/bin/env python
import os
import os.path
import sys
import logging

# I know this is weird, but let us chdir() up to where
# the settings file is.
base_path = os.path.abspath(os.path.join(__file__, '../../..'))
print >> sys.stderr, base_path
os.chdir(base_path)

# Make sure we can find the settings module...
assert os.path.exists('mysite/settings.py')

# Okay, let us vendorify!
sys.path.insert(0, os.path.abspath('.'))
import vendor
vendor.vendorify()

# Now it is safe to import things.
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
