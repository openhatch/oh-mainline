import mysite.search.models

def discover_available_facets():
    bugs = mysite.search.models.Bug.open_ones.all()
    # The langauges facet is based on the project languages, "for now"
    ret = {}
    ret['Language'] = set()
    projects = set([bug.project for bug in bugs])
    for project in projects:
        ret['Language'].add(project.language)
    return ret

    
        

