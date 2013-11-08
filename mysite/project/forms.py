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
import mysite.search.models
import mysite.profile.models


class WannaHelpForm(django.forms.Form):
    project = django.forms.ModelChoiceField(
        mysite.search.models.Project.objects.all())
    from_offsite = django.forms.BooleanField(required=False)


class MarkContactedForm(django.forms.Form):
    project_id = django.forms.IntegerField(widget=django.forms.HiddenInput())
    person_id = django.forms.IntegerField(widget=django.forms.HiddenInput())
    checked = django.forms.BooleanField(
        label="Mark person as contacted", required=True)

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

    def clean_name(self):

        proposed_name = self.cleaned_data['name'].strip()

        # Only save if nothing but capitalization was changed
        if (proposed_name.lower() != self.instance.name.lower()):
            raise django.forms.ValidationError(
                "You can only make changes to the capitalization of the name.")
        return proposed_name

    def clean_language(self):
        lang = self.cleaned_data['language']

        # Try to use the capitalization of a language already assigned to a
        # project
        matching_projects = mysite.search.models.Project.objects.filter(
            language__iexact=lang)
        if matching_projects:
            return matching_projects[0].language
        return lang

    class Meta:
        model = mysite.search.models.Project
        fields = ('name', 'display_name', 'homepage', 'language', 'icon_raw')
