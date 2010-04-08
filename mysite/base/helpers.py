import simplejson
import urllib
import os
import datetime
import dateutil.parser

from django.http import HttpResponse
import django.conf

import mysite.base.decorators

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

def string2naive_datetime(s):
    time_zoned = dateutil.parser.parse(s)
    if time_zoned.tzinfo:
        d_aware = time_zoned.astimezone(dateutil.tz.tzutc())
        d = d_aware.replace(tzinfo=None)
    else:
        d = time_zoned # best we can do
    return d

def instances_with_ids(model, manager, ids):
    ret = []
    for id_num in ids:
        try:
            ret.append(manager.get(id=id_num))
        except model.DoesNotExist:
            logging.info("Huh, it is gone.")
    return ret
    
