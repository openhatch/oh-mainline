# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 John Stumpo
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

from mysite.missions.base.views import *
from mysite.missions.tar import forms, controllers

### POST handlers
###
### Forms submit to this, and we use these to validate input and/or
### modify the information stored about the user, such as recording
### that a mission was successfully completed.
def upload(request):
    # Initialize data array and some default values.
    data = {}
    data['create_form'] = forms.UploadForm()
    data['create_success'] = False
    data['what_was_wrong_with_the_tarball'] = ''
    if request.method == 'POST':
        form = forms.UploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                controllers.TarMission.check_tarfile(form.cleaned_data['tarfile'].read())
                data['create_success'] = True
                StepCompletion.objects.get_or_create(person=request.user.get_profile(), step=Step.objects.get(name='tar'))
            except controllers.IncorrectTarFile, e:
                data['what_was_wrong_with_the_tarball'] = str(e)
        data['create_form'] = form
    return creating(request, data)

def file_download(request, name):
    if name in controllers.TarMission.FILES:
        response = HttpResponse(controllers.TarMission.FILES[name])
        # force it to be presented as a download
        response['Content-Disposition'] = 'attachment; filename=%s' % name
        response['Content-Type'] = 'application/octet-stream'
        return response
    else:
        raise Http404


def download_tarball_for_extract_mission(request):
    response = HttpResponse(controllers.UntarMission.synthesize_tarball())
    # force presentation as download
    response['Content-Disposition'] = 'attachment; filename=%s' % controllers.UntarMission.TARBALL_NAME
    response['Content-Type'] = 'application/octet-stream'
    return response

@login_required
def extract_mission_upload(request):
    # Initialize data array and some default values.
    data = {}
    data['unpack_form'] = forms.ExtractUploadForm()
    data['unpack_success'] = False
    data['what_was_wrong_with_the_extracted_file'] = ''
    if request.method == 'POST':
        form = forms.ExtractUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['extracted_file'].read() == controllers.UntarMission.get_contents_we_want():
                data['unpack_success'] = True
                StepCompletion.objects.get_or_create(person=request.user.get_profile(), step=Step.objects.get(name='tar_extract'))
            else:
                data['what_was_wrong_with_the_extracted_file'] = 'The uploaded file does not have the correct contents.'
        data['unpack_form'] = form
    return unpacking(request, data)

### State manager
class TarMissionPageState(MissionPageState):
    def __init__(self, request, passed_data):
        super(TarMissionPageState, self).__init__(request, passed_data, 'Tar')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        data.update({
            'filenames_for_tarball': controllers.TarMission.FILES.keys(),
            'tarball_for_unpacking_mission': controllers.UntarMission.TARBALL_NAME,
            'file_we_want': controllers.UntarMission.FILE_WE_WANT})
        if person:
            data.update( {
                'create_done': controllers.mission_completed(person, 'tar'),
                'unpack_done': controllers.mission_completed(person, 'tar_extract')
            })
        return data

### Normal GET handlers. These are usually pretty short.

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
    return (request, 'missions/tar/unpacking.html',
            state.as_dict_for_template_context())

@login_required
@view
def creating(request, passed_data={}):
    state = TarMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Creating'
    return (request, 'missions/tar/creating.html',
            state.as_dict_for_template_context())

@view
def hints(request, passed_data={}):
    state = TarMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Hints'
    return (request, 'missions/tar/hints.html',
            state.as_dict_for_template_context())

