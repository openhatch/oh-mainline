import mysite.search.models
import collections

def discover_available_facets():
    """
    Returns facet2value2count
    """
    bugs = mysite.search.models.Bug.open_ones.all()
    # The languages facet is based on the project languages, "for now"
    ret = {}
    ret['Language'] = collections.defaultdict(int)
    projects = set([bug.project for bug in bugs])
    for project in projects:
        ret['Language'][project.language] += 1
    ret['Language'] = dict(ret['Language'])
    return ret
