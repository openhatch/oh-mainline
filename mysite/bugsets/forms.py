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
from django.core.exceptions import ObjectDoesNotExist


class BugsForm(django.forms.Form):
    event_name = django.forms.CharField(max_length=200)
    buglist = django.forms.CharField(
        widget=django.forms.Textarea,
        label='Enter some bugs URLs here, each separated by a newline:',
    )

    @staticmethod
    def bug_list_from_set(bugset):
        return [bug.url for bug in bugset.bugs.all()]

    @staticmethod
    def url_list_from_bugtext(bugtext):
        """
        Convert newline-delimited text blob into list of URLs.

        What is happening here?!
        1. Split the hunk of text on newlines
        2. Strip all the strings of leading/trailing whitespace
        3. Filter out all empty strings by passing the first-order function
           "bool" (to see why: bool(x) == False if and only if x == "")
        """
        return filter(bool, [x.strip() for x in bugtext.split("\n")])

    @staticmethod
    def is_valid_url(x):
        u = URLValidator()

        try:
            u(x)
        except django.forms.ValidationError:
            return False
        return True

    def __init__(self, *args, **kwargs):
        # FIXME: Our home-baked "ModelForm" could be implemented with django
        # ModelForms, but the m2m text blob of URLs will be tricky to work with
        self.pk = kwargs.get('pk')
        self.object = None

        if self.pk is not None:
            kwargs.pop('pk')
            self.object = mysite.bugsets.models.BugSet.objects.get(pk=self.pk)

            if kwargs.get('data') is None:
                data = {
                    'event_name': self.object.name,
                    'buglist': "\n".join(
                        BugsForm.bug_list_from_set(self.object)),
                }
                kwargs['data'] = data

        super(BugsForm, self).__init__(*args, **kwargs)

    def clean_buglist(self):
        # If this corresponds to an existing set, fetch it
        if self.object is not None:
            return self.cleaned_data['buglist']

        bugtext = self.cleaned_data['buglist']

        # Turn the list into a set to filter out duplicates
        buglist = set(BugsForm.url_list_from_bugtext(bugtext))

        if not all([BugsForm.is_valid_url(url) for url in buglist]):
            raise django.forms.ValidationError(
                "You have entered an invalid URL: " + url)  # evil

        # Put this back into text blob format
        return "\n".join(buglist)

    def save(self):
        s = mysite.bugsets.models.BugSet(
            name=self.cleaned_data.get('event_name'))
        s.save()

        for url in self.cleaned_data.get('buglist').split("\n"):
            # get_or_create returns a tuple (object b, bool created?)
            b = mysite.bugsets.models.AnnotatedBug.objects.get_or_create(
                url=url)[0]

            try:
                o = mysite.search.models.Bug.all_bugs.get(
                    canonical_bug_link=url)

                b.title = o.title
                b.description = o.description
                b.project = o.project

                if o.project:
                    b.skill_list = o.project.language
            except ObjectDoesNotExist:
                # No problems here, this URL wasn't cached in our main db
                pass

            b.save()
            s.bugs.add(b)

        # We need the form to return the set info
        self.object = s

    def update(self):
        s = self.object
        old_name = s.name
        old_bugs = set(BugsForm.bug_list_from_set(s))

        new_name = self.cleaned_data.get('event_name')
        new_bugs = set(BugsForm.url_list_from_bugtext(
            self.cleaned_data.get('buglist')))

        if old_name != new_name:
            s.name = new_name
            s.save()

        for bug in old_bugs - new_bugs:
            s.bugs.remove(mysite.bugsets.models.AnnotatedBug.objects.get(
                url=bug))

        for bug in new_bugs - old_bugs:
            b = mysite.bugsets.models.AnnotatedBug.objects.get_or_create(
                url=bug)[0]
            s.bugs.add(b)
