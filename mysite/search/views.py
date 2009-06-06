# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core import serializers
from mysite.search.models import Bug, Project
import simplejson

def fetch_bugs(request, language=False, format='html', start=0, end=10):
    # FIXME: Give bugs some date field

	bugs = Bug.objects.all()

	if language:
		bugs = bugs.filter(project__language=language)

	#if status:
	#	bugs = bugs.filter(project__status=status)
		
	bugs = bugs[start_at:end]

	if format == 'json':
		return bugs_to_json_response(bugs, \
				request.GET.get('jsoncallback', 'alert'))
	else:
		return render_to_response('search/search.html', \
				{'bunch_of_bugs': bugs, \
				'start_at': start_at, 'how_many': how_many})

def bugs_to_json_response(bunch_of_bugs, callback_function_name=''):
	json_serializer = serializers.get_serializer('python')()
	data = json_serializer.serialize(bunch_of_bugs)
	for elt in data:
		elt['fields']['project'] = \
				Project.objects.get(pk=int(elt['fields']['project'])).name
	jsonned = simplejson.dumps(data)
	return HttpResponse( callback_function_name + '(' + jsonned + ')' )

def index(request):
    return render_to_response('search/index.html')
    
