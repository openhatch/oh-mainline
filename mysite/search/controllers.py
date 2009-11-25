import mysite.search.models
import mysite.search.views
import collections

class Query:
    def __init__(self, words, facets): 
        self.words = words
        self.facets = facets

    @staticmethod
    def create_from_GET(GET):
        possible_facets = ['language', 'toughness']
        active_facets = []
        for facet in possible_facets:
            if GET.get(facet):
                active_facets[facet] = GET.get(facet)
        query = GET.get('q', '')
        query_words = split_query_words(query)

        if query_words or active_facets:
            return Query(words=query_words, facets=active_facets)
        else:
            return None

    def get_bugs_unordered(self):
        return Bug.open_ones.filter(self.get_Q())

    def get_Q(self):
        """Get a Q object which can be passed to Bug.open_ones.filter()"""

        # Begin constructing a filter
        q = Q(True)

        if 'toughness' in self.facets and facets['toughness'] in ['bitesize', 'bite-size']:
            q &= Q(good_for_newcomers=True)

        if 'language' in facets:
            q &= Q(project__language__iexact=facets['language'])

        for word in self.words:
            whole_word = "[[:<:]]%s[[:>:]]" % (
                    mysite.base.controllers.mysql_regex_escape(word))
            words_disjunction = (
                    Q(project__language__iexact=word) |
                    Q(title__iregex=whole_word) |
                    Q(description__iregex=whole_word) |
                    Q(project__name__iregex=whole_word) # 'firefox' grabs 'mozilla fx'.
                    )
            q &= words_disjunction

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
