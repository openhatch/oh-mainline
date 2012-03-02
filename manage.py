#!/usr/bin/python
import os
import sys

if not os.path.exists('mysite/manage.py'):
    print "Eek, where is the real manage.py? Quitting."
    sys.exit(1)

execfile('mysite/manage.py', globals(), locals())
