from decorator import decorator
from odict import odict
import logging
from django.http import HttpResponse
import re
import collections
import mysite.base.helpers
import simplejson
import django.core.cache
import sha
from functools import partial

from django.template.loader import render_to_string
from mysite.base.helpers import render_response

def as_view(request, template, data, slug):
    if request.user.is_authenticated() or 'cookies_work' in request.session:
        # Great! Cookies work.
        pass
    else:
        request.session.set_test_cookie()
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
            request.session['cookies_work'] = True
    
    data['the_user'] = request.user
    data['slug'] = slug # Account settings uses this.
    return render_response(request, template, data)

@decorator
def view(func, *args, **kw):
    """Decorator for views."""
    request, template, view_data = func(*args, **kw)
    slug = func.__name__ # Used by account settings
    return as_view(request, template, view_data, slug)

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

@decorator
def cache_function_that_takes_request(func, *args, **kwargs):
    # Let's check to see whether we can avoid all this expensive DB jiggery after all
    request = args[0]

    # Calculate the cache key...
    key_data = []
    # 1. user string
    user_string = None
    if request.user.is_authenticated():
        user_string = request.user.username
    key_data.append(user_string)
    # 2. path_info
    key_data.append(request.path_info)
    # 3. query string
    key_data.append(request.META.get('QUERY_STRING', ''))

    key_string = 'cache_request_function_' + sha.sha(repr(key_data)).hexdigest()
    content = django.core.cache.cache.get(key_string, None)
    if content:
        logging.info("Cache hot for %s", repr(key_data))
        response = HttpResponse(content)
    else:
        logging.info("Cache cold for %s", repr(key_data))
        response = func(*args, **kwargs)
        content = response.content
        django.core.cache.cache.set(key_string, content, 360) # uh, six minutes, sure
    return response

@decorator_factory 
def cache_method(cache_key_getter_name, func, *args, **kwargs):
    # Let's check to see whether we can avoid all this expensive DB jiggery after all
    self = args[0]
    cache_key = getattr(self, cache_key_getter_name)(*args[1:], **kwargs)
    cached_json = django.core.cache.cache.get(cache_key)

    if cached_json is None:
        value = func(*args, **kwargs)
        cached_json = simplejson.dumps({'value': value})
        import logging
        django.core.cache.cache.set(cache_key, cached_json, 864000)
        logging.info('cached output of %s: %s' % (func.__name__, cached_json))
    else:
        value = simplejson.loads(cached_json)['value']

    return value

def cached_property(f):
    """returns a cached property that is calculated by function f"""
    def get(self):
        try:
            return self._property_cache[f]
        except AttributeError:
            self._property_cache = {}
            x = self._property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._property_cache[f] = f(self)
            return x
        
    return property(get)
