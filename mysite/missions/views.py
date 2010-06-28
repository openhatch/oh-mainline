from mysite.base.decorators import view
from mysite.missions.controllers import TarMission, IncorrectTarFile, UntarMission, mission_completed, PatchSingleFileMission
from mysite.missions import forms
from mysite.missions.models import Step, StepCompletion

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import os

def make_download(content, filename, mimetype='application/octet-stream'):
    resp = HttpResponse(content)
    resp['Content-Disposition'] = 'attachment; filename=%s' % filename
    resp['Content-Type'] = mimetype
    return resp

@login_required
@view
def main_page(request):
    completed_missions = dict((c.step.name, True) for c in StepCompletion.objects.filter(person=request.user.get_profile()))
    return (request, 'missions/main.html', {'completed_missions': completed_missions})

@login_required
def tar_upload(request):
    data = {}
    if request.method == 'POST':
        form = forms.TarUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                TarMission.check_tarfile(form.cleaned_data['tarfile'].read())
                data['create_success'] = True
                StepCompletion.objects.get_or_create(person=request.user.get_profile(), step=Step.objects.get(name='tar'))
            except IncorrectTarFile, e:
                data['what_was_wrong_with_the_tarball'] = str(e)
        data['create_form'] = form
    return tar_mission(request, data)

@login_required
@view
def tar_mission(request, passed_data={}):
    data = {
      'create_success': False,
      'what_was_wrong_with_the_tarball': '',
      'filenames_for_tarball': TarMission.FILES.keys(),
      'create_form': forms.TarUploadForm(),
      'unpack_form': forms.TarExtractUploadForm(),
      'unpack_success': False,
      'tarball_for_unpacking_mission': UntarMission.TARBALL_NAME,
      'file_we_want': UntarMission.FILE_WE_WANT,
      'create_done': mission_completed(request.user.get_profile(), 'tar'),
      'unpack_done': mission_completed(request.user.get_profile(), 'tar_extract')
    }
    data.update(passed_data)
    return (request, 'missions/tar_upload.html', data)

def tar_file_download(request, name):
    if name in TarMission.FILES:
        response = HttpResponse(TarMission.FILES[name])
        # force it to be presented as a download
        response['Content-Disposition'] = 'attachment; filename=%s' % name
        response['Content-Type'] = 'application/octet-stream'
        return response
    else:
        raise Http404


def tar_download_tarball_for_extract_mission(request):
    response = HttpResponse(UntarMission.synthesize_tarball())
    # force presentation as download
    response['Content-Disposition'] = 'attachment; filename=%s' % UntarMission.TARBALL_NAME
    response['Content-Type'] = 'application/octet-stream'
    return response

@login_required
def tar_extract_mission_upload(request):
    data = {}
    if request.method == 'POST':
        form = forms.TarExtractUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['extracted_file'].read() == UntarMission.get_contents_we_want():
                data['unpack_success'] = True
                StepCompletion.objects.get_or_create(person=request.user.get_profile(), step=Step.objects.get(name='tar_extract'))
            else:
                data['what_was_wrong_with_the_extracted_file'] = 'The uploaded file does not have the correct contents.'
        data['unpack_form'] = form
    return tar_mission(request, data)

def diffpatch_patchsingle_get_original_file(request):
    return make_download(open(PatchSingleFileMission.OLD_FILE).read(), filename=os.path.basename(PatchSingleFileMission.OLD_FILE))

def diffpatch_patchsingle_get_patch(request):
    return make_download(PatchSingleFileMission.get_patch(), filename=PatchSingleFileMission.PATCH_FILENAME)
