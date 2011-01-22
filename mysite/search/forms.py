# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 OpenHatch
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

class BugAlertSubscriptionForm(django.forms.ModelForm):

    hidden_char_field = lambda: \
            django.forms.CharField(widget=django.forms.HiddenInput())

    query_string = hidden_char_field()
    how_many_bugs_at_time_of_request = hidden_char_field()

    email = django.forms.EmailField(
            label="Email address",
            error_messages={'invalid': 'This email address doesn\'t look right. Real or malarkey?'})

    class Meta:
        model = mysite.search.models.BugAlert
        fields = ('query_string', 'email', 'how_many_bugs_at_time_of_request')
