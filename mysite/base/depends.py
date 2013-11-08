# -*- coding: utf-8 -*-

# This file is part of OpenHatch.
# Copyright (C) 2011 Asheesh Laroia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This file exists to wrap some dependencies for other parts of the code.
#
# In general, core parts of the OpenHatch site are forbidden from importing
# some hard-to-install modules, like lxml. Those files import from here
# instead so that if the import fails, the site doesn't crash.
#
# This is so that new contributors can run the OpenHatch site without
# installing these hard-to-install dependencies.

# Used within this file
import os
import logging

# Wrap lxml and the modules that are part of it


class nothing(object):
    pass

try:
    import lxml
    import lxml.etree
    import lxml.html
except:
    lxml = nothing()
    lxml.etree = None
    lxml.html = None

if lxml.html is None:
    logging.info("Some parts of the OpenHatch site may fail because the lxml"
                 " library is not installed. Look in ADVANCED_INSTALLATION.mkd for"
                 " information about lxml.")

# Provide a helper to check if svnadmin is available. If not,
# we can skip running code (and tests) that require it.


def svnadmin_available():
    # FIXME: This should move to a variable controlled
    # by settings.py.
    SVNADMIN_PATH = '/usr/bin/svnadmin'
    return os.path.exists(SVNADMIN_PATH)

# Here we try to import "Image", from the Python Imaging Library.
# If we fail, Image is None.
Image = None
try:
    import Image
except:
    try:
        from PIL import Image
    except ImportError:
        # Okay, for a good time, let's hack sys.modules.
        # This permits Django to think ImageFields might
        # possibly work.
        import sys
        sys.modules['Image'] = sys.modules['sys']


def postmap_available(already_emitted_warning=[]):
    # Module-level state is used to track if we already emitted the warning.
    # It is not thread-safe, but it sure is convenient.
    POSTMAP_PATH = '/usr/sbin/postmap'
    if not os.path.exists(POSTMAP_PATH):
        if already_emitted_warning:
            pass
        else:
            already_emitted_warning.append(True)
            logging.warning(
                'postmap binary not found at {0}. Look in ADVANCED_INSTALLATION for the section about postfix for more information.'.format(POSTMAP_PATH))
        return False
    return True
