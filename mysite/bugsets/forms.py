# This file is part of OpenHatch.
# Copyright (C) 2014 Elana Hashman
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

import mysite.bugsets.models

import django.forms
from django.core.validators import URLValidator


class BugsForm(django.forms.Form):
    event_name = django.forms.CharField(max_length=200)
    buglist = django.forms.CharField(
        widget=django.forms.Textarea,
        label='Enter some bugs URLs here, each separated by a newline:',
    )

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.get('pk')
        if self.pk is not None:
            kwargs.pop('pk')
            data = {
                'event_name': mysite.bugsets.models.BugSet.objects.get(
                    pk=self.pk).name,
                'buglist': "\n".join([bug.url for bug in
                    mysite.bugsets.models.BugSet.objects.get(
                    pk=self.pk).bugs.all()])
            }
            kwargs['data'] = data

        super(BugsForm, self).__init__(*args, **kwargs)

    def clean_buglist(self):
        # If this corresponds to an existing set, fetch it
        if self.pk is not None:
            return self.cleaned_data['buglist']

        bugtext = self.cleaned_data['buglist']

        # What is happening here?!
        # 1. Split the hunk of text on newlines
        # 2. Strip all the strings of leading/trailing whitespace
        # 3. Filter out all empty strings by passing the first-order function
        #    "bool" (to see why: bool(x) == False if and only if x == "")
        # 4. Turn the list into a set to filter out duplicates
        buglist = set(filter(
            bool,
            [x.strip() for x in bugtext.split("\n")]
        ))

        u = URLValidator()

        def is_valid_url(x):
            try:
                u(x)
            except django.forms.ValidationError:
                return False
            return True

        # Use list generator () instead of comprehension [] for lazy evaluation
        if not all([is_valid_url(url) for url in buglist]):
            raise django.forms.ValidationError(
                "You have entered an invalid URL: " + url)  # evil

        # Put this back into text blob format
        return "\n".join(buglist)

    def save(self):
        s = mysite.bugsets.models.BugSet(
            name=self.cleaned_data.get('event_name'))
        s.save()

        for url in self.cleaned_data.get('buglist').split("\n"):
            b = mysite.bugsets.models.AnnotatedBug(url=url)
            b.save()
            s.bugs.add(b)

        # We need the form to return the set info
        self.object = s
