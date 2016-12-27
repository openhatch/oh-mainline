#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    # The real manage.py is one directory up. So we switch to that directory, which
    # is admittedly a little odd. It means that we get consistent paths for things
    # like static assets no matter if you run manage.py or mysite/manage.py.
    os.chdir('..')

    # We have to add the new current working directory to sys.path, because
    # Python's sys.path was calculcated when this file (mysite/manage.py) was
    # started initially. We only really needs this for the vendor/ directory.
    sys.path.append(os.getcwd())

    # Now, act as though nothing is wrong.
    execfile('manage.py', globals(), locals())
