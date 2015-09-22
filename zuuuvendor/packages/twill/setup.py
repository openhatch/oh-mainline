#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    print '(WARNING: importing distutils, not setuptools!)'
    from distutils.core import setup

#### twill info.

setup(name = 'twill',
      
      version = '0.9.1-cc',
      download_url = 'http://darcs.idyll.org/~t/projects/twill-0.9.tar.gz',
      
      description = 'twill Web browsing language',
      author = 'C. Titus Brown',
      author_email = 'titus@idyll.org',
      license='MIT',

      packages = ['twill', 'twill.other_packages',
                  'twill.other_packages._mechanize_dist',
                  'twill.extensions',
                  'twill.extensions.match_parse'],

      # allow both 
      entry_points = dict(console_scripts=['twill-sh = twill.shell:main'],),
      scripts = ['twill-fork'],
      
      maintainer = 'C. Titus Brown',
      maintainer_email = 'titus@caltech.edu',

      url = 'http://twill.idyll.org/',
      long_description = """\
A scripting system for automating Web browsing.  Useful for testing
Web pages or grabbing data from password-protected sites automatically.
""",
      classifiers = ['Development Status :: 4 - Beta',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'Intended Audience :: System Administrators',
                     'License :: OSI Approved :: MIT License',
                     'Natural Language :: English',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Programming Language :: Other Scripting Engines',
                     'Topic :: Internet :: WWW/HTTP',
                     'Topic :: Software Development :: Testing',
                     ],

      test_suite = 'nose.collector'
      )
