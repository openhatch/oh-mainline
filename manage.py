#!/usr/bin/env python
import os
import sys

if not os.path.exists('mysite/manage.py'):
    # Try one more thing -- chdir() into the path of this file
    # and try to find mysite/manage.py. Note that chdir()ing is
    # a somewhat intense strategy here.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists('mysite/manage.py'):   
        print "Eek, where is the real manage.py? Quitting."
        sys.exit(1)

execfile('mysite/manage.py', globals(), locals())
