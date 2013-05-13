# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponse, QueryDict, HttpResponseServerError, HttpResponseRedirect
from django.core import serializers
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
try:
    from urlparse import parse_qsl
except ImportError:
    from cgi import parse_qsl # Python 2.5 on deployment


from mysite.search.models import Project
import mysite.search.view_helpers 
import mysite.base.view_helpers
import mysite.base.unicode_sanity
from mysite.base.view_helpers import render_response

import datetime
from dateutil import tz
import pytz
from django.utils import simplejson
import mysite.search.forms
import mysite.base.decorators

# Via http://www.djangosnippets.org/snippets/1435/
def encode_datetime(obj):
    if isinstance(obj, datetime.date):
        fixed = datetime.datetime(obj.year, obj.month, obj.day, tzinfo=pytz.utc)
        obj = fixed
    if isinstance(obj, datetime.datetime):
        return obj.astimezone(tz.tzutc()).strftime('%Y-%m-%dT%H:%M:%SZ')
    raise TypeError("%s" % type(obj) + repr(obj) + " is not JSON serializable")

def fetch_bugs(request, invalid_subscribe_to_alert_form=None):
    # Make the query string keys lowercase using a redirect.
    if any([k.lower() != k for k in request.GET.keys()]):
        new_GET = {}
        for key in request.GET.keys():
            new_GET[key.lower()] = request.GET[key]
        return HttpResponseRedirect(reverse(fetch_bugs) + '?' + mysite.base.unicode_sanity.urlencode(new_GET))

    if request.user.is_authenticated():
        person = request.user.get_profile()
        suggestion_keys = person.get_recommended_search_terms()
    else:
        suggestion_keys = []

    suggestions = [(i, k, False) for i, k in enumerate(suggestion_keys)]

    format = request.GET.get('format', None)
    start = int(request.GET.get('start', 1))
    end = int(request.GET.get('end', 10))

    total_bug_count = 0

    query = mysite.search.view_helpers.Query.create_from_GET_data(request.GET)

    if query:
        bugs = query.get_bugs_unordered()

        # Sort
        bugs = mysite.search.view_helpers.order_bugs(bugs)

        total_bug_count = bugs.count()

        bugs = bugs[start-1:end]

    else:
        bugs = []

    data = {}
    data['query'] = query

    prev_page_query_str = QueryDict('')
    prev_page_query_str = prev_page_query_str.copy()
    next_page_query_str = QueryDict('')
    next_page_query_str = next_page_query_str.copy()
    if query:
        prev_page_query_str['q'] = query.terms_string
        next_page_query_str['q'] = query.terms_string
    if format:
        prev_page_query_str['format'] = format
        next_page_query_str['format'] = format
    for facet_name, selected_option in query.active_facet_options.items():
        prev_page_query_str[facet_name] = selected_option
        next_page_query_str[facet_name] = selected_option
    diff = end - start
    prev_page_query_str['start'] = start - diff - 1
    prev_page_query_str['end'] = start - 1
    next_page_query_str['start'] = end + 1
    next_page_query_str['end'] = end + diff + 1

    data['start'] = start
    data['end'] = min(end, total_bug_count)
    data['prev_page_url'] = '/search/?' + prev_page_query_str.urlencode()
    data['next_page_url'] = '/search/?' + next_page_query_str.urlencode()
    data['this_page_query_str'] = mysite.base.unicode_sanity.urlencode(request.GET)

    is_this_page_1 = (start <= 1)
    is_this_the_last_page = ( end >= (total_bug_count - 1) )
    data['show_prev_page_link'] = not is_this_page_1
    data['show_next_page_link'] = not is_this_the_last_page

    if request.GET.get('confirm_email_alert_signup', ''):
        data['confirm_email_alert_signup'] = 1

    # If this the last page of results, display a form allowing user to
    # subscribe to a Volunteer Opportunity search alert
    if query and is_this_the_last_page:
        if invalid_subscribe_to_alert_form:
            alert_form = invalid_subscribe_to_alert_form
        else:
            initial = {
                    'query_string': request.META['QUERY_STRING'],
                    'how_many_bugs_at_time_of_request': len(bugs)
                    }
            if request.user.is_authenticated():
                initial['email'] = request.user.email
            alert_form = mysite.search.forms.BugAlertSubscriptionForm(initial=initial)
        data['subscribe_to_alert_form'] = alert_form

    # FIXME
    # The template has no way of grabbing what URLs to put in the [x]
    # So we help it out here by hacking around our fruity list-of-dicts
    # data structure.
    facet2any_query_string = {}
    for facet in query.active_facet_options:
        facet2any_query_string[facet] = query.get_facet_options(
            facet, [''])[0]['query_string']

    Bug = mysite.search.models.Bug
    from django.db.models import Q, Count
    data['popular_projects'] = list(Project.objects.filter(name__in=['Miro', 'GnuCash', 'brasero', 'Evolution Exchange', 'songbird']).order_by('name').reverse())
    data['all_projects'] = Project.objects.values('pk','name').filter(bug__looks_closed=False).annotate(Count('bug')).order_by('name')

    Person = mysite.profile.models.Person
    import random
    random_start = int(random.random() * 700)
    data['contributors'] = Person.objects.all()[random_start:random_start+5]
    data['contributors2'] = Person.objects.all()[random_start+10:random_start+15]
    data['languages'] = Project.objects.all().values_list('language', flat=True).order_by('language').exclude(language='').distinct()[:4]

    if format == 'json':
        # FIXME: Why `alert`?
        return bugs_to_json_response(data, bugs, request.GET.get(
            'jsoncallback', 'alert'))
    else:
        data['user'] = request.user
        data['suggestions'] = suggestions
        data['bunch_of_bugs'] = bugs
        data['url'] = 'http://launchpad.net/'
        data['total_bug_count'] = total_bug_count
        data['facet2any_query_string'] = facet2any_query_string
        data['project_count'] = mysite.search.view_helpers.get_project_count()

        return mysite.base.decorators.as_view(request, 'search/search.html', data, slug=None)

def bugs_to_json_response(data, bunch_of_bugs, callback_function_name=''):
    """ The search results page accesses this view via jQuery's getJSON method, 
    and loads its results into the DOM."""
    # Purpose of this code: Serialize the list of bugs
    # Step 1: Pull the bugs out of the database, getting them back
    #   as simple Python objects
    
    obj_serializer = serializers.get_serializer('python')()
    bugs = obj_serializer.serialize(bunch_of_bugs)

    # Step 2: With a (tragically) large number of database calls, 
    # loop over these objects, replacing project primary keys with project
    # display names.
    for bug in bugs:
        project = Project.objects.get(pk=int(bug['fields']['project']))
        bug['fields']['project'] = project.display_name

    # Step 3: Create a JSON-happy list of key-value pairs
    data_list = [{'bugs': bugs}]

    # Step 4: Create the string form of the JSON
    json_as_string = simplejson.dumps(data_list, default=encode_datetime)

    # Step 5: Prefix it with the desired callback function name
    json_string_with_callback = callback_function_name + '(' + json_as_string + ')'

    # Step 6: Return that.
    return HttpResponse(json_string_with_callback)

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
      - project.display_name
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
        # XXX: This searches on display_name, as that is what the user is more
        # likely to be trying to type. And also because it is display_name that
        # search uses to query projects.
        projects_by_name = Project.objects.filter(
                display_name__istartswith=partial_query)
        # FIXME: Is __istartswith faster than
        # lowercasing and using startswith?

        # Produce a list of names like ['Exaile', 'GNOME-DO', ...]
        project_names = projects_by_name.values_list('display_name', flat=True)

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

def subscribe_to_bug_alert_do(request):
    confirmation_query_string_fragment = "&confirm_email_alert_signup=1"
    alert_form = mysite.search.forms.BugAlertSubscriptionForm(request.POST)
    query_string = request.POST.get('query_string', '') # Lacks initial '?'
    query_string = query_string.replace(confirmation_query_string_fragment, '')
    next = reverse(fetch_bugs) + '?' + query_string
    if alert_form.is_valid():
        alert = alert_form.save()
        if request.user.is_authenticated():
            alert.user = request.user
            alert.save()
        next += confirmation_query_string_fragment
        return HttpResponseRedirect(next)
    elif query_string:
        # We want fetch_bugs to get the right query string but we can't exactly
        # do that. What we *can* do is fiddle with the request obj we're about
        # to pass to fetch_bugs.
        # Commence fiddling.
        request.GET = dict(parse_qsl(query_string))
        return fetch_bugs(request, alert_form)
    else:
        # If user tries to do a different bug search after invalid form input
        return HttpResponseRedirect(next + request.META['QUERY_STRING'])

def project_has_icon(request, project_name):
    p = get_object_or_404(Project, name=project_name)
    if p.date_icon_was_fetched_from_ohloh is None:
        return HttpResponse("keep polling")
    return HttpResponse(p.get_url_of_icon_or_generic())


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
