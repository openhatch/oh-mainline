from django.http import HttpResponse
import simplejson
import urllib
import mysite.base.decorators
import django.conf
import os

def json_response(python_object):
    json = simplejson.dumps(python_object)
    return HttpResponse(json, mimetype="application/json")

class ObjectFromDict(object):
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key])

def assert_or_pdb(expression):
    if expression:
        pass
    else:
        if 'LOTSA_PDB' in os.environ:
            import pdb
            pdb.set_trace()
        else:
            raise ValueError, "eek"
