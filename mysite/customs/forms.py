# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
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

import django.forms

import mysite.customs.models

class TrackerTypesForm(django.forms.Form):
    TRACKER_TYPES = (
            ('bugzilla', 'Bugzilla'),
            ('google', 'Google Code'),
            ('trac', 'Trac')
            )
    tracker_type = django.forms.ChoiceField(choices=TRACKER_TYPES)

class BugzillaTrackerForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaTracker

class BugzillaUrlForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaUrl
        exclude = ('tracker',)

class GoogleTrackerForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.GoogleTracker

class GoogleQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.GoogleQuery
        exclude = ('tracker',)
