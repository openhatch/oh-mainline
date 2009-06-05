# Create your views here.
from django.shortcuts import render_to_response
from mysite.search.models import Bug

def index(request):
    # FIXME: Give bugs some date field
    bunch_of_bugs = Bug.objects.all().order_by('title')[:5]
    return render_to_response('search/index.html', {'bunch_of_bugs': bunch_of_bugs})
