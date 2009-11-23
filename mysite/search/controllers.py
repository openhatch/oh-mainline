import mysite.search.models
import mysite.search.views
import collections

def discover_available_facets(query_words=[]):
    """
    Returns facet2value2count
    """
    bugs = mysite.search.views.get_bugs_by_query_words(query_words)

    if not bugs:
        return []

    # The languages facet is based on the project languages, "for now"
    ret = {}
    ret['Language'] = dict()

    language_columns = mysite.search.models.Project.objects.all().only('language')
    distinct_language_columns = language_columns.distinct().values('language')
    languages = [x['language'] for x in distinct_language_columns]
    for lang in languages:
        ret['Language'][lang] = bugs.filter(project__language=lang).count()

    return ret
