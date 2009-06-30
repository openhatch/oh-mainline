from django.http import HttpResponse, QueryDict, HttpResponseServerError
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
        # b.description = b.description[:65] + "..."
        b.project.icon_url = "/static/images/icons/projects/%s.png" % \
                b.project.name.lower()
        # FIXME: Randomize for camera
        b.good_for_newcomers = True

    if format == 'json':
        return bugs_to_json_response(bugs, request.GET.get(
            'jsoncallback', 'alert'))
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
    """
    Wraps get_autocompletion_suggestions and
    list_to_jquery_autocompletion_format in a
    HttpRequest -> HttpResponse loop.
    Validates GET parameters. Expected:
        ?q=[suggestion fodder]
    If q is absent or empty, this function
    returns an HttpResponseServerError.
    """
    partial_query = request.GET.get('q', None)
    if (partial_query is None) or (partial_query == ''):
        return HttpResponseServerError("Need partial_query in GET")

    # jQuery autocomplete also gives us this variable:
    # timestamp = request.GET.get('timestamp', None)

    suggestions_list = get_autocompletion_suggestions(partial_query)
    suggestions_string = list_to_jquery_autocompletion_format(
                suggestions_list)
    return HttpResponse(suggestions_string)

def list_to_jquery_autocompletion_format(list):
    """Converts a list to the format required by
    jQuery's autocomplete plugin."""
    return "\n".join(list)

class SearchableField:
    "A field in the database you can search."
    fields_by_prefix = {}
    def __init__(self, _prefix):
        self.prefix = _prefix
        self.is_queried = False
        self.fields_by_prefix[self.prefix] = self

def get_autocompletion_suggestions(input):
    """
    This method returns a list of suggested queries.
    It checks the query substring against a number of
    fields in the database:
      - project.name
      - project.language

    Not yet implemented:
      - libraries (frameworks? toolkits?) like Django
      - search by date
    """

    sf_project = SearchableField('project')
    sf_language = SearchableField('lang')
    sf_dependency = SearchableField('dep')
    sf_library = SearchableField('lib')
    sf_date_before = SearchableField('before')
    sf_date_after = SearchableField('after')

    separator = ":"
    prefix = ''
    partial_query = ''

    if separator in input[1:-1]:
        prefix = input.split(separator)[0]
        partial_query = input.split(separator)[1]
        sf = SearchableField.fields_by_prefix.get(prefix, None)
        if sf is not None:
            sf.is_queried = True
            # FIXME: What happens when
            # the user enters a bad prefix?
    else:
        for p in SearchableField.fields_by_prefix:
            SearchableField.fields_by_prefix[
                    p].is_queried = True
        partial_query = input

    project_max = 5
    lang_max = 5

    suggestions = []

    if sf_project.is_queried:

        # Compile list of projects
        projects_by_name = Project.objects.filter(
                name__istartswith=partial_query)
        # FIXME: Is __istartswith faster than
        # lowercasing and using startswith?

        # Produce a list of names like ['Exaile', 'GNOME-DO', ...]
        project_names = projects_by_name.values_list('name', flat=True)

        # Limit
        project_names = project_names[:project_max]

        suggestions += [sf_project.prefix + separator + name
                for name in project_names]

    if sf_language.is_queried:

        # For languages, get projects first
        projects_by_lang = Project.objects.filter(
                language__istartswith=partial_query)

        # Then use bugs to compile a list of languages.
        langs = projects_by_lang.values_list(
                'language', flat=True).order_by(
                        'language')[:lang_max]

        if langs:

            suggestions += [sf_language.prefix + separator + lang
                    for lang in langs]

    return suggestions

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
# vim: set ai ts=4 sw=4 et:
