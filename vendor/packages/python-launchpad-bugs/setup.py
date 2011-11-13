#!/usr/bin/env python

# Written by Henrik Nilsen Omma
# (C) Canonical, Ltd. Licensed under the GPL

from distutils.core import setup
import os
import re

# look/set what version we have
changelog = "debian/changelog"
if os.path.exists(changelog):
    head=open(changelog).readline()
    match = re.compile(".*\((.*)\).*").match(head)
    if match:
        version = match.group(1)

### <Asheesh hack>
# or, whatever, just set version to a reasonable-looking number
# later versions of this tar.gz hopefully won't have this nonsense.
version='0.3.6.openhatch1'
### </Asheesh>
   
setup(name='python-launchpad-bugs',
      version=version,
      packages=['launchpadbugs'],
)

