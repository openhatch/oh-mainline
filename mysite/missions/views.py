from mysite.base.decorators import view
from mysite.missions import forms, controllers
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
                controllers.TarMission.check_tarfile(form.cleaned_data['tarfile'].read())
                data['create_success'] = True
                StepCompletion.objects.get_or_create(person=request.user.get_profile(), step=Step.objects.get(name='tar'))
            except controllers.IncorrectTarFile, e:
                data['what_was_wrong_with_the_tarball'] = str(e)
        data['create_form'] = form
    return tar_mission(request, data)

def tar_mission_data(request, passed_data={}):
    data = {
      'create_success': False,
      'what_was_wrong_with_the_tarball': '',
      'filenames_for_tarball': controllers.TarMission.FILES.keys(),
      'create_form': forms.TarUploadForm(),
      'unpack_form': forms.TarExtractUploadForm(),
      'unpack_success': False,
      'tarball_for_unpacking_mission': controllers.UntarMission.TARBALL_NAME,
      'file_we_want': controllers.UntarMission.FILE_WE_WANT,
      'create_done': controllers.mission_completed(request.user.get_profile(), 'tar'),
      'unpack_done': controllers.mission_completed(request.user.get_profile(), 'tar_extract')
    }
    data.update(passed_data)
    return data

@login_required
@view
def tar_mission(request, passed_data={}):
    data = tar_mission_data(request, passed_data)
    return (request, 'missions/tar_upload.html', data)

def tar_file_download(request, name):
    if name in controllers.TarMission.FILES:
        response = HttpResponse(controllers.TarMission.FILES[name])
        # force it to be presented as a download
        response['Content-Disposition'] = 'attachment; filename=%s' % name
        response['Content-Type'] = 'application/octet-stream'
        return response
    else:
        raise Http404


def tar_download_tarball_for_extract_mission(request):
    response = HttpResponse(controllers.UntarMission.synthesize_tarball())
    # force presentation as download
    response['Content-Disposition'] = 'attachment; filename=%s' % controllers.UntarMission.TARBALL_NAME
    response['Content-Type'] = 'application/octet-stream'
    return response

@login_required
def tar_extract_mission_upload(request):
    data = {}
    if request.method == 'POST':
        form = forms.TarExtractUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['extracted_file'].read() == controllers.UntarMission.get_contents_we_want():
                data['unpack_success'] = True
                StepCompletion.objects.get_or_create(person=request.user.get_profile(), step=Step.objects.get(name='tar_extract'))
            else:
                data['what_was_wrong_with_the_extracted_file'] = 'The uploaded file does not have the correct contents.'
        data['unpack_form'] = form
    return tar_mission(request, data)

def diffpatch_patchsingle_get_original_file(request):
    return make_download(open(controllers.PatchSingleFileMission.OLD_FILE).read(),
                         filename=os.path.basename(controllers.PatchSingleFileMission.OLD_FILE))

def diffpatch_patchsingle_get_patch(request):
    return make_download(controllers.PatchSingleFileMission.get_patch(),
                         filename=controllers.PatchSingleFileMission.PATCH_FILENAME)

@login_required
@view
def diffpatch_mission(request, passed_data={}):
    data = {
      'patchsingle_success': False,
      'patchsingle_form': forms.PatchSingleUploadForm(),
      'patchsingle_error_message': '',
      'patchsingle_done': controllers.mission_completed(request.user.get_profile(), 'diffpatch_patchsingle'),
      'diffsingle_success': False,
      'diffsingle_form': forms.DiffSingleUploadForm(),
      'diffsingle_error_message': '',
      'diffsingle_done': controllers.mission_completed(request.user.get_profile(), 'diffpatch_diffsingle'),
      'diffrecursive_success': False,
      'diffrecursive_form': forms.DiffRecursiveUploadForm(),
      'diffrecursive_error_message': '',
      'diffrecursive_done': controllers.mission_completed(request.user.get_profile(), 'diffpatch_diffrecursive'),
      'patchrecursive_success': False,
      'patchrecursive_form': forms.PatchRecursiveUploadForm(),
      'patchrecursive_children_hats_error_message': '',
      'patchrecursive_lizards_hats_error_message': '',
      'patchrecursive_done': controllers.mission_completed(request.user.get_profile(), 'diffpatch_patchrecursive'),
    }
    data.update(passed_data)
    return (request, 'missions/diff_patch.html', data)

@login_required
def diffpatch_patchsingle_submit(request):
    data = {}
    if request.method == 'POST':
        form = forms.PatchSingleUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['patched_file'].read() == open(controllers.PatchSingleFileMission.NEW_FILE).read():
                controllers.set_mission_completed(request.user.get_profile(), 'diffpatch_patchsingle')
                data['patchsingle_success'] = True
            else:
                data['patchsingle_error_message'] = 'The file did not match the contents it should have.'
        data['patchsingle_form'] = form
    return diffpatch_mission(request, data)

def diffpatch_diffsingle_get_original_file(request):
    return make_download(open(controllers.DiffSingleFileMission.OLD_FILE).read(),
                         filename=os.path.basename(controllers.DiffSingleFileMission.OLD_FILE))

@login_required
def diffpatch_diffsingle_submit(request):
    data = {}
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
    return diffpatch_mission(request, data)

def diffpatch_diffrecursive_get_original_tarball(request):
    return make_download(controllers.DiffRecursiveMission.synthesize_tarball(), filename=controllers.DiffRecursiveMission.TARBALL_NAME)

@login_required
def diffpatch_diffrecursive_submit(request):
    data = {}
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
    return diffpatch_mission(request, data)

def diffpatch_patchrecursive_get_original_tarball(request):
    return make_download(controllers.PatchRecursiveMission.synthesize_tarball(), filename=controllers.PatchRecursiveMission.BASE_NAME+'.tar.gz')

def diffpatch_patchrecursive_get_patch(request):
    return make_download(controllers.PatchRecursiveMission.get_patch(), filename=controllers.PatchRecursiveMission.BASE_NAME+'.patch')

@login_required
def diffpatch_patchrecursive_submit(request):
    data = {}
    wrong_answers_present = False
    if request.method == 'POST':
        form = forms.PatchRecursiveUploadForm(request.POST)
        if form.is_valid():
            for key, value in controllers.PatchRecursiveMission.ANSWERS.iteritems():
                if form.cleaned_data[key] != value:
                    data['patchrecursive_%s_error_message' % key] = 'This answer is incorrect.'
                    wrong_answers_present = True
            if not wrong_answers_present:
                controllers.set_mission_completed(request.user.get_profile(), 'diffpatch_patchrecursive')
                data['patchrecursive_success'] = True
        data['patchrecursive_form'] = form
    return diffpatch_mission(request, data)
