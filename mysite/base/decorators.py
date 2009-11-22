from decorator import decorator
from odict import odict
import re
import collections

from django.template.loader import render_to_string
from django.shortcuts import render_to_response

from mysite.profile.models import ProjectExp, Link_Person_Tag, Link_Project_Tag, Link_ProjectExp_Tag

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
