from decorator import decorator
from odict import odict
import re
import collections
import mysite.base.helpers

from django.template.loader import render_to_string
from django.shortcuts import render_to_response

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
