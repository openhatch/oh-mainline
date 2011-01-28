# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
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

import simplejson
import urllib
import os
import os.path
import shutil
import tempfile
import datetime
import dateutil.parser
import subprocess

from django.http import HttpResponse
import django.shortcuts
from django.template import RequestContext
import django.conf

def json_response(python_object):
    json = simplejson.dumps(python_object)
    return HttpResponse(json, mimetype="application/json")

class ObjectFromDict(object):
    def __init__(self, data, recursive = False):
        for key in data:
            if recursive:
                if type(data[key]) == type({}):
                    data[key] = ObjectFromDict(data[key], recursive=recursive)
                elif type(data[key]) == type([]):
                    data[key] = [ObjectFromDict(item, recursive=recursive) for item in data[key]]
            setattr(self, key, data[key])

def sanitize_wide_unicode(data):
    # Recurse on dicts and lists.
    if type(data) == type({}):
        for key in data:
            data[key] = sanitize_wide_unicode(data[key])
    elif type(data) == type([]):
        data = [sanitize_wide_unicode(item) for item in data]
    elif type(data) == type(u''):
        # Replace any wide unicode or surrogate code points with a unicode question mark.
        data = u''.join(c if not (0xD800 <= ord(c) <= 0xDFFF or ord(c) >= 0x10000) else u'\ufffd' for c in data)
    return data

def assert_or_pdb(expression):
    if expression:
        pass
    else:
        if 'LOTSA_PDB' in os.environ:
            import pdb
            pdb.set_trace()
        else:
            raise ValueError, "eek"

def string2naive_datetime(s):
    time_zoned = dateutil.parser.parse(s)
    if time_zoned.tzinfo:
        d_aware = time_zoned.astimezone(dateutil.tz.tzutc())
        d = d_aware.replace(tzinfo=None)
    else:
        d = time_zoned # best we can do
    return d

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return django.shortcuts.render_to_response(*args, **kwargs)

def clear_static_cache(path):
    '''Atomically destroy the static file cache for a certain path.'''
    # Steps:
    fully_qualified_path = os.path.join(settings.WEB_ROOT, path)

    # 0. Create new temp dir
    new_temp_path = tempfile.mkdtemp(settings.WEB_ROOT)

    # 1. Atomically move the path that we want to expire into the new directory
    try:
        os.rename(fully_qualified_path, os.path.join(new_temp_path, 'old'))
    except OSError, e:
        if e.errno == 2: # No such file or directory
            # Well, that means the cache is already clear.
            # We still have to nuke new_temp_path though!
            pass

    # 2. shutil.rmtree() the new path
    shutil.rmtree(new_temp_path)

# Implementation of something like subprocess.check_output, which didn't
# get added to the Python standard library until 2.7.
def subproc_check_output(*args, **kw):
    if 'stdout' in kw:
        raise ValueError, 'stdout must not be specified'
    kw['stdout'] = subprocess.PIPE
    subproc = subprocess.Popen(*args, **kw)
    output = subproc.stdout.read()
    if subproc.wait() != 0:
        raise RuntimeError, 'subprocess failed with return code %d' % subproc.returncode
    return output
