import mysite.search.models
import mysite.search.views
import collections

class Query:
    def __init__(self, terms, facets): 
        self.terms = terms
        self.facets = facets

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
        active_facets = []
        for facet in possible_facets:
            if GET.get(facet):
                active_facets[facet] = GET.get(facet)
        terms_string = GET.get('q', '')
        terms = Query.split_into_terms(query)

        return Query(terms=terms, facets=active_facets)

    def get_bugs_unordered(self):
        return Bug.open_ones.filter(self.get_Q())

    def __bool__(self):
        return self.terms or self.active_facets

    def get_Q(self):
        """Get a Q object which can be passed to Bug.open_ones.filter()"""

        # Begin constructing a filter
        q = Q(True)

        if 'toughness' in self.facets and facets['toughness'] in ['bitesize', 'bite-size']:
            q &= Q(good_for_newcomers=True)

        if 'language' in facets:
            q &= Q(project__language__iexact=facets['language'])

        for word in self.terms:
            whole_word = "[[:<:]]%s[[:>:]]" % (
                    mysite.base.controllers.mysql_regex_escape(word))
            terms_disjunction = (
                    Q(project__language__iexact=word) |
                    Q(title__iregex=whole_word) |
                    Q(description__iregex=whole_word) |
                    Q(project__name__iregex=whole_word) # 'firefox' grabs 'mozilla fx'.
                    )
            q &= terms_disjunction

        return q

class Facet:
    def __init__(self, name_in_GET, sidebar_name, description_above_results, values):
        self.name_in_GET = name_in_GET
        self.sidebar_name = sidebar_name
        self.description_above_results = description_above_results
        self.values = values

    @staticmethod
    def get_all(relative_to_query=None):
        if relative_to_query:
            bugs = Bugs.open_ones.filter(query.get_Q)
        else:
            bugs = Bugs.open_ones.all()

        if not bugs:
            return []

        distinct_language_columns = bugs.values('project__language').distinct()
        languages = [x['project__language'] for x in distinct_language_columns]
        values = []
        for lang in languages:
            values.append((lang, bugs.filter(project__language=lang).count()))

        # The languages facet is based on the project languages, "for now"
        facet_language = Facet(
                name_in_GET="language",
                sidebar_name="by main project language",
                description_above_results="projects primarily coded in %s",
                values=languages)
        facets.append(facet_language)

        facet_toughness = Facet(
                name_in_GET="toughness",
                sidebar_name="by toughness",
                description_above_results="where toughness = %s",
                values="bite-size")
        facets.append(facet_toughness)

        return facets
