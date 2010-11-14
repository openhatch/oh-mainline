from mysite.base.decorators import view
from mysite.missions.models import Step, StepCompletion

from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import os
import simplejson

def make_download(content, filename, mimetype='application/octet-stream'):
    resp = HttpResponse(content)
    resp['Content-Disposition'] = 'attachment; filename=%s' % filename
    resp['Content-Type'] = mimetype
    return resp

@view
def main_page(request):
    completed_missions = {}
    if request.user.is_authenticated():
        completed_missions = dict((c.step.name, True) for c in StepCompletion.objects.filter(person=request.user.get_profile()))
    return (request, 'missions/main.html', {'completed_missions': completed_missions})
