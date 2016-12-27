#!/usr/bin/env python
"""Generate html documentation"""

import sys, os,re

# Allow this script to find its doc config resource
docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../docs')
sys.path.insert(0,docs_path)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import conf
import vendor
vendor.vendorify()

from sphinx import main

if __name__ == "__main__":
    # generate rendered html on the docs/html directory.
    os.chdir(docs_path)
    sys.exit(main(['render_docs.py','-b','html','-d','_temp','.','html']))
