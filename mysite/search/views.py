from django.http import HttpResponse, QueryDict
from django.shortcuts import render_to_response
from django.core import serializers
from mysite.search.models import Bug, Project
import simplejson
from django.db.models import Q

# Via http://www.djangosnippets.org/snippets/1435/
import datetime
from dateutil import tz
import pytz
def encode_datetime(obj):
    if isinstance(obj, datetime.date):
        fixed = datetime.datetime(obj.year, obj.month, obj.day, tzinfo=pytz.utc)
        obj = fixed
    if isinstance(obj, datetime.datetime):
        return obj.astimezone(tz.tzutc()).strftime('%Y-%m-%dT%H:%M:%SZ')
    raise TypeError("%s" % type(obj) + repr(obj) + " is not JSON serializable")

def fetch_bugs(request):
    # FIXME: Give bugs some date field

    query = request.GET.get('language', '')
    query_words = query.split()
    format = request.GET.get('format', None)
    start = int(request.GET.get('start', 1))
    end = int(request.GET.get('end', 10))

    bugs = Bug.objects.all()

    for word in query_words:
        bugs = bugs.filter(Q(project__language=word) | \
                Q(title__contains=word) | Q(description__contains=word))

    bugs.order_by('last_touched')

    #if status:
    #    bugs = bugs.filter(project__status=status)
        
    bugs = bugs[start-1:end]

    for b in bugs:
        b.description += "<p>Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        """
        b.description = b.description[:65] + "..."
        """
        b.project.icon_url = "/static/images/icons/projects/%s.png" % \
                b.project.name.lower()

    if format == 'json':
        return bugs_to_json_response(bugs,
                request.GET.get('jsoncallback', 'alert'))
    else:
        prev_page_query_str = QueryDict('')
        prev_page_query_str = prev_page_query_str.copy()
        next_page_query_str = QueryDict('')
        next_page_query_str = next_page_query_str.copy()
        if query:
            prev_page_query_str['language'] = query
            next_page_query_str['language'] = query
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
            'language': query,
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
    jsonned = simplejson.dumps(data, default=encode_datetime)
    return HttpResponse( callback_function_name + '(' + jsonned + ')' )

def index(request):
    return render_to_response('search/index.html')

def request_jquery_autocompletion_suggestions(request):

    partial_query = request.GET.get('q', None)
    if (partial_query is None) or (partial_query == ''):
        return HttpResponseServerError("Need partial_query in GET")

    # jQuery autocomplete also gives us this variable:
    # timestamp = request.GET.get('timestamp', None)

    suggestions = get_autocompletion_suggestions(partial_query)
    #return list_to_jquery_autocompletion_format(suggestions)
    return suggestions

def list_to_jquery_autocompletion_format(list):
    """Converts a list to the format required by
    jQuery's autocomplete plugin."""
    return "\n".join(list)

def get_autocompletion_suggestions(partial_query):
    """
    This method returns a list of suggested queries.
    It checks the query substring against a number of
    fields in the database:
      - project.name
      - project.language

    Not yet implemented:
      - libraries (frameworks? toolkits?) like Django
    """

    fields = {
            'project': {'prefix': 'project'},
            'language': {'prefix': 'lang'},
            'dependency': {'prefix': 'dep'},
            'library': {'prefix': 'lib'},
            }
    separator = ":"

    for field in fields: fields[field]['is_queried'] = True

    if partial_query.find(':') > 0:
        prefix = partial_query.split(":")[0]
        for field in fields:
            if fields[field]['prefix'] == prefix:
                fields[field]['is_queried'] = True
        partial_query = partial_query.split(":")[1]
    else:
        for field in fields: fields[field]['is_queried'] = True

    project_max = 5
    lang_max = 5

    suggestions = ''

    if fields['project']['is_queried']:

        # Compile list of projects
        projects_by_name = Project.objects.filter(name__istartswith=partial_query)
        project_names = projects_by_name.values_list('name', flat=True)

        # Limit
        project_names = project_names[:project_max]
        # FIXME: Is __istartswith faster?

        # Add prefix and convert to string.
        if (project_names):
            project_str = "%s" + "\n%s".join(project_names)
            suggestions += project_str % (fields['project']['prefix'] + separator)

    if fields['language']['is_queried']:

        # For languages, get projects first
        projects_by_lang = Project.objects.filter(language__istartswith=partial_query)

        # Then use bugs to compile a list of languages.
        langs = projects_by_lang.values_list('language', flat=True).order_by('language')[:lang_max]

        if (langs):

            # Add prefix and convert to string.
            suggestions += ("\n%s" + "\n%s".join(langs)) % (fields['language']['prefix'] + separator)

    return HttpResponse(suggestions)

"""
Ways we could do autocompletion:

Method 1.
Cache languages, search those first.
Ask server to give a list of projects beginning with "c"
Server returns list, cache that.

Method 2.
Ask server to give a list of projects and languages beginning with "c"

Add top 100 fulltext words to the mix.
"""
    
# vim: set ai ts=4 sw=4 et columns=80:
