from mysite.search.models import Project

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404

def project(request, project__name = None):
    p = Project.objects.get(name=project__name)
    return render_to_response('project/project.html',
            {
                'project': p,
                'contributors': p.get_contributors()
                }
            )
