import mysite.search.models
import mysite.search.views
import collections

def discover_available_facets(query_words=[]):
    """
    Returns facet2value2count
    """
    bugs = mysite.search.views.get_bugs_by_query_words(query_words)
    # The languages facet is based on the project languages, "for now"
    ret = {}
    ret['Language'] = collections.defaultdict(int)
    projects = set([bug.project for bug in bugs])
    for bug in bugs:
        ret['Language'][bug.project.language] += 1
    ret['Language'] = dict(ret['Language'])
    return ret
