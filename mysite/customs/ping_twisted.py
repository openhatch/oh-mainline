# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
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

# We use Twisted to get pages from the web.
# The point of this file is to make it easy to tell Twisted,
# "Hey, you have more work to do."

from django.conf import settings
import os

def directory():
    return os.path.join(settings.MEDIA_ROOT, 'twisted-ping-dir')

def filename():
    return os.path.join(directory(), 'twisted-ping-file')

def ping_it():
    fd = open(filename(), 'a')
    fd.close()
