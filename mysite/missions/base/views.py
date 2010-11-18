### This is the "base" set of views for the OpenHatch missions.

from mysite.base.decorators import view
from mysite.missions.models import Step, StepCompletion

from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import os
import simplejson

# Other missions use this helper.
#
# By using it, you can force the web browser to show a "Save as..."
# dialog box rather than show the file inside the browser.
def make_download(content, filename, mimetype='application/octet-stream'):
    resp = HttpResponse(content)
    resp['Content-Disposition'] = 'attachment; filename=%s' % filename
    resp['Content-Type'] = mimetype
    return resp

# This is the /missions/ page.
@view
def main_page(request):
    completed_missions = {}
    if request.user.is_authenticated():
        completed_missions = dict((c.step.name, True) for c in StepCompletion.objects.filter(person=request.user.get_profile()))
    return (request, 'missions/main.html', {'completed_missions': completed_missions})
