# This file is part of OpenHatch.
# Copyright (C) 2009, 2010 OpenHatch
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
    homepage_url = django.forms.URLField(required=False)
    understands = django.forms.CharField(required=False, widget=django.forms.Textarea())
    understands_not = django.forms.CharField(required=False, widget=django.forms.Textarea())
    studying = django.forms.CharField(required=False, widget=django.forms.Textarea())
    can_pitch_in = django.forms.CharField(required=False, widget=django.forms.Textarea())
    can_mentor = django.forms.CharField(required=False, widget=django.forms.Textarea())

class ContactBlurbForm(django.forms.Form):
    contact_blurb = django.forms.CharField(required=False, widget=django.forms.Textarea())

class UseDescriptionFromThisPortfolioEntryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.profile.models.PortfolioEntry
        fields = ('use_my_description', )

# vim: set nu:
