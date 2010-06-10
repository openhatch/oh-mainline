from mysite.base.decorators import view
from mysite.missions.controllers import TarMission, TarUploadForm, IncorrectTarFile
from mysite.missions.models import Step, StepCompletion

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

@login_required
@view
def main_page(request):
    completed_missions = dict((c.step.name, True) for c in StepCompletion.objects.filter(person=request.user.get_profile()))
    return (request, 'missions/main.html', {'completed_missions': completed_missions})

@login_required
@view
def tar_upload(request):
    data = {'success': False, 'what_was_wrong_with_the_tarball': ''}
    if request.method == 'POST':
        form = TarUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                TarMission.check_tarfile(form.cleaned_data['tarfile'].read())
                data['success'] = True
                StepCompletion(person=request.user.get_profile(), step=Step.objects.get(name='tar')).save()
            except IncorrectTarFile, e:
                data['what_was_wrong_with_the_tarball'] = str(e)
        data['form'] = form
    else:
        data['form'] = TarUploadForm()
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
