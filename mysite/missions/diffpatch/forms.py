# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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

import django.forms

class PatchSingleUploadForm(django.forms.Form):
    patched_file = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})

class DiffSingleUploadForm(django.forms.Form):
    diff = django.forms.CharField(error_messages={'required': 'No diff output was given.'}, widget=django.forms.Textarea())

class DiffRecursiveUploadForm(django.forms.Form):
    diff = django.forms.FileField(error_messages={'required': 'No file was uploaded.'})

class PatchRecursiveUploadForm(django.forms.Form):
    children_hats = django.forms.IntegerField()
    lizards_hats = django.forms.IntegerField()
