import mysite.search.models
import mysite.search.views
import collections
import urllib
import re
import sha
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
        possible_facets = ['language', 'toughness', 'contribution_type']

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

        # toughness facet
        toughness_is_active = ('toughness' in self.active_facet_options.keys())
        exclude_toughness = exclude_active_facets and toughness_is_active
        if (self.active_facet_options.get('toughness', None) == 'bitesize'
                and not exclude_toughness):
            q &= Q(good_for_newcomers=True)

        # language facet
        language_is_active = ('language' in self.active_facet_options.keys())
        exclude_language = exclude_active_facets and language_is_active
        if 'language' in self.active_facet_options and not exclude_language: 
            q &= Q(project__language__iexact=self.active_facet_options['language'])

        # contribution type facet
        contribution_type_is_active = ('contribution_type' in
                                       self.active_facet_options.keys())
        exclude_contribution_type = exclude_active_facets and contribution_type_is_active
        if (self.active_facet_options.get('contribution_type', None) == 'documentation'
                and not exclude_contribution_type):
            q &= Q(concerns_just_documentation=True)


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

            caller_query = self
            # ^^^ NB: The value of 'self' is determined by the caller environment.

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
            name = option_name or 'any'

            active_option_name = caller_query.active_facet_options.get(facet_name, None)

            # This facet isn't active...
            is_active = False

            # ...unless there's an item in active_facet_options mapping the
            # current facet_name to the option whose data we're creating...
            if active_option_name == option_name:
                is_active = True

            # ...or if this is the 'any' option and there is no active option
            # for this facet.
            if name == 'any' and active_option_name is None:
                is_active = True

            return {
                    'name': name,
                    'count': query.get_or_create_cached_hit_count(),
                    'query_string': query_string,
                    'is_active': is_active
                    }

        return [get_facet_option_data(n) for n in option_names]

    def get_possible_facets(self):

        bugs = mysite.search.models.Bug.open_ones.filter(self.get_Q())

        toughness_options = self.get_facet_options('toughness', ['bitesize', ''])

        contribution_type_options = self.get_facet_options(
            'contribution_type', ['documentation', ''])

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
                    },
                'Contribution type': {
                    'name_in_GET': "contribution_type",
                    'sidebar_name': "contribution type",
                    'description_above_results': "where contribution_type = %s",
                    'options': contribution_type_options,
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

        # Add the active language facet, if there is one
        if 'language' in self.active_facet_options:
            active_language = self.active_facet_options['language']
            if active_language not in languages:
                languages.append(active_language)

        return languages
  
    def get_sha1(self):

        # first, make a dictionary mapping strings to strings
        simple_dictionary = {}

        # add terms_string
        simple_dictionary['terms'] = str(sorted(self.terms))

        # add active_facet_options
        simple_dictionary['active_facet_options'] = str(sorted(self.active_facet_options.items()))

        stringified = str(sorted(simple_dictionary.items()))
        # then return a hash of our sorted items self.
        return sha.sha(stringified).hexdigest() # sadly we cause a 2x space blowup here
    
    def get_or_create_cached_hit_count(self):

        existing_hccs = mysite.search.models.HitCountCache.objects.filter(hashed_query=self.get_sha1())
        if existing_hccs:
            hcc = existing_hccs[0]
        else:
            count = self.get_bugs_unordered().count()
            hcc = mysite.search.models.HitCountCache.objects.create(
                    hashed_query=self.get_sha1(),
                    hit_count=count)
        return hcc.hit_count

       
def get_project_count():
    """Retrieve the number of projects currently indexed."""
    bugs = mysite.search.models.Bug.all_bugs.all()
    return bugs.values('project').distinct().count()

def get_projects_with_bugs():
    bugs = mysite.search.models.Bug.all_bugs.all()
    one_bug_dict_per_project = bugs.values('project').distinct().order_by('project__name')
    #project_names = [b['project__name'] for b in one_bug_dict_per_project]
    projects = []
    for bug_dict in one_bug_dict_per_project:
        pk = bug_dict['project']
        projects.append(mysite.search.models.Project.objects.get(pk=pk))
    return projects

def get_projects_having_contributors_but_no_bugs():
    portfolio_entries = mysite.profile.models.PortfolioEntry.objects.filter(
            is_published=True, is_deleted=False)
    # Make this a manager
    one_pfe_dict_per_project = portfolio_entries.values('project').distinct().order_by('project__name')

    projects_with_contributors = []
    for pfe_dict in one_pfe_dict_per_project:
        pk = pfe_dict['project']
        projects_with_contributors.append(mysite.search.models.Project.objects.get(pk=pk))

    projects_with_bugs = get_projects_with_bugs()
    return [p for p in projects_with_contributors if p not in projects_with_bugs]
