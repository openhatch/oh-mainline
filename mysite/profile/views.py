from django.http import HttpResponse
from django.shortcuts import render_to_response

def index(request):
    project = request.GET.get('project', '')
    contrib_text = request.GET.get('contrib_text', '')
    url = request.GET.get('url', '')

    if project and contrib_text and url:
        display_data = dict(project=project,
                            url=url,
                            contrib_text=contrib_text)
    else:
        display_data = {}
    
    return render_to_response('profile/index.html',
                              display_data)
