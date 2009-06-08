# Create your views here.
from django.http import HttpResponse, QueryDict
from django.shortcuts import render_to_response
from django.core import serializers
from mysite.search.models import Bug, Project
import simplejson

def fetch_bugs(request):
    # FIXME: Give bugs some date field

    language = request.GET.get('language', '')
    format = request.GET.get('format', None)
    start = int(request.GET.get('start', 1))
    end = int(request.GET.get('end', 10))

    bugs = Bug.objects.all()

    if language:
        bugs = bugs.filter(project__language=language)

    #if status:
    #    bugs = bugs.filter(project__status=status)
        
    bugs = bugs[start-1:end]

    for b in bugs:
        b.description += "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        b.description = b.description[:65] + "..."

    if format == 'json':
        return bugs_to_json_response(bugs,
                request.GET.get('jsoncallback', 'alert'))
    else:
        prev_page_query_str = QueryDict('')
        prev_page_query_str = prev_page_query_str.copy()
        next_page_query_str = QueryDict('')
        next_page_query_str = next_page_query_str.copy()
        if language:
            prev_page_query_str['language'] = language
            next_page_query_str['language'] = language
        if format:
            prev_page_query_str['format'] = format
            next_page_query_str['format'] = format
        diff = end - start
        prev_page_query_str['start'] = start - diff - 1
        prev_page_query_str['end'] = start - 1
        next_page_query_str['start'] = end + 1
        next_page_query_str['end'] = end + diff + 1
        return render_to_response('search/search.html', {
            'bunch_of_bugs': bugs,
            'developer_name': "Orrin Hatch",
            'language': language,
            'start': start, 'end': end,
			'url': 'http://launchpad.net/',
            'prev_page_url': '/search/?' + prev_page_query_str.urlencode(),
            'next_page_url': '/search/?' + next_page_query_str.urlencode()
            })

def bugs_to_json_response(bunch_of_bugs, callback_function_name=''):
    json_serializer = serializers.get_serializer('python')()
    data = json_serializer.serialize(bunch_of_bugs)
    for elt in data:
        elt['fields']['project'] = \
                Project.objects.get(pk=int(elt['fields']['project'])).name
    jsonned = simplejson.dumps(data)
    return HttpResponse( callback_function_name + '(' + jsonned + ')' )

def index(request):
    return render_to_response('search/index.html')
    
#vim:set ts=3 sw=3 expandtab:
