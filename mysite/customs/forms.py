# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
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

import mysite.search.models
import mysite.customs.models

class TrackerTypesForm(django.forms.Form):
    TRACKER_TYPES = (
            ('bugzilla', 'Bugzilla'),
            ('google', 'Google Code'),
            ('roundup', 'Roundup'),
            ('trac', 'Trac'),
            )
    tracker_type = django.forms.ChoiceField(choices=TRACKER_TYPES)

class BugzillaTrackerForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaTrackerModel

class TrackerFormThatHidesCreatedForProject(django.forms.ModelForm):
    created_for_project = django.forms.ModelChoiceField(
            queryset=mysite.search.models.Project.objects.all(),
            widget=django.forms.HiddenInput(),
            required=False)

class BugzillaQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaQueryModel
        exclude = ('tracker', 'last_polled',)

class GoogleTrackerForm(TrackerFormThatHidesCreatedForProject):
    class Meta:
        model = mysite.customs.models.GoogleTrackerModel

class GoogleQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.GoogleQueryModel
        exclude = ('tracker', 'last_polled',)

class TracTrackerForm(TrackerFormThatHidesCreatedForProject):
    class Meta:
        model = mysite.customs.models.TracTrackerModel

class TracQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.TracQueryModel
        exclude = ('tracker', 'last_polled',)

class RoundupTrackerForm(TrackerFormThatHidesCreatedForProject):
    class Meta:
        model = mysite.customs.models.RoundupTrackerModel

class RoundupQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.RoundupQueryModel
        exclude = ('tracker', 'last_polled',)
