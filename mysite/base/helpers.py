from django.http import HttpResponse
import simplejson
import urllib
import mysite.base.decorators

def json_response(python_object):
    json = simplejson.dumps(python_object)
    return HttpResponse(json, mimetype="application/json")

class ObjectFromDict(object):
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key])

