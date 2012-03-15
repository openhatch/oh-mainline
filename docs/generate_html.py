"""Generate html documentation"""

__requires__ = 'Sphinx>=1.1.2'

import sys,os,re,conf
from pkg_resources import load_entry_point


def main(argv=None):
    if argv:
        sys.argv = argv
    # Generate documentation
    return load_entry_point(__requires__, 'console_scripts',
        'sphinx-build')()

if __name__ == "__main__":
    sys.exit(main(['generate_html.py','-b','html','-d','_temp','.','html']))

