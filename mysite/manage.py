#!/usr/bin/env python
import os, sys

THIS_FILE = os.path.abspath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
UP_ONE_DIR = os.path.join(THIS_DIR, '..')
sys.path.append(UP_ONE_DIR)

# Use the modules in vendor/
import vendor
vendor.vendorify()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
