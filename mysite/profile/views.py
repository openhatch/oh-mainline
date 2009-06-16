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
        # FIXME: Actually call out to e.g. Ohloh
        if username == 'paulproteus':
            new_values = {'project': 'ccHost',
                          'url': 'http://wiki.creativecommons.org/CcHost',
                          'contrib_text': 'Contributed a little bit'}
            saved.append(new_values)
            request.session['saved_data'] = saved
    return HttpResponseRedirect('/profile/')

# vim: ai ts=4 sts=4 et sw=4
