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

from mysite.missions.base.views import (
    MissionPageState,
    view,
    login_required
)

from mysite.missions.base.view_helpers import (
    mission_completed,
    set_mission_completed,
)

from mysite.missions.pipvirtualenv import forms, view_helpers
from mysite.base.unicode_sanity import utf8

# POST handlers
#
# Forms submit to this, and we use these to validate input and/or
# modify the information stored about the user, such as recording
# that a mission was successfully completed.

@login_required
def pip_freeze_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['pipfreeze_form'] = forms.PipFreezeOutputForm()
    data['pipfreeze_success'] = False
    data['pipfreeze_error_message'] = ''
    if request.method == 'POST':
        form = forms.PipFreezeOutputForm(request.POST)
        if form.is_valid():
            try:
                view_helpers.validate_pip_freeze_output(
                    form.cleaned_data['pipfreeze_output'])
                set_mission_completed(
                    request.user.get_profile(), 'pipvirtualenv_pipfreeze')
                data['pipfreeze_success'] = True
            except view_helpers.IncorrectPipOutput, e:
                data['pipfreeze_error_message'] = utf8(e)
        data['pipfreeze_form'] = form
    return installing_packages(request, data)


@login_required
def pip_list_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['piplist_form'] = forms.PipListOutputForm()
    data['piplist_success'] = False
    data['piplist_error_message'] = ''
    if request.method == 'POST':
        form = forms.PipListOutputForm(request.POST)
        if form.is_valid():
            try:
                view_helpers.validate_pip_list_output(
                    form.cleaned_data['piplist_output'])
                set_mission_completed(
                    request.user.get_profile(), 'pipvirtualenv_piplist')
                data['piplist_success'] = True
            except view_helpers.IncorrectPipOutput, e:
                data['piplist_error_message'] = utf8(e)
        data['piplist_form'] = form
    return removing_packages(request, data)


# State manager


class PipVirtualenvMissionPageState(MissionPageState):

    def __init__(self, request, passed_data):
        super(PipVirtualenvMissionPageState, self).__init__(
            request, passed_data, 'Using pip and virtualenv')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            data.update({
                'pipfreeze_done': mission_completed(person, 'pipvirtualenv_pipfreeze'),
                'piplist_done': mission_completed(person, 'pipvirtualenv_piplist'),
            })

        return data

# Normal GET handlers. These are usually pretty short.


@view
def about(request, passed_data={}):
    state = PipVirtualenvMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'About'
    return (request, 'missions/pipvirtualenv/about.html',
            state.as_dict_for_template_context())


@view
def setup_pipvirtualenv(request, passed_data={}):
    state = PipVirtualenvMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Setup pip and virtualenv'
    return (request, 'missions/pipvirtualenv/setup.html',
            state.as_dict_for_template_context())


@view
def installing_packages(request, passed_data={}):
    state = PipVirtualenvMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Installing packages and creating virtualenvs'
    data = state.as_dict_for_template_context()
    data['pipfreeze_form'] = forms.PipFreezeOutputForm()
    return (request, 'missions/pipvirtualenv/installing_packages.html', data)


@view
def removing_packages(request, passed_data={}):
    state = PipVirtualenvMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Removing packages and deactivating virtualenvs'
    data = state.as_dict_for_template_context()
    data['piplist_form'] = forms.PipListOutputForm()
    return (request, 'missions/pipvirtualenv/removing_packages.html', data)


@view
def learning_more(request, passed_data={}):
    state = PipVirtualenvMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'More about pip and virtualenv'
    return (request, 'missions/pipvirtualenv/learning_more.html',
            state.as_dict_for_template_context())

@view
def reference(request, passed_data={}):
    state = PipVirtualenvMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Quick Reference'
    return (request, 'missions/pipvirtualenv/quick_reference.html',
            state.as_dict_for_template_context())

