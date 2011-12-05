# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
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
import mysite.customs.models
import mysite.customs.forms

all_trackers = {
        'bugzilla': {
            'namestr': 'Bugzilla',
            'model': mysite.customs.models.BugzillaTrackerModel,
            'form': mysite.customs.forms.BugzillaTrackerForm,
            'urlmodel': mysite.customs.models.BugzillaQueryModel,
            'urlform': mysite.customs.forms.BugzillaQueryForm,
            },
        'google': {
            'namestr': 'Google Code',
            'model': mysite.customs.models.GoogleTrackerModel,
            'form': mysite.customs.forms.GoogleTrackerForm,
            'urlmodel': mysite.customs.models.GoogleQueryModel,
            'urlform': mysite.customs.forms.GoogleQueryForm,
            },
        'roundup': {
            'namestr': 'Roundup',
            'model': mysite.customs.models.RoundupTrackerModel,
            'form': mysite.customs.forms.RoundupTrackerForm,
            'urlmodel': mysite.customs.models.RoundupQueryModel,
            'urlform': mysite.customs.forms.RoundupQueryForm,
            },
        'trac': {
            'namestr': 'Trac',
            'model': mysite.customs.models.TracTrackerModel,
            'form': mysite.customs.forms.TracTrackerForm,
            'urlmodel': mysite.customs.models.TracQueryModel,
            'urlform': mysite.customs.forms.TracQueryForm,
            },
        'launchpad': {
            'namestr': 'Launchpad',
            'model': mysite.customs.models.LaunchpadTrackerModel,
            'form':  mysite.customs.forms.LaunchpadTrackerForm,
            'urlmodel': mysite.customs.models.LaunchpadQueryModel,
            'urlform': mysite.customs.forms.LaunchpadQueryForm,
            },
        }
