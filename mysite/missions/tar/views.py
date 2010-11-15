from mysite.missions.base.views import *
from mysite.missions.tar import forms, controllers

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
    return tar_mission_creating(request, data)

def tar_mission_data(request, passed_data={}):
    data = {
      'mission_name': 'Tar',
      'create_success': False,
      'what_was_wrong_with_the_tarball': '',
      'filenames_for_tarball': controllers.TarMission.FILES.keys(),
      'create_form': forms.TarUploadForm(),
      'unpack_form': forms.TarExtractUploadForm(),
      'unpack_success': False,
      'tarball_for_unpacking_mission': controllers.UntarMission.TARBALL_NAME,
      'file_we_want': controllers.UntarMission.FILE_WE_WANT}
    if request.user.is_authenticated():
        data.update( {
            'create_done': controllers.mission_completed(request.user.get_profile(), 'tar'),
            'unpack_done': controllers.mission_completed(request.user.get_profile(), 'tar_extract')
        })
    data.update(passed_data)
    return data

@view
def tar_mission_about(request, passed_data={}):
    data = tar_mission_data(request, passed_data)
    data['this_mission_page_short_name'] = 'About'
    return (request, 'missions/tar/tar_about.html', data)

@login_required
@view
def tar_mission_unpacking(request, passed_data={}):
    data = tar_mission_data(request, passed_data)
    data['this_mission_page_short_name'] = 'Unpacking'
    return (request, 'missions/tar/tar_unpacking.html', data)

@login_required
@view
def tar_mission_creating(request, passed_data={}):
    data = tar_mission_data(request, passed_data)
    data['this_mission_page_short_name'] = 'Creating'
    return (request, 'missions/tar/tar_creating.html', data)

@view
def tar_mission_hints(request, passed_data={}):
    data = tar_mission_data(request, passed_data)
    data['this_mission_page_short_name'] = 'Hints'
    return (request, 'missions/tar/tar_hints.html', data)

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
    return tar_mission_unpacking(request, data)

