#!/usr/bin/python
import sys, os
sys.path.append('/home/deploy/milestone-a')

try:
    import settings
except:
    sys.exit(1)

# Set the DJANGO_SETTINGS_MODULE environment variable.
os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")

