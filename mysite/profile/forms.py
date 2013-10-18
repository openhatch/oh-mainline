# This file is part of OpenHatch.
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

import django.forms
import mysite.profile.models
from mysite.profile.models import  TimeToCommit, Heard_From, Language, Organization, Cause, Skill, Experience
from mysite.search.models import Project


class ManuallyAddACitationForm(django.forms.ModelForm):
    portfolio_entry = django.forms.ModelChoiceField(
            queryset=mysite.profile.models.PortfolioEntry.objects.all(), 
            widget=django.forms.HiddenInput())

    # The ID of the element in the portfolio editor that contains this form.
    form_container_element_id = django.forms.CharField(widget=django.forms.HiddenInput())
    #FIXME: Make is_published always true
    class Meta:
        model = mysite.profile.models.Citation
        fields = ('portfolio_entry', 'url', )

    def set_user(self, user):
        self.user = user

    def clean_portfolio_entry(self):
        '''Note: I will explode violently if you
        have not set self.user.'''
        # Assert that self.user is set
        try:
            self.user
        except AttributeError:
            raise django.forms.ValidationError("For some reason, the programmer made a mistake, "
                    "and I will blame you, the user.")

            # Check that the user owns this portfolio entry.
        pf_entry = self.cleaned_data['portfolio_entry'] # By now this is an object, not an ID.
        if pf_entry.person.user == self.user:
            return pf_entry
        else:
            raise django.forms.ValidationError("Somehow, you submitted "
                    "regarding a portfolio entry that you do not own.")

class EditInfoForm(django.forms.Form):

    bio = django.forms.CharField(required=False, widget=django.forms.Textarea())
    can_mentor = django.forms.CharField(required=False, widget=django.forms.Textarea())
    can_pitch_in = django.forms.CharField(required=False, widget=django.forms.Textarea())
    causes = django.forms.ModelMultipleChoiceField(
        required=False, queryset=Cause.objects.all(), widget=django.forms.CheckboxSelectMultiple)
    comment = django.forms.CharField(required=False, widget=django.forms.Textarea())
    company_name = django.forms.CharField(required=False, widget=django.forms.TextInput())
    experience = django.forms.ModelChoiceField(
        required=False, empty_label=None, queryset=Experience.objects.all(),widget=django.forms.RadioSelect())
    github_name = django.forms.CharField(required=False, widget=django.forms.TextInput())
    google_code_name = django.forms.CharField(required=False, widget=django.forms.TextInput())
    heard_from = django.forms.ModelMultipleChoiceField(
        required=False, queryset=Heard_From.objects.all(), widget=django.forms.CheckboxSelectMultiple)
    homepage_url = django.forms.URLField(required=False)
    irc_nick = django.forms.CharField(required=False, widget=django.forms.TextInput())
    language_spoken = django.forms.CharField(required=False, widget=django.forms.TextInput())
    languages = django.forms.ModelMultipleChoiceField(
        required=False, queryset=Language.objects.all(), widget=django.forms.CheckboxSelectMultiple)
    linked_in_url = django.forms.URLField(required=False)
    open_source = django.forms.BooleanField(required=False)
    organizations = django.forms.ModelMultipleChoiceField(
        required=False, queryset=Organization.objects.all(), widget=django.forms.CheckboxSelectMultiple)
    other_name = django.forms.CharField(required=False, widget=django.forms.TextInput())
    private = django.forms.BooleanField(required=False)
    resume = django.forms.FileField(required=False)
    studying = django.forms.CharField(required=False, widget=django.forms.Textarea())
    subscribed = django.forms.BooleanField(required=False)
    times_to_commit = django.forms.ModelChoiceField(
        required=False, empty_label=None, queryset=TimeToCommit.objects.all(),widget=django.forms.RadioSelect())
    understands = django.forms.CharField(required=False, widget=django.forms.Textarea())
    understands_not = django.forms.CharField(required=False, widget=django.forms.Textarea())
    skills = django.forms.ModelMultipleChoiceField(
        required=False, queryset=Skill.objects.all(),widget=django.forms.CheckboxSelectMultiple)

class ContactBlurbForm(django.forms.Form):
    contact_blurb = django.forms.CharField(required=False, widget=django.forms.Textarea())

class UseDescriptionFromThisPortfolioEntryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.profile.models.PortfolioEntry
        fields = ('use_my_description', )

class DeleteUser(django.forms.Form):
    username = django.forms.CharField(required=True,
                                      widget=django.forms.Textarea())

class SelectProjectsModelMultipleChoiceField(django.forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class SelectProjectsForm(django.forms.Form):
    Projects = SelectProjectsModelMultipleChoiceField(
        required=False, queryset=Project.objects.all(),widget=django.forms.CheckboxSelectMultiple)

# vim: set nu:
