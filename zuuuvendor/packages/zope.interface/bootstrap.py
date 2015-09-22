##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Bootstrap a buildout-based project

Simply run this script in a directory containing a buildout.cfg.
The script accepts buildout command-line options, so you can
use the -c option to specify an alternate configuration file.
"""

import os, shutil, sys, tempfile, urllib2

tmpeggs = tempfile.mkdtemp()

ez = {}
exec urllib2.urlopen('http://peak.telecommunity.com/dist/ez_setup.py'
                     ).read() in ez
ez['use_setuptools'](to_dir=tmpeggs, download_delay=0)

import pkg_resources

is_jython = sys.platform.startswith('java')

if is_jython:
    import subprocess

cmd = 'from setuptools.command.easy_install import main; main()'
if sys.platform == 'win32':
    cmd = '"%s"' % cmd # work around spawn lamosity on windows

ws = pkg_resources.working_set

if is_jython:
    assert subprocess.Popen([sys.executable] + ['-c', cmd, '-mqNxd', tmpeggs,
    'zc.buildout'],
    env = dict(os.environ,
          PYTHONPATH=
          ws.find(pkg_resources.Requirement.parse('setuptools')).location
          ),
    ).wait() == 0

else:
    assert os.spawnle(
        os.P_WAIT, sys.executable, sys.executable,
        '-c', cmd, '-mqNxd', tmpeggs, 'zc.buildout',
        dict(os.environ,
            PYTHONPATH=
            ws.find(pkg_resources.Requirement.parse('setuptools')).location
            ),
        ) == 0

ws.add_entry(tmpeggs)
ws.require('zc.buildout')
import zc.buildout.buildout
zc.buildout.buildout.main(sys.argv[1:] + ['bootstrap'])
shutil.rmtree(tmpeggs)
