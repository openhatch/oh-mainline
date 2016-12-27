# This file is part of OpenHatch.
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

from mysite.missions.base import Mission, MissionBaseView
from mysite.missions.base.views import (
    MissionPageState,
    view,
    login_required
)

from mysite.missions.base.view_helpers import (
    mission_completed,
    set_mission_completed,
)


@login_required
def command_cd_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['command_cd_success'] = False
    data['command_cd_error_message'] = ''
    if request.method == 'POST':
        selected = request.POST.get('option')
        if selected == '3':
            data['command_cd_success'] = True
            set_mission_completed(
                request.user.get_profile(), 'command_cd')
        else:
            data['command_cd_error_message'] = 'Oops! wrong answer \n Hint: \
            see the second point'
    return command_cd(request, data)


@login_required
def command_ls_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['command_ls_success'] = False
    data['command_ls_error_message'] = ''
    if request.method == 'POST':
        selected = request.POST.get('option')
        if selected == '1':
            data['command_ls_success'] = True
            set_mission_completed(
                request.user.get_profile(), 'command_ls')
        else:
            data['command_ls_error_message'] = 'Oops! wrong answer \n Hint: \
                    type "ls --help" to view list of options'
    return command_ls(request, data)


@login_required
def command_mkdir_rm_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['command_mkdir_rm_success'] = False
    data['command_mkdir_rm_error_message'] = ''
    if request.method == 'POST':
        selected = request.POST.get('option')
        if selected == '3':
            data['command_mkdir_rm_success'] = True
            set_mission_completed(
                request.user.get_profile(), 'command_mkdir_rm')
        else:
            data['command_mkdir_rm_error_message'] = 'Oops! wrong answer \n \
            Hint: here, "music" directory is removed and "videos" directory \
            is created'
    return command_mkdir_rm(request, data)


@login_required
def command_cp_mv_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['command_cp_mv_success'] = False
    data['command_cp_mv_error_message'] = ''
    if request.method == 'POST':
        selected = request.POST.get('option')
        if selected == '4':
            data['command_cp_mv_success'] = True
            set_mission_completed(
                request.user.get_profile(), 'command_cp_mv')
        else:
            data['command_cp_mv_error_message'] = 'Oops! wrong answer \n \
            Hint: here, "test.txt" is renamed to "songs.txt" and then it is\
            copied to "music" directory'
    return command_cp_mv(request, data)


@view
def about(request, passed_data={}):
    state = ShellMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'About'
    return (request, 'missions/shell/about.html',
            state.as_dict_for_template_context())


@view
def command_cd(request, passed_data={}):
    state = ShellMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Using cd command'
    data = state.as_dict_for_template_context()
    return (request, 'missions/shell/cd.html',
            state.as_dict_for_template_context())


@view
def command_ls(request, passed_data={}):
    state = ShellMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Using ls command'
    data = state.as_dict_for_template_context()
    return (request, 'missions/shell/ls.html',
            state.as_dict_for_template_context())


@view
def command_mkdir_rm(request, passed_data={}):
    state = ShellMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Using mkdir and rm command'
    data = state.as_dict_for_template_context()
    return (request, 'missions/shell/mkdir_rm.html',
            state.as_dict_for_template_context())


@view
def command_cp_mv(request, passed_data={}):
    state = ShellMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Using cp and mv command'
    data = state.as_dict_for_template_context()
    return (request, 'missions/shell/cp_mv.html',
            state.as_dict_for_template_context())


@view
def file_and_directory(request, passed_data={}):
    state = ShellMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Differece between file and \
                                          directory'
    return (request, 'missions/shell/structure.html',
            state.as_dict_for_template_context())


@view
def more_info(request, passed_data={}):
    state = ShellMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'More Information'
    return (request, 'missions/shell/resources.html',
            state.as_dict_for_template_context())

# State Manager


class ShellMissionPageState(MissionPageState):

    def __init__(self, request, passed_data):
        super(ShellMissionPageState, self).__init__(
            request, passed_data, 'Using command line shell')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            data.update({
                'command_cd_done': mission_completed(person, 'command_cd'),
                'command_ls_done': mission_completed(person, 'command_ls'),
                'command_mkdir_rm_done': mission_completed(person,
                                        'command_mkdir_rm'),
                'command_cp_mv_done': mission_completed(person,
                                        'command_cp_mv'),
                })
        return data
