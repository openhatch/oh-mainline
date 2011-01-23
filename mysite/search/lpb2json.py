# This file is part of OpenHatch.
# Copyright (C) 2009, 2010 OpenHatch, Inc.
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

import launchpadbugs.text_bug
import launchpadbugs.lphelper
import types

## Note that this sucks, and is not directly tested.

def obj2serializable(obj):
    if type(obj) in (bool, unicode, int, types.NoneType):
        return obj
    elif type(obj) == str:
        return unicode(obj, 'utf-8')
    elif type(obj) == set:
        return list(obj)
    elif type(obj) == launchpadbugs.lphelper.product:
        return unicode(obj.title())
    elif type(obj) == launchpadbugs.text_bug.Bug:
        growing = {}
        keys = ['affects', 'assignee', 'bugnumber',
                # skip attachments for now; kinda tough
                'comments', 'date', 'date_reported', 'date_updated',
                'description', 'duplicate_of', 'duplicates', 'importance',
                # do grab 'tags
                'tags',
                # skip 'info'
                # skip 'mentors because it's NotImplemented
                'milestone', 'reporter', 'security', 
	        'date', 'affects', 'summary', 'sourcepackage', 'status', 'url', 'reporter', 'private', 'sourcepackage',
                'title', 'text', 'comments']
        for key in keys:
            try:
                growing[key] = obj2serializable(getattr(obj, key))
            except AttributeError:
                growing[key] = None
        return growing
    elif type(obj) == launchpadbugs.lphelper.user:
        growing = {}
        keys = ['realname', 'lplogin']
        for key in keys:
            growing[key] = obj2serializable(getattr(obj, key))
        return growing
    elif type(obj) == launchpadbugs.text_bug.Comments:
        growing = []
        for thing in obj:
            growing.append(obj2serializable(thing))
        return growing
    elif type(obj) == launchpadbugs.text_bug.Comment:
        growing = {}
        for key in ['text', 'user', 'date', 'number']:
            growing[key] = obj2serializable(getattr(obj, key))
        return growing
    elif type(obj) == launchpadbugs.lptime.LPTime:
        return list(obj.timetuple())
    elif type(obj) == list:
        return [unicode(k) for k in obj]
    else:
        raise AssertionError, "Not recognized: %s" % type(obj) 


