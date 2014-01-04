# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
# Copyright (C) 2012 Nathan R. Yergler
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

# This is the "base" set of views for the OpenHatch missions.

from mysite.base.decorators import view
import mysite.base.decorators
from mysite.missions.models import Step, StepCompletion
from mysite.missions.base import view_helpers

from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.conf.urls.defaults import (
    url,
    patterns,
)
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import django.views.generic.base
import django.views.generic.edit
import django.conf

import os
from django.utils import simplejson
import collections

# Other missions use this helper.
#
# By using it, you can force the web browser to show a "Save as..."
# dialog box rather than show the file inside the browser.


def make_download(content, filename, mimetype='application/octet-stream'):
    resp = HttpResponse(content)
    resp['Content-Disposition'] = 'attachment; filename=%s' % filename
    resp['Content-Type'] = mimetype
    return resp

# Generic state manager


class MissionPageState(object):

    def __init__(self, request, passed_data, mission_name):
        self.mission_name = mission_name
        self.mission_parts = None
        self.this_mission_page_short_name = ''
        self.request = request
        self.passed_data = passed_data
        self.prerequisites = []
        self.mission_step_prerequisite = None

    def get_base_data_dict_and_person(self):
        user = self.request.user
        person = None
        data = {
            'this_mission_page_short_name': self.this_mission_page_short_name,
            'mission_name': self.mission_name,
            'url_prefix': getattr(django.conf.settings, 'URL_PREFIX', 'http://127.0.0.1:8000'),
            'mission_step_prerequisites_passed': not self.mission_step_prerequisite}
        if (self.passed_data):
            data.update(self.passed_data)
        if user.is_authenticated():
            person = self.request.user.get_profile()
            if self.mission_step_prerequisite:
                data['mission_step_prerequisites_passed'
                     ] = view_helpers.mission_completed(person,
                                                        self.mission_step_prerequisite)
            else:
                data['mission_step_prerequisites_passed'] = True
        return (data, person)

    def reset(self, mission_parts=None):
        ''' Resets whole mission or selected steps.

        Args:
            mission_parts: A list of names for mission steps to reset.
        '''
        mission_parts = mission_parts and mission_parts or self.mission_parts

        if mission_parts:
            profile = self.request.user.get_profile()

            for part_name in mission_parts:
                if part_name in self.mission_parts:
                    view_helpers.unset_mission_completed(profile, part_name)


class MissionViewMixin(object):

    """Support code for Mission Views."""

    login_required = False

    mission = None
    mission_step = None
    view_name = None
    title = None

    # DEPRECATED
    mission_name = None
    this_mission_page_short_name = None

    @classmethod
    def name(cls):
        """Return the name for this View."""

        if cls.view_name:
            return cls.view_name

        # no explicit view_name defined,
        # strip the leading / from the URL and use that
        return cls.url[1:]

    @property
    def page_title(self):
        """Return the text title of this mission page."""

        return self.title or self.this_mission_page_short_name

    def get_context_data(self, *args, **kwargs):
        """Return the dict of context data for rendering this view."""

        data = super(MissionViewMixin, self).get_context_data()

        # Add some OpenHatch-specific stuff through side-effects
        # from a call to as_view().
        mysite.base.decorators.as_view(self.request,
                                       template=self.template_name,
                                       data=data,
                                       slug=None,
                                       just_modify_data=True)
        # Transitional:
        # While some missions do not have a prev_step_url,
        # we make that optional here.
        if getattr(self.mission, 'prev_step_url', None):
            data.update({
                'prev_step_url': self.mission.prev_step_url(self),
                'next_step_url': self.mission.next_step_url(self),
            })

        # Always set these template data values
        data.update({
            'mission': self.mission,
            'this_mission_page_short_name': self.page_title,
            'mission_name': self.mission_name or self.mission.name,
            'mission_page_name': self.page_title,
            'title': self.page_title,
        })

        # If a dictionary was passed in to us, either via __init__() or
        # as_view(), then incorporate that into the template data as well.
        if 'extra_context_data' in kwargs:
            data.update(kwargs['extra_context_data'])

        return data

    @classmethod
    def as_view(cls, *args, **kwargs):
        do_it = lambda: super(MissionViewMixin, cls).as_view(*args, **kwargs)
        if cls.login_required:
            return login_required(do_it())
        else:
            return do_it()


class MissionBaseView(MissionViewMixin, django.views.generic.base.TemplateView):

    """A Template-based Page in a Mission."""


class MissionBaseFormView(MissionViewMixin, django.views.generic.edit.BaseFormView):

    """A Form-based Page in a Mission."""

    def form_valid(self, form):

        view_helpers.set_mission_completed(request.user.get_profile(),
                                           self.mission_step)


class IncompleteConfiguration(ValueError):

    """Exception raised when a Mission[View] is not fully configured."""


class Mission(object):

    mission_id = None
    name = None
    VIEW_PREFIX = ''
    view_classes = None

    def __init__(self):

        if not all((
            self.mission_id,
            self.name,
            self.view_classes,
        )):
            raise IncompleteConfiguration(
                "%s is not fully configured." % (self, )
            )

    @classmethod
    def get(cls):
        """Return the single instance of this Mission class."""

        instance = getattr(cls, '__instance', None)
        if instance is None:
            cls.__instance = instance = cls()

        return instance

    @classmethod
    def as_views(cls):
        """Return a sequence of instantiated Views for Mission."""

        mission = cls.get()

        return tuple(
            view.as_view(mission=mission)
            for view in cls.view_classes
        )

    @classmethod
    def urls(cls):
        """Return the URL Configuration for this Mission."""

        mission = cls.get()

        urls = tuple(
            url('%s$' % v.url, v.as_view(mission=mission),
                name='missions-%s-%s' % (mission.mission_id, v.name(),),
                )

            for v in cls.view_classes
        )

        return patterns(cls.VIEW_PREFIX, *urls)

    def step_urls(self):

        return (
            (self.step_url(index), step.title)
            for index, step in enumerate(self.view_classes)
        )

    def step_url(self, index):
        """Return the URL of the step at index.

        If index is out of bounds, returns None.
        """

        if index < 0 or index >= len(self.view_classes):
            return None

        return reverse('missions-%s-%s' % (
            self.mission_id,
            self.view_classes[index].name(),
        ))

    def next_step_url(self, step):

        return self.step_url(self.view_classes.index(step.__class__) + 1)

    def prev_step_url(self, step):

        return self.step_url(self.view_classes.index(step.__class__) - 1)


# This is the /missions/ page.
@view
def main_page(request):
    completed_missions = collections.defaultdict(bool)
    fully_completed_missions = {}

    if request.user.is_authenticated():
        for c in StepCompletion.objects.filter(person=request.user.get_profile()):
            completed_missions[c.step.name] = True

        # FIXME: Below is a hack. It should be easier to find out if a
        # training mission is fully completed.
        if (completed_missions['tar'] and
                completed_missions['tar_extract']):
            fully_completed_missions['tar'] = True
        if (completed_missions['diffpatch_diffsingle'] and
            completed_missions['diffpatch_patchsingle'] and
            completed_missions['diffpatch_diffrecursive'] and
                completed_missions['diffpatch_patchrecursive']):
            fully_completed_missions['diffpatch'] = True
        if (completed_missions['svn_checkout'] and
            completed_missions['svn_diff'] and
                completed_missions['svn_commit']):
            fully_completed_missions['svn'] = True
        if (completed_missions['git_checkout'] and
            completed_missions['git_diff'] and
                completed_missions['git_rebase']):
            fully_completed_missions['git'] = True

    return (request, 'missions/main.html', {
            'completed_missions': completed_missions,
            'fully_completed_missions': fully_completed_missions})
