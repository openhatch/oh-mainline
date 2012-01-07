# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
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

### This is the "base" set of views for the OpenHatch missions.

from mysite.base.decorators import view
import mysite.base.decorators
from mysite.missions.models import Step, StepCompletion
from mysite.missions.base import controllers

from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import django.views.generic

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

### Generic state manager
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
            'mission_step_prerequisites_passed': not self.mission_step_prerequisite}
        if (self.passed_data):
            data.update(self.passed_data)
        if user.is_authenticated():
            person = self.request.user.get_profile()
            if self.mission_step_prerequisite:
                data['mission_step_prerequisites_passed'
                     ] = controllers.mission_completed(person,
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
                    controllers.unset_mission_completed(profile, part_name)

class MissionBaseView(django.views.generic.TemplateView):
    login_required = False

    def get_context_data(self):
        data = super(MissionBaseView, self).get_context_data()

        # Add some OpenHatch-specific stuff through side-effects
        # from a call to as_view().
        mysite.base.decorators.as_view(self.request,
                                       template=self.template_name,
                                       data=data,
                                       slug=None,
                                       just_modify_data=True)
        data.update({
                'this_mission_page_short_name': self.this_mission_page_short_name,
                'mission_name': self.mission_name})
        return data

    @classmethod
    def as_view(cls, *args, **kwargs):
        do_it = lambda: super(MissionBaseView, cls).as_view()
        if cls.login_required:
            return login_required(do_it())
        else:
            return do_it()

# This is the /missions/ page.
@view
def main_page(request):
    completed_missions = collections.defaultdict(bool)
    fully_completed_missions = {}

    if request.user.is_authenticated():
        for c in StepCompletion.objects.filter(person=request.user.get_profile()):
            completed_missions[c.step.name] = True

        ### FIXME: Below is a hack. It should be easier to find out if a
        ### training mission is fully completed.
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
