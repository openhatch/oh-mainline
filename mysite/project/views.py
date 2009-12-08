from mysite.search.models import Project
import django.template
import mysite.base.decorators

from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponsePermanentRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse

@mysite.base.decorators.view
def project(request, project__name = None):
    p = get_object_or_404(Project, name=project__name)
    return (request,
            'project/project.html',
            {
                'project': p,
                'contributors': p.get_contributors()
                },
            )

@mysite.base.decorators.view
def projects(request):
    template = "search/projects_with_bugs.html"
    projects_with_bugs = mysite.search.controllers.get_names_of_projects_with_bugs()
    data = {'projects_with_bugs': projects_with_bugs}
    return (request, template, data)


def redirect_project_to_projects(request, project__name):
    new_url = reverse(project, kwargs={'project__name': project__name})
    return HttpResponsePermanentRedirect(new_url)
