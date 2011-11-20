#!/usr/bin/env python
import os
import sys

### I know this is weird, but let us chdir() up to where
### the settings file is.
os.path.chdir(os.path.abspath(__file__, '../..'))
assert os.path.exists('mysite/settings.py')

### Okay, let us vendorify!
import vendor
vendor.vendorify()

### Now it is safe to import things.
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
