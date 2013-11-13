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

import django.forms
from mysite.base.models import Organization, Duration, Skill, Language
import mysite.search.models
import mysite.profile.models
from file_resubmit.admin import AdminResubmitFileWidget

class WannaHelpForm(django.forms.Form):
    project = django.forms.ModelChoiceField(mysite.search.models.Project.objects.all())
    from_offsite = django.forms.BooleanField(required=False)

class MarkContactedForm(django.forms.Form):
    project_id = django.forms.IntegerField(widget=django.forms.HiddenInput())
    person_id = django.forms.IntegerField(widget=django.forms.HiddenInput())
    checked = django.forms.BooleanField(label="Mark person as contacted", required=True)

    # We are avoiding the use of ModelChoiceField.
    #
    # We use this custom validation code instead so that we can create
    # these form instances cheaply, without hitting the database, yet
    # we can still return valid ForeignKey IDs to users of this class.
    def clean_project_id(self):
        value = self.cleaned_data['project_id']
        if mysite.search.models.Project.objects.filter(
            id=value):
            return value
        raise django.forms.ValidationError, "Invalid project ID."

    def clean_person_id(self):
        value = self.cleaned_data['person_id']
        if mysite.profile.models.Person.objects.filter(
            id=value).count():
            return value
        raise django.forms.ValidationError, "Invalid person ID."

class ProjectForm(django.forms.ModelForm):
    name = django.forms.CharField(required=True, widget=django.forms.TextInput)
    display_name = django.forms.CharField(required=True, widget=django.forms.TextInput)
    language = django.forms.CharField(required=False, widget=django.forms.TextInput)
    homepage = django.forms.URLField(required=False)
    organization = django.forms.ModelChoiceField(required=True,
                                                 queryset=Organization.objects.all(),
                                                 widget=django.forms.Select)
    duration = django.forms.ModelChoiceField(required=True,
                                             queryset=Duration.objects.all(),
                                             widget=django.forms.Select)
    skills = django.forms.ModelMultipleChoiceField(required=True,
                                                   queryset=Skill.objects.all(),
                                                   widget=django.forms.CheckboxSelectMultiple)
    languages = django.forms.ModelMultipleChoiceField(required=True,
                                                      queryset=Language.objects.all(),
                                                      widget=django.forms.CheckboxSelectMultiple)
    icon_raw = django.forms.ImageField(required=False, widget=AdminResubmitFileWidget)
    id = django.forms.IntegerField(required=False)

    class Meta:
        model = mysite.search.models.Project
        fields = ("name", "display_name", "language", "homepage", "skills", "duration", "organization",
                  "languages", "icon_raw", "id")