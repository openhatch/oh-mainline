# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
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

from mysite.missions.base.views import *
from mysite.missions.diffpatch import forms, controllers

### POST handlers
###
### Forms submit to this, and we use these to validate input and/or
### modify the information stored about the user, such as recording
### that a mission was successfully completed.
def patchsingle_get_original_file(request):
    return make_download(open(controllers.PatchSingleFileMission.OLD_FILE).read(),
                         filename=os.path.basename(controllers.PatchSingleFileMission.OLD_FILE))

def patchsingle_get_patch(request):
    return make_download(controllers.PatchSingleFileMission.get_patch(),
                         filename=controllers.PatchSingleFileMission.PATCH_FILENAME)

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
            if form.cleaned_data['patched_file'].read() == open(controllers.PatchSingleFileMission.NEW_FILE).read():
                controllers.set_mission_completed(request.user.get_profile(), 'diffpatch_patchsingle')
                data['patchsingle_success'] = True
            else:
                data['patchsingle_error_message'] = 'The file did not match the contents it should have.'
        data['patchsingle_form'] = form
    return single_file_patch(request, data)

def diffsingle_get_original_file(request):
    return make_download(open(controllers.DiffSingleFileMission.OLD_FILE).read(),
                         filename=os.path.basename(controllers.DiffSingleFileMission.OLD_FILE))

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
                controllers.DiffSingleFileMission.validate_patch(form.cleaned_data['diff'])
                controllers.set_mission_completed(request.user.get_profile(), 'diffpatch_diffsingle')
                data['diffsingle_success'] = True
            except controllers.IncorrectPatch, e:
                data['diffsingle_error_message'] = str(e)
        data['diffsingle_form'] = form
    return single_file_diff(request, data)

def diffrecursive_get_original_tarball(request):
    return make_download(controllers.DiffRecursiveMission.synthesize_tarball(), filename=controllers.DiffRecursiveMission.TARBALL_NAME)

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
                controllers.DiffRecursiveMission.validate_patch(form.cleaned_data['diff'].read())
                controllers.set_mission_completed(request.user.get_profile(), 'diffpatch_diffrecursive')
                data['diffrecursive_success'] = True
            except controllers.IncorrectPatch, e:
                data['diffrecursive_error_message'] = str(e)
        data['diffrecursive_form'] = form
    return recursive_diff(request, data)

def patchrecursive_get_original_tarball(request):
    return make_download(controllers.PatchRecursiveMission.synthesize_tarball(), filename=controllers.PatchRecursiveMission.BASE_NAME+'.tar.gz')

def patchrecursive_get_patch(request):
    return make_download(controllers.PatchRecursiveMission.get_patch(), filename=controllers.PatchRecursiveMission.BASE_NAME+'.patch')

@login_required
def patchrecursive_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['patchrecursive_form'] = forms.PatchRecursiveUploadForm()
    data['patchrecursive_success'] = False
    wrong_answers_present = False
    if request.method == 'POST':
        form = forms.PatchRecursiveUploadForm(request.POST)
        if form.is_valid():
            for key, value in controllers.PatchRecursiveMission.ANSWERS.iteritems():
                if form.cleaned_data[key] != value:
                    data['patchrecursive_%s_error_message' % key] = 'This answer is incorrect.'
                    wrong_answers_present = True
                else:
                    data['patchrecursive_%s_error_message' % key] = ''
            if not wrong_answers_present:
                controllers.set_mission_completed(request.user.get_profile(), 'diffpatch_patchrecursive')
                data['patchrecursive_success'] = True
        data['patchrecursive_form'] = form
    return recursive_patch(request, data)

### State manager
class DiffPatchMissionPageState(MissionPageState):
    def __init__(self, request, passed_data):
        super(DiffPatchMissionPageState, self).__init__(request, passed_data, 'Using diff and patch')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            data.update({
                'patchrecursive_done': controllers.mission_completed(person, 'diffpatch_patchrecursive'),
                'diffrecursive_done': controllers.mission_completed(person, 'diffpatch_diffrecursive'),
                'patchsingle_done': controllers.mission_completed(person, 'diffpatch_patchsingle'),
                'diffsingle_done': controllers.mission_completed(person, 'diffpatch_diffsingle')
            })
        return data

### Normal GET handlers. These are usually pretty short.

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
    return (request, 'missions/diffpatch/single_file_diff.html',
            state.as_dict_for_template_context())

@view
def single_file_patch(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Single file patch'
    return (request, 'missions/diffpatch/single_file_patch.html',
            state.as_dict_for_template_context())

@view
def recursive_patch(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Recursive patch'
    return (request, 'missions/diffpatch/recursive_patch.html',
            state.as_dict_for_template_context())

@view
def recursive_diff(request, passed_data={}):
    state = DiffPatchMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Recursive diff'
    return (request, 'missions/diffpatch/recursive_diff.html',
            state.as_dict_for_template_context())
