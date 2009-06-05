# Create your views here.
from django.shortcuts import render_to_response
from mysite.search.models import Bug

def query(request, query):
    # FIXME: Give bugs some date field
    bunch_of_bugs = Bug.objects.filter(
        project__language=query)
    return render_to_response('search/search.html', {'bunch_of_bugs': bunch_of_bugs})

def index(request):
    return render_to_response('search/index.html')
    
