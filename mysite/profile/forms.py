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


class ManuallyAddACitationForm(django.forms.ModelForm):
    portfolio_entry = django.forms.ModelChoiceField(
        queryset=mysite.profile.models.PortfolioEntry.objects.all(),
        widget=django.forms.HiddenInput())

    # The ID of the element in the portfolio editor that contains this form.
    form_container_element_id = django.forms.CharField(
        widget=django.forms.HiddenInput())
    # FIXME: Make is_published always true

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
        # By now this is an object, not an ID.
        pf_entry = self.cleaned_data['portfolio_entry']
        if pf_entry.person.user == self.user:
            return pf_entry
        else:
            raise django.forms.ValidationError("Somehow, you submitted "
                                               "regarding a portfolio entry that you do not own.")


class EditInfoForm(django.forms.Form):
    bio = django.forms.CharField(
        required=False,
        widget=django.forms.Textarea(
            attrs={
                'placeholder':'I like traffic lights. On weekends, I like to make websites, destroy Twitter, and eat breakfast.'
            }
        )
    )
    homepage_url = django.forms.URLField(
        required=False,
        widget=django.forms.TextInput(
            attrs=
                {
                    'placeholder':'www.github.io/myAccountName',
                    'size':'40',
                 }
        )
    )
    irc_nick = django.forms.CharField(
        required=False,
        widget=django.forms.TextInput(
            attrs=
                {
                    'placeholder':'your_irc_nick',
                    'size':'40',
                }
        )
    )
    understands = django.forms.CharField(
        required=False,
        widget=django.forms.Textarea(
            attrs=
                {
                    'placeholder':'ruby, wordpress, regular expressions, classical guitar',
                }
        )
    )
    understands_not = django.forms.CharField(
        required=False,
        widget=django.forms.Textarea(
                attrs=
                    {
                        'placeholder':'Swing, Star Trek, the transcendental deduction, why kids love Cinnamon Toast Crunch',
                    }
        )
    )
    studying = django.forms.CharField(
        required=False,
        widget=django.forms.Textarea(
            attrs=
                {
                    'placeholder':'Qt, DVD DRM circumvention, Bayesian inference, neural networks',
                }
        )
    )
    can_pitch_in = django.forms.CharField(
        required=False,
        widget=django.forms.Textarea(
            attrs=
                {
                    'placeholder':'documentation, testing, c++, mac compatibility, design',
                }
        )
    )
    can_mentor = django.forms.CharField(
        required=False,
        widget=django.forms.Textarea(
            attrs=
                {
                    'placeholder':'python, unicode, git, GTK+',
                }
        )
    )


class ContactBlurbForm(django.forms.Form):
    contact_blurb = django.forms.CharField(
        required=False,
        widget=django.forms.Textarea(
            attrs=
                {
                    'placeholder':'The best way to reach me is by private message on Twitter, email, and/or IRC.',
                }
        )
    )


class UseDescriptionFromThisPortfolioEntryForm(django.forms.ModelForm):

    class Meta:
        model = mysite.profile.models.PortfolioEntry
        fields = ('use_my_description', )


class DeleteUser(django.forms.Form):
    username = django.forms.CharField(required=True,
                                      widget=django.forms.Textarea())

# vim: set nu:
