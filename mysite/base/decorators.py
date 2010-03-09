from decorator import decorator
from odict import odict
import re
import collections
import mysite.base.helpers
import simplejson
import django.core.cache
from functools import partial

from django.template.loader import render_to_string
from django.shortcuts import render_to_response

def as_view(request, template, data):
    data = {}
    data['the_user'] = request.user
    data['slug'] = func.__name__ # Account settings uses this.
    data.update(view_data)
    return render_to_response(template, data)

@decorator
def view(func, *args, **kw):
    """Decorator for views."""
    request, template, view_data = func(*args, **kw)
    data = {}
    data['the_user'] = request.user
    data['slug'] = func.__name__ # Account settings uses this.
    data.update(view_data)
    return render_to_response(template, data)

# vim: ai ts=3 sts=4 et sw=4 nu

@decorator
def unicodify_strings_when_inputted(func, *args, **kwargs):
    '''Decorator that makes sure every argument passed in that is
    a string-esque type is turned into a Unicode object. Does so
    by decoding UTF-8 byte strings into Unicode objects.'''
    args_as_list = list(args)
    # first, *args
    for i in range(len(args)):
        arg = args[i]
        if type(arg) is str:
            args_as_list[i] = unicode(arg, 'utf-8')

    # then, **kwargs
    for key in kwargs:
        arg = kwargs[key]
        if type(arg) is str:
            kwargs[key] = unicode(arg, 'utf-8')
    return func(*args_as_list, **kwargs)

def no_str_in_the_dict(d):
    if not d:
        return d
    
    for key in d:
        value = d[key]
        mysite.base.helpers.assert_or_pdb(type(key) != str)
        mysite.base.helpers.assert_or_pdb(type(value) != str)
    return d

def no_str_in_the_list(l):
    if not l:
        return l
    
    for elt in l:
        mysite.base.helpers.assert_or_pdb(type(l) != str)
    return l

def decorator_factory(decfac): # partial is functools.partial
    "decorator_factory(decfac) returns a one-parameter family of decorators"
    return partial(lambda df, param: decorator(partial(df, param)), decfac)

@decorator_factory 
def cache_method(cache_key_getter_name, func, *args, **kwargs):
    # Let's check to see whether we can avoid all this expensive DB jiggery after all
    self = args[0]
    cache_key = getattr(self, cache_key_getter_name)()
    cached_json = django.core.cache.cache.get(cache_key)

    if cached_json is None:
        value = func(*args, **kwargs)
        cached_json = simplejson.dumps({'value': value})
        import logging
        django.core.cache.cache.set(cache_key, cached_json, 864000)
        logging.info('cached output of func.__name__: %s' % cached_json)
    else:
        value = simplejson.loads(cached_json)['value']

    return value
