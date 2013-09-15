# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
# Copyright (C) 2012 John Morrissey
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

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
import django.forms
import re
import mysite.search.models
import mysite.customs.models

class TrackerTypesForm(django.forms.Form):
    TRACKER_TYPES = (
            ('bugzilla', 'Bugzilla'),
            ('github', 'GitHub'),
            ('google', 'Google Code'),
            ('launchpad', 'Launchpad'),
            ('roundup', 'Roundup'),
            ('trac', 'Trac'),
            )
    tracker_type = django.forms.ChoiceField(choices=TRACKER_TYPES,
            widget=django.forms.Select(attrs={
                    'onchange': 'this.form.submit(); return false;'
                }))

class BugzillaTrackerForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaTrackerModel

class TrackerFormThatHidesCreatedForProject(django.forms.ModelForm):
    created_for_project = django.forms.ModelChoiceField(
            queryset=mysite.search.models.Project.objects.all(),
            widget=django.forms.HiddenInput(),
            required=False)

class BugzillaQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.BugzillaQueryModel
        exclude = ('tracker', 'last_polled',)

class GoogleTrackerForm(TrackerFormThatHidesCreatedForProject):
    class Meta:
        model = mysite.customs.models.GoogleTrackerModel

class GoogleQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.GoogleQueryModel
        exclude = ('tracker', 'last_polled',)

class TracTrackerForm(TrackerFormThatHidesCreatedForProject):
    class Meta:
        model = mysite.customs.models.TracTrackerModel

class TracQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.TracQueryModel
        exclude = ('tracker', 'last_polled',)

class RoundupTrackerForm(TrackerFormThatHidesCreatedForProject):
    class Meta:
        model = mysite.customs.models.RoundupTrackerModel

class RoundupQueryForm(django.forms.ModelForm):
    class Meta:
        model = mysite.customs.models.RoundupQueryModel
        exclude = ('tracker', 'last_polled',)

class LaunchpadTrackerForm(TrackerFormThatHidesCreatedForProject):
    max_connections = django.forms.IntegerField(
        widget=django.forms.HiddenInput(), initial=8)
    custom_parser = django.forms.CharField(
        widget=django.forms.HiddenInput(), required=False)
    class Meta:
        model = mysite.customs.models.LaunchpadTrackerModel

    def save(self, *args, **kwargs):
        # Call out to superclass
        obj = super(LaunchpadTrackerForm, self).save(*args, **kwargs)

        # In our case, now is a good time to make sure that a QueryModel gets created
        lqm, _ = mysite.customs.models.LaunchpadQueryModel.objects.get_or_create(tracker=obj)

        # Return the "upstream" return value
        return obj

class GitHubTrackerForm(TrackerFormThatHidesCreatedForProject):
    github_url = django.forms.RegexField(
        regex=r'^https?:\/\/github.com\/[\_\-\w]+\/[\_\-\w]+$',
        max_length=200,
        required=True,
        help_text='This is the url of the GitHub project.',
        error_messages = {'invalid' : 'Not a valid github url.'},
    )

    class Meta:
        model = mysite.customs.models.GitHubTrackerModel
        fields = ('tracker_name', 'github_url', 'bitesized_tag', 'documentation_tag')

    def clean_github_url(self):
        github_url = self.cleaned_data['github_url']

        github_name_repo = re.match(
            r'^https?:\/\/github.com\/([\_\-\w]+)\/([\_\-\w]+)$',
            github_url
        )

        # github name shouldn't need to be unique because a github user can
        # have multiple repositories.
        # Because at GitHubTrackerModel github_name is set to be unique,
        # we need to check if it's unique or not.
        # We should talk about changing the model.
        try:
            (mysite.customs.models.GitHubTrackerModel.all_trackers
             .get(
                    ~Q(id=self.instance.id) & (
                        Q(github_name__iexact=github_name_repo.group(1)) |
                        Q(github_repo__iexact=github_name_repo.group(2)))))
        except ObjectDoesNotExist:
            # If github_name or/and github_repo don't exist, it continues to save.
            self.instance.github_name = github_name_repo.group(1)
            self.instance.github_repo = github_name_repo.group(2)
        else:
            msg = 'The github name or repo is already taken.'
            self._errors['github_url'] = self.error_class([msg])

        return github_url 

    def save(self, *args, **kwargs):
        # Call out to superclass
        obj = super(GitHubTrackerForm, self).save(*args, **kwargs)

        # Create two QueryModels (one for 'open' bugs, another for 'closed'
        # bugs), since GitHub's v2 API doesn't let us list all bugs
        # regardless of status.
        open_qm, _ = mysite.customs.models.GitHubQueryModel.objects.get_or_create(
            tracker=obj, state='')
        closed_qm, _ = mysite.customs.models.GitHubQueryModel.objects.get_or_create(
            tracker=obj, state='closed')

        # Return the "upstream" return value
        return obj
