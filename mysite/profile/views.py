from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

def index(request):
    return render_to_response('profile/index.html',
                              {'saved_data':
                               request.session.get('saved_data',
                                                   [])})

def add_contribution(request):
    project = request.POST.get('project', '')
    contrib_text = request.POST.get('contrib_text', '')
    url = request.POST.get('url', '')

    if project and contrib_text and url:
        saved = request.session.get('saved_data', [])
        # always append the data
        saved.append(
            dict(project=project,
                 url=url,
                 contrib_text=contrib_text))
        request.session['saved_data'] = saved
    return HttpResponseRedirect('/profile/')

def get_data_for_username(request):
    username = request.POST.get('username', '')

    if username:
        saved = request.session.get('saved_data', [])
        # always append the data
        import ohloh
        oh = ohloh.get_ohloh()
        projects = oh.get_contribution_info_by_username('paulproteus')
        for project in projects:
            new_values = {'project': project['project'],
                          'url': project['project_homepage_url'],
                          'contrib_text': str(project['man_months']) + ' measured month(s) of primarily ' + project['primary_language'] + ' activity'}
            saved.append(new_values)
            request.session['saved_data'] = saved
    return HttpResponseRedirect('/profile/')

# vim: ai ts=4 sts=4 et sw=4
