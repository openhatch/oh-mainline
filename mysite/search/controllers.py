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
    ret['language'] = dict()

    distinct_language_columns = bugs.values('project__language').distinct()
    languages = [x['project__language'] for x in distinct_language_columns]
    for lang in languages:
        ret['language'][lang] = bugs.filter(project__language=lang).count()

    return ret
