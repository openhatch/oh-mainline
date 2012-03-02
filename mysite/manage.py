#!/usr/bin/env python

### We must chdir() up one level.
import os
import os.path
import sys
THIS_FILE=os.path.abspath(__file__)
THIS_DIR=os.path.dirname(THIS_FILE)
UP_ONE_DIR=os.path.join(THIS_DIR, '..')
sys.path.append(UP_ONE_DIR)

# Use the modules in vendor/
import vendor
vendor.vendorify()

# Now we can import from third-party libraries.
from django.core.management import execute_manager, setup_environ

import mysite.settings

# The first thing execute_manager does is call `setup_environ`.
setup_environ(mysite.settings)

if __name__ == "__main__":
    execute_manager(mysite.settings)
