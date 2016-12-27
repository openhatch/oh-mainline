# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
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

from django.http import HttpResponse

from mysite.missions.base.views import *
from mysite.missions.tar import view_helpers


# POST handlers
#
# Forms submit to this, and we use these to validate input and/or
# modify the information stored about the user, such as recording
# that a mission was successfully completed.
def reset(request):
    ''' Resets the state of the Tar mission '''
    if request.method == 'POST' and request.POST['mission_parts']:
        mission_parts = request.POST['mission_parts'].split(',')

        state = TarMissionPageState(request, None)
        state.reset(mission_parts)
        message = 'Operation successful'
    else:
        message = 'An error occured'

    return HttpResponse(message)


def file_download(request, name):
    if name in view_helpers.TarMission.FILES:
        response = HttpResponse(view_helpers.TarMission.FILES[name])
        # force it to be presented as a download
        response['Content-Disposition'] = 'attachment; filename=%s' % name
        response['Content-Type'] = 'application/octet-stream'
        return response
    else:
        raise Http404


def download_tarball_for_extract_mission(request):
    response = HttpResponse(view_helpers.UntarMission.synthesize_tarball())
    # force presentation as download
    response[
        'Content-Disposition'] = 'attachment; filename=%s' % view_helpers.UntarMission.TARBALL_NAME
    response['Content-Type'] = 'application/octet-stream'
    return response


@login_required
def extract_mission_success(request):
    if request.method == 'POST' and request.POST['unpack_success']:
        view_helpers.set_mission_completed(
            request.user.get_profile(), 'tar_extract')
        message = 'Step successfully completed'
    else:
        message = 'An error occured'
    return HttpResponse(message)


@login_required
def create_mission_success(request):
    if request.method == 'POST' and request.POST['create_success']:
        view_helpers.set_mission_completed(
            request.user.get_profile(), 'tar')
        message = 'Step successfully completed'
    else:
        message = 'An error occured'
    return HttpResponse(message)

# State manager


class TarMissionPageState(MissionPageState):

    def __init__(self, request, passed_data):
        super(TarMissionPageState, self).__init__(request, passed_data, 'Tar')
        self.mission_parts = ['tar', 'tar_extract', ]

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            data.update({
                'create_done': view_helpers.mission_completed(person, 'tar'),
                'unpack_done': view_helpers.mission_completed(person, 'tar_extract')
            })
        return data

# Normal GET handlers. These are usually pretty short.


@view
def about(request, passed_data={}):
    state = TarMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'About'
    return (request, 'missions/tar/about.html',
            state.as_dict_for_template_context())


@login_required
@view
def unpacking(request, passed_data={}):
    state = TarMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Unpacking'
    data = state.as_dict_for_template_context()
    return (request, 'missions/tar/unpacking.html', data)


@login_required
@view
def creating(request, passed_data={}):
    state = TarMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Creating'
    data = state.as_dict_for_template_context()
    return (request, 'missions/tar/creating.html', data)


@view
def hints(request, passed_data={}):
    state = TarMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Quick reference'
    return (request, 'missions/tar/hints.html',
            state.as_dict_for_template_context())
