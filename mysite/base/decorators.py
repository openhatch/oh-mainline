from decorator import decorator
from odict import odict
import re
import collections

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
