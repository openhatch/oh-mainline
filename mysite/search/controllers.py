import mysite.search.models
import mysite.search.views
import collections
import urllib
import re
from django.db.models import Q

class Query:
    
    def __init__(self, terms, facets, terms_string=None): 
        self.terms = terms
        self.facets = facets
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
    def create_from_GET(GET):
        possible_facets = ['language', 'toughness']

        active_facets = {}
        for facet in possible_facets:
            if GET.get(facet):
                active_facets[facet] = GET.get(facet)
        terms_string = GET.get('q', '')
        terms = Query.split_into_terms(terms_string)

        return Query(terms=terms, facets=active_facets, terms_string=terms_string)

    def get_bugs_unordered(self):
        return mysite.search.models.Bug.open_ones.filter(self.get_Q())

    def __bool__(self):
        return self.terms or self.active_facets

    def get_Q(self):
        """Get a Q object which can be passed to Bug.open_ones.filter()"""

        # Begin constructing a conjunction of Q objects (filters)
        q = Q()

        if self.facets.get('toughness', None) in ['bitesize']:
            q &= Q(good_for_newcomers=True)

        if 'language' in self.facets:
            q &= Q(project__language__iexact=self.facets['language'])

        for word in self.terms:
            whole_word = "[[:<:]]%s[[:>:]]" % (
                    mysite.base.controllers.mysql_regex_escape(word))
            terms_disjunction = (
                    Q(project__language__iexact=word) |
                    Q(title__iregex=whole_word) |
                    Q(description__iregex=whole_word) |

                    # 'firefox' grabs 'mozilla fx'.
                    Q(project__name__iregex=whole_word)
                    )
            q &= terms_disjunction

        return q

    def get_possible_facets(self):
        bugs = mysite.search.models.Bug.open_ones.filter(self.get_Q())

        if not bugs:
            return []

        
        bitesize_get_parameters = dict(self.facets)
        bitesize_get_parameters.update({
            'q': self.terms_string,
            'toughness': 'bitesize',
            })
        bitesize_query_string = urllib.urlencode(bitesize_get_parameters)


        facets = { 
                # The languages facet is based on the project languages, "for now"
                'language': {
                    'name_in_GET': "language",
                    'sidebar_name': "by main project language",
                    'description_above_results': "projects primarily coded in %s",
                    'values': [], # populated below
                    },
                'toughness': {
                    'name_in_GET': "toughness",
                    'sidebar_name': "by toughness",
                    'description_above_results': "where toughness = %s",
                    'values': [
                        {
                            'name': "bitesize",
                            'count': 0,
                            'query_string': bitesize_query_string
                            }
                        ]
                    }
                }

        distinct_language_columns = bugs.values('project__language').distinct()
        languages = [x['project__language'] for x in distinct_language_columns]
        for lang in sorted(languages):

            lang_get_parameters = dict(self.facets)
            lang_get_parameters.update({
                'q': self.terms_string,
                'language': lang,
                })
            lang_query_string = urllib.urlencode(lang_get_parameters)

            facets['language']['values'].append({
                'name': lang,
                'count': bugs.filter(project__language=lang).count(),
                'query_string': lang_query_string
                })

        return facets
