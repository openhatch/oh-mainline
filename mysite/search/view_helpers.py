# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010 OpenHatch, Inc.
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

import mysite.search.models
import mysite.search.views
import mysite.base.unicode_sanity
import mysite.base.decorators
import re
import hashlib
import django.core.cache
from django.db import connection
from django.db.models import Q, Count
import logging

CCT = 'hit_count_cache_timestamp'

def order_bugs(query):
    # Minus sign: reverse order
    # Minus good for newcomers: this means true values
    # (like 1) appear before false values (like 0)
    # Minus last touched: Old bugs last.
    return query.order_by('-good_for_newcomers', '-last_touched')

class Query:

    def __init__(self, terms=None, active_facet_options=None, any_facet=False, terms_string=None):
        self.terms = terms or []
        self.active_facet_options = (mysite.base.decorators.no_str_in_the_dict(active_facet_options)
                                     or {})
        self.any_facet = any_facet
        if type(terms_string) == str:
            terms_string = unicode(terms_string, 'utf-8')
        self._terms_string = terms_string

    @property
    def terms_string(self):
        if self._terms_string is None:
            raise ValueError
        return self._terms_string

    @staticmethod
    def split_into_terms(string):
        # We're given some query terms "between quotes"
        # and some glomped on with spaces.
        # Strategy: Find the strings validly inside quotes, and remove them
        # from the original string. Then split the remainder (and probably trim
        # whitespace from the remaining terms).
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

    @staticmethod
    def create_from_GET_data(GET):
        possible_facets = [u'language', u'toughness', u'contribution_type',
                           u'project']

        active_facet_options = {}
        any_facet = False
        for facet in possible_facets:
            if GET.get(facet):
                active_facet_options[facet] = GET.get(facet)
            elif GET.get(facet) == '': # Only select any_facet if a facet is empty string, not None
                any_facet = True
        terms_string = GET.get('q', u'')
        terms = Query.split_into_terms(terms_string)

        return Query(terms=terms, active_facet_options=active_facet_options, any_facet=any_facet, terms_string=terms_string)

    def get_bugs_unordered(self):
        return mysite.search.models.Bug.open_ones.filter(self.get_Q())

    def __nonzero__(self):
        if self.terms or self.active_facet_options or self.any_facet:
            return 1
        return 0

    def get_Q(self, exclude_active_facets=False):
        """Get a Q object which can be passed to Bug.open_ones.filter()"""

        # Begin constructing a conjunction of Q objects (filters)
        q = Q()

        # toughness facet
        toughness_is_active = ('toughness' in self.active_facet_options.keys())
        exclude_toughness = exclude_active_facets and toughness_is_active
        if (self.active_facet_options.get('toughness', None) == 'bitesize'
                and not exclude_toughness):
            q &= Q(good_for_newcomers=True)

        # language facet
        language_is_active = (u'language' in self.active_facet_options.keys())
        exclude_language = exclude_active_facets and language_is_active
        if u'language' in self.active_facet_options and not exclude_language:
            language_value = self.active_facet_options[u'language']
            if language_value == 'Unknown':
                language_value=''
            q &= Q(project__language__iexact=language_value)

        # project facet
        # FIXME: Because of the way the search page is set up, we have to use
        # the project's display_name to identify the project, which isn't
        # very nice.
        project_is_active = (u'project' in self.active_facet_options.keys())
        exclude_project = exclude_active_facets and project_is_active
        if u'project' in self.active_facet_options and not exclude_project:
            project_value = self.active_facet_options[u'project']
            q &= Q(project__display_name__iexact=project_value)

        # contribution type facet
        contribution_type_is_active = ('contribution_type' in
                                       self.active_facet_options.keys())
        exclude_contribution_type = exclude_active_facets and contribution_type_is_active
        if (self.active_facet_options.get('contribution_type', None) == 'documentation'
                and not exclude_contribution_type):
            q &= Q(concerns_just_documentation=True)

        # NOTE: This is a terrible hack. We should stop doing this and
        # just ditch this entire class and swap it out for something like
        # haystack.
        if connection.vendor == 'sqlite':
            use_regexes = False
        else:
            use_regexes = True

        for word in self.terms:
            if use_regexes:
                whole_word = "[[:<:]]%s($|[[:>:]])" % (
                    mysite.base.view_helpers.mysql_regex_escape(word))
                terms_disjunction = (
                    Q(project__language__iexact=word) |
                    Q(title__iregex=whole_word) |
                    Q(description__iregex=whole_word) |
                    Q(as_appears_in_distribution__iregex=whole_word) |

                    # 'firefox' grabs 'mozilla firefox'.
                    Q(project__name__iregex=whole_word)
                    )
            else:
                terms_disjunction = (
                    Q(project__language__icontains=word) |
                    Q(title__icontains=word) |
                    Q(description__icontains=word) |
                    Q(as_appears_in_distribution__icontains=word) |

                    # 'firefox' grabs 'mozilla firefox'.
                    Q(project__name__icontains=word)
                    )

            q &= terms_disjunction

        return q

    def get_facet_option_data(self, facet_name, option_name):

        # Create a Query for this option.

        # This Query is sensitive to the currently active facet options...
        GET_data = dict(self.active_facet_options)

        # ...except the toughness facet option in question.
        GET_data.update({
            u'q': unicode(self.terms_string),
            unicode(facet_name): unicode(option_name),
            })
        query_string = mysite.base.unicode_sanity.urlencode(GET_data)
        query = Query.create_from_GET_data(GET_data)
        the_all_option = u'any'
        name = option_name or the_all_option

        active_option_name = self.active_facet_options.get(facet_name, None)

        # This facet isn't active...
        is_active = False

        # ...unless there's an item in active_facet_options mapping the
        # current facet_name to the option whose data we're creating...
        if active_option_name == option_name:
            is_active = True

        # ...or if this is the 'any' option and there is no active option
        # for this facet.
        if name == the_all_option and active_option_name is None:
            is_active = True

        return {
                'name': name,
                'count': query.get_or_create_cached_hit_count(),
                'query_string': query_string,
                'is_active': is_active
                }

    def get_facet_options(self, facet_name, option_names):
        # Assert that there are only unicode strings in this list
        option_names = mysite.base.decorators.no_str_in_the_list(option_names)

        options = [self.get_facet_option_data(facet_name, n) for n in option_names]
        # ^^ that's a list of facet options, where each "option" is a
        # dictionary that looks like this:
        # {
        #   'name': name,
        #   'count': query.get_or_create_cached_hit_count(),
        #   'query_string': query_string,
        #   'is_active': is_active
        # }

        # Now we're gonna sort these dictionaries.
        # Active facet options first. Then non-'Unknowns'. Then by number of
        # bugs. Then alphabetically.

        # Note that these keys are in ascending order of precedence. So the
        # last one trumps all the previous sortings.

        options.sort(key=lambda x: x['name'])
        # Sort alphabetically by name. (This appears first because it has the
        # lowest precedence.)

        options.sort(key=lambda x: x['count'], reverse=True) # 3 sorts before 50
        # We want facet options that contain lots of bugs to appear at the top.
        # If you sort (naively) by x['count'], then the lower numbers appear
        # higher in the list. Let's reverse that with reverse=True.

        options.sort(
                key=lambda x: (facet_name == 'language') and (x['name'] == 'Unknown'))
        # We want the Unknown language to appear last, unless it's active. If
        # the key lambda function returns False, then those options appear
        # first (because False appears before True), which is what we want.

        options.sort(key=lambda x: x['is_active'], reverse=True)
        # We want the value True to sort before the value False. So let's
        # reverse this comparison (because normally False sorts before True,
        # just like zero comes before one).

        return options

    def get_possible_facets(self):

        project_options = self.get_facet_options(u'project', self.get_project_names())

        toughness_options = self.get_facet_options(u'toughness', [u'bitesize'])

        contribution_type_options = self.get_facet_options(
            u'contribution_type', [u'documentation'])

        language_options = self.get_facet_options(u'language', self.get_language_names())

        # looks something like:
        # [{'count': 1180L, 'query_string': 'q=&language=Python', 'is_active': False, 'name': u'Python'}, {'count': 478L, 'query_string': 'q=&language=C%23', 'is_active': False, 'name': u'C#'}, {'count': 184L, 'query_string': 'q=&language=Unknown', 'is_active': False, 'name': 'Unknown'}, {'count': 532L, 'query_string': 'q=&language=C', 'is_active': False, 'name': u'C'}, {'count': 2374L, 'query_string': 'q=&language=', 'is_active': True, 'name': 'any'}]

        possible_facets = (
                # The languages facet is based on the project languages, "for now"
                (u'language', {
                    u'name_in_GET': u"language",
                    u'sidebar_heading': u"Languages",
                    u'description_above_results': u"projects primarily coded in %s",
                    u'options': language_options,
                    u'the_any_option': self.get_facet_options(u'language', [u''])[0],
                    }),
                (u'project', {
                    u'name_in_GET': u'project',
                    u'sidebar_heading': u'Projects',
                    u'description_above_results': 'in the %s project',
                    u'options': project_options,
                    u'the_any_option': self.get_facet_options(u'project', [u''])[0],
                }),
                (u'toughness', {
                    u'name_in_GET': u"toughness",
                    u'sidebar_heading': u"Toughness",
                    u'description_above_results': u"where toughness = %s",
                    u'options': toughness_options,
                    u'the_any_option': self.get_facet_options(u'toughness', [u''])[0],
                }),
                (u'contribution type', {
                    u'name_in_GET': u"contribution_type",
                    u'sidebar_heading': u"Just bugs labeled...",
                    u'description_above_results': u"which need %s",
                    u'options': contribution_type_options,
                    u'the_any_option': self.get_facet_options(u'contribution_type', [u''])[0],
                    })
            )

        return possible_facets

    def get_GET_data(self):
        GET_data = {u'q': unicode(self.terms_string)}
        GET_data.update(self.active_facet_options)
        return GET_data

    def get_language_names(self):

        GET_data = self.get_GET_data()
        if u'language' in GET_data:
            del GET_data[u'language']
        query_without_language_facet = Query.create_from_GET_data(GET_data)

        bugs = query_without_language_facet.get_bugs_unordered()
        distinct_language_columns = bugs.values(u'project__language').distinct()
        languages = [x[u'project__language'] for x in distinct_language_columns]
        languages = [l or u'Unknown' for l in languages]

        # Add the active language facet, if there is one
        if u'language' in self.active_facet_options:
            active_language = self.active_facet_options[u'language']
            if active_language not in languages:
                languages.append(active_language)

        return languages

    def get_active_facet_options_except_toughness(self):
        if 'toughness' not in self.active_facet_options:
            return self.active_facet_options

        options = self.active_facet_options.copy()
        del options['toughness']
        return options

    def get_project_names(self):
        Project = mysite.search.models.Project

        GET_data = self.get_GET_data()
        if u'project' in GET_data:
            del GET_data[u'project']
        query_without_project_facet = Query.create_from_GET_data(GET_data)

        bugs = query_without_project_facet.get_bugs_unordered()
        project_ids = list(bugs.values_list(u'project__id', flat=True).distinct())
        projects = Project.objects.filter(id__in=project_ids)
        project_names = [project.display_name or u'Unknown' for project in projects]

        # Add the active project facet, if there is one
        if u'project' in self.active_facet_options:
            name_of_active_project = self.active_facet_options[u'project']
            if name_of_active_project not in project_names:
                project_names.append(name_of_active_project)

        return project_names

    def get_sha1(self):

        # first, make a dictionary mapping strings to strings
        simple_dictionary = {}

        # add terms_string
        simple_dictionary[u'terms'] = str(sorted(self.terms))

        # add active_facet_options
        simple_dictionary[u'active_facet_options'] = str(sorted(self.active_facet_options.items()))

        stringified = str(sorted(simple_dictionary.items()))
        # then return a hash of our sorted items self.
        return hashlib.sha1(stringified).hexdigest() # sadly we cause a 2x space blowup here

    def get_hit_count_cache_key(self):
        hashed_query = self.get_sha1()
        hcc_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string(CCT)
        hit_count_cache_key = "hcc_%s_%s" % (hashlib.sha1(hcc_timestamp.__str__()).hexdigest(), hashed_query)
        return hit_count_cache_key

    def get_or_create_cached_hit_count(self):
        # Get the cache key used to store the hit count.
        hit_count_cache_key = self.get_hit_count_cache_key()
        # Fetch the hit count from the cache.
        hit_count = django.core.cache.cache.get(hit_count_cache_key)
        logging.debug( "Cached hit count: " + str(hit_count))
        # We need to be careful to check if the count is None, rather than just if the
        # count is a false value. That's because a value of zero is still a cached value;
        # if we just use a boolean test, we would mistake the zero value for an empty
        # cache and regenerate the cache needlessly.
        if hit_count is None:
            # There is nothing in the cache for this key. Either the
            # query has not been counted before, or the Timestamp has
            # been refreshed due to a change in the Bug objects. So get
            # a new count.
            hit_count = self.get_bugs_unordered().count()
            django.core.cache.cache.set(hit_count_cache_key, hit_count)
            logging.info("Set hit count: " + str(hit_count))
        # TODO: Add sql query in the logging
        logging.info("Hit Count:" + str(hit_count))

        return hit_count

    def get_query_string(self):
        GET_data = self.get_GET_data()
        query_string = mysite.base.unicode_sanity.urlencode(GET_data)
        logging.info("Query is " + query_string)
        return query_string

def get_project_count():
    """Retrieve the number of projects currently indexed."""
    bugs = mysite.search.models.Bug.all_bugs.all()
    return bugs.values(u'project').distinct().count()

def get_projects_with_bugs():
    """
    Return a sorted list of all the Projects for which we've indexed bugs.
    """
    projects = mysite.search.models.Project.objects.annotate(
        bug_count=Count('bug')).filter(
        bug_count__gt=0).order_by(u'display_name')
    return projects

def get_cited_projects_lacking_bugs():
    project_ids = mysite.profile.models.PortfolioEntry.published_ones.all().values_list('project_id', flat=True)
    return mysite.search.models.Project.objects.filter(id__in=project_ids).annotate(
        bug_count=Count('bug')).filter(bug_count=0)
