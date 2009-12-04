import mysite.search.models
import mysite.search.views
import collections
import urllib
import re
from django.db.models import Q

def order_bugs(query):
    # Minus sign: reverse order
    # Minus good for newcomers: this means true values
    # (like 1) appear before false values (like 0)
    # Minus last touched: Old bugs last.
    return query.order_by('-good_for_newcomers', '-last_touched')

class Query:
    
    def __init__(self, terms=None, active_facet_options=None, terms_string=None): 
        self.terms = terms or []
        self.active_facet_options = active_facet_options or {}
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
        possible_facets = ['language', 'toughness']

        active_facet_options = {}
        for facet in possible_facets:
            if GET.get(facet):
                active_facet_options[facet] = GET.get(facet)
        terms_string = GET.get('q', '')
        terms = Query.split_into_terms(terms_string)

        return Query(terms=terms, active_facet_options=active_facet_options, terms_string=terms_string)

    def get_bugs_unordered(self):
        return mysite.search.models.Bug.open_ones.filter(self.get_Q())

    def __nonzero__(self):
        if self.terms or self.active_facet_options:
            return 1
        return 0

    def get_Q(self, exclude_active_facets=False):
        """Get a Q object which can be passed to Bug.open_ones.filter()"""

        # Begin constructing a conjunction of Q objects (filters)
        q = Q()

        toughness_is_active = ('toughness' in self.active_facet_options.keys())
        exclude_toughness = exclude_active_facets and toughness_is_active
        if (self.active_facet_options.get('toughness', None) == 'bitesize'
                and not exclude_toughness):
            q &= Q(good_for_newcomers=True)

        language_is_active = ('language' in self.active_facet_options.keys())
        exclude_language = exclude_active_facets and language_is_active
        if 'language' in self.active_facet_options and not exclude_language: 
            q &= Q(project__language__iexact=self.active_facet_options['language'])

        for word in self.terms:
            whole_word = "[[:<:]]%s[[:>:]]" % (
                    mysite.base.controllers.mysql_regex_escape(word))
            terms_disjunction = (
                    Q(project__language__iexact=word) |
                    Q(title__iregex=whole_word) |
                    Q(description__iregex=whole_word) |

                    # 'firefox' grabs 'mozilla firefox'.
                    Q(project__name__iregex=whole_word)
                    )
            q &= terms_disjunction

        return q

    def get_facet_options(self, facet_name, option_names):

        def get_facet_option_data(option_name):
            # Create a Query for this option. 

            # This Query is sensitive to the currently active facet options...
            GET_data = dict(self.active_facet_options)

            # ...except the toughness facet option in question.
            GET_data.update({
                'q': self.terms_string,
                facet_name: option_name,
                })
            query_string = urllib.urlencode(GET_data)
            query = Query.create_from_GET_data(GET_data)
            return {
                    'name': option_name or 'any',
                    'count': query.get_bugs_unordered().count(),
                    'query_string': query_string
                    }

        return [get_facet_option_data(n) for n in option_names]

    def get_possible_facets(self):

        bugs = mysite.search.models.Bug.open_ones.filter(self.get_Q())

        toughness_options = self.get_facet_options('toughness', ['bitesize', ''])

        language_options = self.get_facet_options('language', self.get_language_names() + [''])

        possible_facets = { 
                # The languages facet is based on the project languages, "for now"
                'language': {
                    'name_in_GET': "language",
                    'sidebar_name': "main project language",
                    'description_above_results': "projects primarily coded in %s",
                    'options': language_options,
                    },
                'toughness': {
                    'name_in_GET': "toughness",
                    'sidebar_name': "toughness",
                    'description_above_results': "where toughness = %s",
                    'options': toughness_options,
                    }
                }

        return possible_facets

    def get_GET_data(self):
        GET_data = {'q': self.terms_string}
        GET_data.update(self.active_facet_options)
        return GET_data

    def get_language_names(self):

        GET_data = self.get_GET_data()
        if 'language' in GET_data:
            del GET_data['language']
        query_without_language_facet = Query.create_from_GET_data(GET_data)

        bugs = query_without_language_facet.get_bugs_unordered()
        distinct_language_columns = bugs.values('project__language').distinct()
        languages = [x['project__language'] for x in distinct_language_columns]
        languages = [l for l in languages if l]
        return languages

def get_bug_tracker_count():
    """Retrieve the number of bug trackers currently indexed."""
    # FIXME: Calculate this automatically.
    return 49
