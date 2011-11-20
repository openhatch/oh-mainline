#!/usr/bin/env python
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
