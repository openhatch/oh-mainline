from django.http import HttpResponse
from django.shortcuts import render_to_response

def index(request):
    project = request.GET.get('project', '')
    contrib_text = request.GET.get('contrib_text', '')
    url = request.GET.get('url', '')

    if project and contrib_text and url:
        if 'saved_data' not in request.session:
            request.session['saved_data'] = []
        # always append the data
        request.session['saved_data'].append(
            dict(project=project,
                 url=url,
                 contrib_text=contrib_text))
    
    return render_to_response('profile/index.html',
                              {'saved_data':
                               request.session.get('saved_data',
                                                   [])})
