#!/usr/bin/python
import os, sys

os.chdir('/home/deploy/milestone-a/mysite')
sys.path.append('/home/deploy/milestone-a')
sys.path.append('/home/deploy/milestone-a/mysite/')

os.environ['PYTHON_EGG_CACHE'] = '/tmp/egg-cache'

os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.deployment_settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

