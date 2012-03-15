# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from decorator import decorator
from odict import odict
import logging
from django.http import HttpResponse
import re
import collections
import mysite.base.helpers
from django.utils import simplejson
import django.core.cache
import hashlib
from functools import partial

from django.template.loader import render_to_string
import django.db.models.query
from mysite.base.helpers import render_response
from django.core.urlresolvers import reverse, resolve
import django.contrib.auth.decorators

def as_view(request, template, data, slug, just_modify_data=False):
    ### add settings to the request so that the template
    ### can adjust what it displays depending on settings.
    data['settings'] = django.conf.settings
    if request.user.is_authenticated() or 'cookies_work' in request.session:
        # Great! Cookies work.
        pass
    else:
        request.session.set_test_cookie()
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
            request.session['cookies_work'] = True


    # Where should the user be sent if she clicks 'logout'?
    # Depends on whether this is a login-requiring page.
    try:
        view_function, _, _ = resolve(request.path)
        is_login_required = isinstance(view_function,
                django.contrib.auth.decorators._CheckLogin)
        if is_login_required:
            data['go_here_after_logging_in_or_out'] = '/'
        else:
            data['go_here_after_logging_in_or_out'] = request.get_full_path()
    except:
        data['go_here_after_logging_in_or_out'] = '/'

    data['slug'] = slug # Account settings uses this.
    if just_modify_data:
        return data
    else:
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

    key_string = 'cache_request_function_' + hashlib.sha1(repr(key_data)).hexdigest()
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
    # The point of cache_method is to decorate expensive methods in classes
    # with a flexible way to store their input/output mappings in the cache.

    # The object implicitly passed to this function has an instance method we
    # can use to calculate the cache key. That instance method's name is stored
    # in cache_key_getter_name. Let's get the cache key. Notice that the cache
    # key also varies based on what arguments get passed to the decorated function.
    self = args[0]
    cache_key = getattr(self, cache_key_getter_name)(*args[1:], **kwargs)

    # We cache objects as JSON. (We could have used Pickle, but we, er, Asheesh
    # prefers JSON.)
    cached_json = django.core.cache.cache.get(cache_key)

    if cached_json is None:
        # If there's nothing in the cache, well, shoot, we have to actually do
        # the expensive work. Let's run it.
        value = func(*args, **kwargs)

        # Then cache the input/output mapping, in a few steps:

        # First transform certain objects into a cachable format.
        if type(value) == django.db.models.query.ValuesListQuerySet:
            value = list(value)
        cached_json = simplejson.dumps({'value': value})

        # Then cache the input/output mapping.
        django.core.cache.cache.set(cache_key, cached_json, 864000)

        logging.debug('cached output of %s: %s' % (func.__name__, cached_json))
    else:
        # Sweet, no need to run the expensive method. Just use the cached output.
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
