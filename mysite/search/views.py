# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core import serializers
from mysite.search.models import Bug

def query(request, query):
    # FIXME: Give bugs some date field
    bunch_of_bugs = Bug.objects.filter(
        project__language=query)
    return render_to_response('search/search.html', {'bunch_of_bugs': bunch_of_bugs})

def query_json(request, query):
    # FIXME: Give bugs some date field
    bunch_of_bugs = Bug.objects.filter(
        project__language=query)
    json_serializer = serializers.get_serializer('json')()
    return HttpResponse(json_serializer.serialize(bunch_of_bugs))

def index(request):
    return render_to_response('search/index.html')
    
