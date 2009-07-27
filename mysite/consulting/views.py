from django.http import HttpResponse, QueryDict, HttpResponseServerError
from django.shortcuts import render_to_response
from django.core import serializers
from mysite.search.models import Bug, Project
import simplejson
from django.db.models import Q

#Karen's crap is here       
        
def search(request):
    #return HttpResponse('Hello, world. You are at the consulting search page.')
    return render_to_response('consulting/search.html')
    
def list(request,query='list'):
    if query == 'list':
        return render_to_response('consulting/list.html')
    else:
        return render_to_response('consulting/list.html',{'query' : query})