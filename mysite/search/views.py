from django.http import HttpResponse, QueryDict, HttpResponseServerError
from django.shortcuts import render_to_response
from django.core import serializers
from django.db.models import Q
from django.utils.timesince import timesince
from django.utils.html import escape

from mysite.search.models import Bug, Project

import datetime
from dateutil import tz
import pytz
import re
import simplejson

# Via http://www.djangosnippets.org/snippets/1435/
def encode_datetime(obj):
    # {{{
    if isinstance(obj, datetime.date):
        fixed = datetime.datetime(obj.year, obj.month, obj.day, tzinfo=pytz.utc)
        obj = fixed
    if isinstance(obj, datetime.datetime):
        return obj.astimezone(tz.tzutc()).strftime('%Y-%m-%dT%H:%M:%SZ')
    raise TypeError("%s" % type(obj) + repr(obj) + " is not JSON serializable")
    # }}}

def split_query_words(string):
    # We're given some query terms "between quotes"
    # and some glomped on with spaces.
    # Strategy: Find the strings validly inside quotes, and remove them
    # from the original string. Then split the remainder (and probably trim
    # whitespace from the remaining words).
    # {{{
    ret = []
    splitted = re.split(r'(".*?")', string)

    for (index, word) in enumerate(splitted):
        if (index % 2) == 0:
            ret.extend(word.split())
        else:
            assert word[0] == '"'
            assert word[-1] == '"'
            ret.append(word[1:-1])

    return ret
    # }}}

def get_bugs_by_query_words(query_words):
    """Get bugs matching any of the words in 'query_words'."""

    bugs = Bug.objects.all()

    # Filter
    for word in query_words:
        bugs = bugs.filter(
            Q(project__language__iexact=word) |
            Q(title__contains=word) |
            Q(description__contains=word) |
            Q(project__name__iexact=word))

    # Sort
    bugs = bugs.order_by('-last_touched') # Minus sign = reverse order.

    return bugs

def prettify_dates(bugs):
    """Take the dates in the bugs data and say e.g. '8 days ago' rather than '10/01/2009'."""
    for bug in bugs:
        if bug.last_touched:
            try:
                bug.last_touched = timesince(bug.last_touched) + " ago"
                bug.last_touched.split(",")[0] #FIXME: Raffi doesn't understand this line.
            except AttributeError:
                pass
        if bug.last_polled:
            try:
                bug.last_polled = timesince(bug.last_polled) + " ago"
                bug.last_polled.split(",")[0]
            except AttributeError:
                pass
    return bugs

def fetch_bugs(request):
    # {{{

    # FIXME: Give bugs some date field

    if request.user.is_authenticated():
        suggestion_keys = request.user.get_profile().\
                get_recommended_search_terms()
    else:
        suggestion_keys = []

    suggestions = [(i, k, False) for i, k in enumerate(suggestion_keys)]

    query = request.GET.get('language', '')
    query_words = split_query_words(query)
    format = request.GET.get('format', None)
    start = int(request.GET.get('start', 1))
    end = int(request.GET.get('end', 10))

    total_bug_count = 0

    if query:
        bugs = get_bugs_by_query_words(query_words)

        total_bug_count = bugs.count()

        bugs = bugs[start-1:end]

        for b in bugs:
            b.project.icon_url = "/static/images/icons/projects/%s.png" % \
                    b.project.name.lower()

        bugs = prettify_dates(bugs)

        bugs = list(bugs)

        bugs = prettify_dates(bugs)

    else:
        bugs = []

    data = {}
    data['language'] = query
    data['query_words'] = query_words

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

    data['start'] = start
    data['end'] = end
    data['prev_page_url'] = '/search/?' + prev_page_query_str.urlencode()
    data['next_page_url'] = '/search/?' + next_page_query_str.urlencode()

    if format == 'json':
        # FIXME: Why `alert`?
        return bugs_to_json_response(data, bugs, request.GET.get(
            'jsoncallback', 'alert'))
    else:
        data['the_user'] = request.user
        data['suggestions'] = suggestions
        data['bunch_of_bugs'] = bugs
        data['developer_name'] = "Orrin Hatch"
        data['url'] = 'http://launchpad.net/'

        data['total_bug_count'] = total_bug_count
        data['show_prev_page_link'] = start > 1
        data['show_next_page_link'] = end < (total_bug_count - 1)

        return render_to_response('search/search.html', data)
    # }}}

def bugs_to_json_response(data, bunch_of_bugs, callback_function_name=''):
    """ The search results page accesses this view via jQuery's getJSON method, 
    and loads its results into the DOM."""
    # {{{
    # Purpose of this code: Serialize the list of bugs
    # Step 1: Pull the bugs out of the database, getting them back
    #   as simple Python objects
    
    obj_serializer = serializers.get_serializer('python')()
    bugs = obj_serializer.serialize(bunch_of_bugs)

    # Step 2: With a (tragically) large number of database calls, 
    # loop over these objects, replacing project primary keys with project names.
    for bug in bugs:
        project = Project.objects.get(pk=int(bug['fields']['project']))
        bug['fields']['project'] = project.name

    # Step 3: Create a JSON-happy list of key-value pairs
    data_list = [{'bugs': bugs}]

    # Step 4: Create the string form of the JSON
    json_as_string = simplejson.dumps(data_list, default=encode_datetime)

    # Step 5: Prefix it with the desired callback function name
    json_string_with_callback = callback_function_name + '(' + json_as_string + ')'

    # Step 6: Return that.
    return HttpResponse(json_string_with_callback)
    # }}}

def request_jquery_autocompletion_suggestions(request):
    """
    Wraps get_autocompletion_suggestions and
    list_to_jquery_autocompletion_format in an
    HttpRequest -> HttpResponse loop.
    Validates GET parameters. Expected:
        ?q=[suggestion fodder]
    If q is absent or empty, this function
    returns an HttpResponseServerError.
    """
    # {{{
    partial_query = request.GET.get('q', None)
    if (partial_query is None) or (partial_query == ''):
        return HttpResponseServerError("Need partial_query in GET")

    # jQuery autocomplete also gives us this variable:
    # timestamp = request.GET.get('timestamp', None)

    suggestions_list = get_autocompletion_suggestions(partial_query)
    suggestions_string = list_to_jquery_autocompletion_format(
                suggestions_list)
    return HttpResponse(suggestions_string)
    # }}}

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
    # {{{
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
    # }}}

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
# vim: set ai ts=4 sw=4 et nu:
