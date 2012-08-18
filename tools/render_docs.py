#!/usr/bin/env python
"""Generate html documentation"""

__requires__ = 'Sphinx>=1.1.2'

import sys,os,re
from pkg_resources import load_entry_point

# Allow this script to find its doc config resource
docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../docs')
sys.path.insert(0,docs_path)

import conf

def main(argv=None):
    if argv:
        sys.argv = argv
    # Generate documentation
    return load_entry_point(__requires__, 'console_scripts',
        'sphinx-build')()

if __name__ == "__main__":

    # generate rendered html on the docs/html directory.
    os.chdir(docs_path)
    sys.exit(main(['render_docs.py','-b','html','-d','_temp','.','html']))

