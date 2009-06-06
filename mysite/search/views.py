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
    start = int(request.GET.get('start', 0))
    end = int(request.GET.get('end', 10))

    bugs = Bug.objects.all()

    if language:
        bugs = bugs.filter(project__language=language)

    #if status:
    #    bugs = bugs.filter(project__status=status)
        
    bugs = bugs[start:end]

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
        prev_page_query_str['start'] = start - diff
        prev_page_query_str['end'] = start
        next_page_query_str['start'] = end
        next_page_query_str['end'] = end + diff
        return render_to_response('search/search.html', {
            'bunch_of_bugs': bugs,
            'language': language,
            'start': start, 'end': end,
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
    
#:vim set ts=4 sw=4 expandtab:
