# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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

### This is the "base" set of views for the OpenHatch missions.

from mysite.base.decorators import view
from mysite.missions.models import Step, StepCompletion
from mysite.missions.base import controllers

from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import os
import simplejson

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
            'mission_name': self.mission_name}
        if (self.passed_data):
            data.update(self.passed_data)
        if user.is_authenticated():
            person = self.request.user.get_profile()
            if self.mission_step_prerequisite:
                data['mission_step_prerequisites_passed'
                     ] = controllers.mission_completed(person,
                                                       self.mission_step_prerequisite)
        return (data, person)

# This is the /missions/ page.
@view
def main_page(request):
    completed_missions = {}
    if request.user.is_authenticated():
        completed_missions = dict((c.step.name, True) for c in StepCompletion.objects.filter(person=request.user.get_profile()))
    return (request, 'missions/main.html', {'completed_missions': completed_missions})
