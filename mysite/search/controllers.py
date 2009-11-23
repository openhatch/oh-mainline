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
    ret['Language'] = collections.defaultdict(int)
    projects = bugs.only('project').distinct()
    for p in projects:
        ret['Language'][p.language] = 0 # This is to be used for the count. A a a.

    #for bug in bugs:
    #   ret['Language'][bug.project.language] += 1

    # convert from defaultdict so items will work in dj templates.
    ret['Language'] = dict(ret['Language']) 

    return ret
