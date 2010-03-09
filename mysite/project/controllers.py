import mysite.search.models

def similar_project_names(project_name):
    # HOPE: One day, order this by relevance.
    return mysite.search.models.Project.objects.filter(
        name__icontains=project_name)
