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

import os.path
from mysite.missions.base.views import (
    make_download,
    login_required,
    MissionPageState,
    HttpResponseRedirect,
    reverse,
    view,
)
from mysite.missions.base.view_helpers import (
    mission_completed,
    set_mission_completed,
)
from mysite.base.unicode_sanity import utf8
from mysite.missions.diffpatch import forms, view_helpers

# POST handlers
#
# Forms submit to this, and we use these to validate input and/or
# modify the information stored about the user, such as recording
# that a mission was successfully completed.


def patchsingle_get_original_file(request):
    return make_download(
        open(view_helpers.PatchSingleFileMission.OLD_FILE).read(),
        filename=os.path.basename(view_helpers.PatchSingleFileMission.OLD_FILE))


def patchsingle_get_patch(request):
    return make_download(view_helpers.PatchSingleFileMission.get_patch(),
                         filename=view_helpers.PatchSingleFileMission.PATCH_FILENAME)


@login_required
def patchsingle_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['patchsingle_form'] = forms.PatchSingleUploadForm()
    data['patchsingle_success'] = False
    data['patchsingle_error_message'] = ''
    if request.method == 'POST':
        form = forms.PatchSingleUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['patched_file'].read() == open(view_helpers.PatchSingleFileMission.NEW_FILE).read():
                set_mission_completed(
                    request.user.get_profile(), 'diffpatch_patchsingle')
                data['patchsingle_success'] = True
            else:
                data[
                    'patchsingle_error_message'] = 'The file did not match the contents it should have.'
        data['patchsingle_form'] = form
    return single_file_patch(request, data)


def diffsingle_get_original_file(request):
    return make_download(
        open(view_helpers.DiffSingleFileMission.OLD_FILE).read(),
        filename=os.path.basename(view_helpers.DiffSingleFileMission.OLD_FILE))


@login_required
def diffsingle_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['diffsingle_form'] = forms.DiffSingleUploadForm()
    data['diffsingle_success'] = False
    data['diffsingle_error_message'] = ''
    if request.method == 'POST':
        form = forms.DiffSingleUploadForm(request.POST)
        if form.is_valid():
            try:
                view_helpers.DiffSingleFileMission.validate_patch(
                    form.cleaned_data['diff'])
                set_mission_completed(
                    request.user.get_profile(), 'diffpatch_diffsingle')
                data['diffsingle_success'] = True
            except view_helpers.IncorrectPatch, e:
                data['diffsingle_error_message'] = utf8(e)
        data['diffsingle_form'] = form
    return single_file_diff(request, data)


def diffrecursive_get_original_tarball(request):
    return make_download(view_helpers.DiffRecursiveMission.synthesize_tarball(), filename=view_helpers.DiffRecursiveMission.TARBALL_NAME)


@login_required
def diffrecursive_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['diffrecursive_form'] = forms.DiffRecursiveUploadForm()
    data['diffrecursive_success'] = False
    data['diffrecursive_error_message'] = ''
    if request.method == 'POST':
        form = forms.DiffRecursiveUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                view_helpers.DiffRecursiveMission.validate_patch(
                    form.cleaned_data['diff'].read())
                set_mission_completed(
                    request.user.get_profile(), 'diffpatch_diffrecursive')
                data['diffrecursive_success'] = True
            except view_helpers.IncorrectPatch, e:
                data['diffrecursive_error_message'] = utf8(e)
        else:
            errors = list(form['diff'].errors)
            if errors:
                data['diffrecursive_error_message'] = (
                    data.get('diffrecursive_error_message', '') +
                    utf8(' '.join(errors)))
        data['diffrecursive_form'] = form
    return recursive_diff(request, data)


def patchrecursive_get_patch(request):
    return make_download(view_helpers.PatchRecursiveMission.get_patch(), filename=view_helpers.PatchRecursiveMission.BASE_NAME + '.patch')


@login_required
def patchrecursive_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['patchrecursive_form'] = forms.PatchRecursiveUploadForm()
    data['patchrecursive_success'] = False
    if request.method == 'POST':
        form = forms.PatchRecursiveUploadForm(request.POST)
        if form.is_valid():
            set_mission_completed(
                request.user.get_profile(), 'diffpatch_patchrecursive')
            return HttpResponseRedirect(reverse(recursive_patch))
        data['patchrecursive_form'] = form
    return recursive_patch(request, data)

# State manager


class DiffPatchMissionPageState(MissionPageState):

    def __init__(self, request, passed_data):
        super(DiffPatchMissionPageState, self).__init__(
            request, passed_data, 'Using diff and patch')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            data.update({
                'patchrecursive_done': mission_completed(person, 'diffpatch_patchrecursive'),
                'diffrecursive_done': mission_completed(person, 'diffpatch_diffrecursive'),
                'patchsingle_done': mission_completed(person, 'diffpatch_patchsingle'),
                'diffsingle_done': mission_completed(person, 'diffpatch_diffsingle')
            })
        return data

# Normal GET handlers. These are usually pretty short.


@view
def about(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'About'
    return (request, 'missions/diffpatch/about.html',
            state.as_dict_for_template_context())


@view
def single_file_diff(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Single file diff'
    data = state.as_dict_for_template_context()
    data['diffsingle_form'] = forms.DiffSingleUploadForm()
    return (request, 'missions/diffpatch/single_file_diff.html', data)


@view
def single_file_patch(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Single file patch'
    data = state.as_dict_for_template_context()
    data['patchsingle_form'] = forms.PatchSingleUploadForm()
    return (request, 'missions/diffpatch/single_file_patch.html', data)


@view
def recursive_patch(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Recursive patch'
    data = state.as_dict_for_template_context()
    data['patchrecursive_form'] = forms.PatchRecursiveUploadForm()
    data.update(passed_data)
    return (request, 'missions/diffpatch/recursive_patch.html', data)


@view
def recursive_diff(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Recursive diff'
    data = state.as_dict_for_template_context()
    data['diffrecursive_form'] = forms.DiffRecursiveUploadForm()
    return (request, 'missions/diffpatch/recursive_diff.html', data)
