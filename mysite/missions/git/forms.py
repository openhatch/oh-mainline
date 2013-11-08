# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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
import re


class ConfigForm(django.forms.Form):
    BAD_ENDINGS = ['local', 'none', 'host']

    user_email = django.forms.EmailField()

    def clean_user_email(self):
        for ending in ConfigForm.BAD_ENDINGS:
            if self.cleaned_data['user_email'].endswith(ending):
                raise django.forms.ValidationError, (
                    'The email address is invalid '
                    'because it ends with %s' % (ending,))


class CheckoutForm(django.forms.Form):
    secret_word = django.forms.CharField(
        error_messages={'required': 'No author was given.'})


class DiffForm(django.forms.Form):
    diff = django.forms.CharField(
        error_messages={'required': 'No git diff output was given.'}, widget=django.forms.Textarea())

    def clean_diff(self):
        REGEX_DIFF_LINE = '\+print "[H,h]ello,?[ ]+[w,W]orld\!'
        success_count = re.search(REGEX_DIFF_LINE, self.cleaned_data['diff'])
        if success_count == None:
            raise django.forms.ValidationError, (
                "Something doesn't look right.The expected line is '+print... ' Give it another try!")
        return self.cleaned_data['diff']


class RebaseForm(django.forms.Form):
    secret_word = django.forms.CharField(
        error_messages={'required': 'The password was incorrect.'})
