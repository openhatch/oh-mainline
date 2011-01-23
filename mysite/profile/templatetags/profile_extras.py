# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2010 Mister Deployed
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

from django import template
import re
from django.utils.html import escape
from urlparse import urlparse
import logging

register = template.Library()

# See Django document on inclusion tags
# <http://docs.djangoproject.com/en/dev/howto/custom-template-tags/#inclusion-tags>
@register.inclusion_tag('profile/contributors.html')
def show_other_contributors(project, user, count, **args):
    return {
            'project': project,
            'user': user,
            'contributors': project.get_n_other_contributors_than(count, user.get_profile()),
            }

def person_tag_descriptions_for_tag_text(person, tag_text):
    "Returns a boolean of whether the value is greater than the argument"
    return person.get_tag_descriptions_for_keyword(tag_text)

# From <http://code.djangoproject.com/wiki/BasicComparisonFilters>
def gt(value, arg):
    "Returns a boolean of whether the value is greater than the argument"
    return value > int(arg)

@register.filter
def equals(value, arg):
    return value == arg

def lt(value, arg):
    "Returns a boolean of whether the value is less than the argument"
    return value < int(arg)

def gte(value, arg):
    "Returns a boolean of whether the value is greater than or equal to the argument"
    return value >= int(arg)

def lte(value, arg):
    "Returns a boolean of whether the value is less than or equal to the argument"
    return value <= int(arg)

def length_gt(value, arg):
    "Returns a boolean of whether the value's length is greater than the argument"
    return len(value) > int(arg)

def length_lt(value, arg):
    "Returns a boolean of whether the value's length is less than the argument"
    return len(value) < int(arg)

def length_gte(value, arg):
    "Returns a boolean of whether the value's length is greater than or equal to the argument"
    return len(value) >= int(arg)

def length_lte(value, arg):
    "Returns a boolean of whether the value's length is less than or equal to the argument"
    return len(value) <= int(arg)

def break_long_words(value, max_word_length=8):
    # if the word is really long, insert a <wbr> occasionally.

    # We really want "value" to be Unicode. Sometimes it is, and sometimes it isn't. So...
    if type(value) == str:
        # Django 2.6 sometimes gives us the empty string as '', not u''.
        # Are there other cases where we do get a byte string, not a Unicode string?
        if value != '':
            logging.warn("Wanted %r to be unicode. Instead it's %s. Moving on with life." % (value, type(value)))

        # In all cases, I guess we should just buckle up and move on with life.
        value = unicode(value, 'utf-8')

    re_capitalized_word = re.compile(r'([A-Z][a-z][a-z]+)', re.UNICODE)  
    words = re_capitalized_word.split(value)
    re_too_many_letters_in_a_row = re.compile(r'([\w]{%d}|[.\_^/])' % max_word_length, re.UNICODE)
    broken_words = []
    for word in words:
        if word:
            broken_words += re_too_many_letters_in_a_row.split(word)
    broken_words = filter(lambda x: x, broken_words)
    return "<wbr />".join(broken_words)

@register.filter
def prepend_http_if_necessary(value):
    """If someone makes "www.example.org" their homepage, then we need to prepend "http://" so it doesn't link to https://openhatch.org/people/username/www.example.org. This template filter prepends that."""
    parsed = urlparse(value)
    if not parsed.scheme:
        return "http://" + parsed.geturl()
    return value

@register.filter
def is_logged_in(user, request):
    return (user == request.user)

register.filter('gt', gt)
register.filter('lt', lt)
register.filter('gte', gte)
register.filter('lte', lte)
register.filter('length_gt', length_gt)
register.filter('length_lt', length_lt)
register.filter('length_gte', length_gte)
register.filter('length_lte', length_lte)
register.filter('break_long_words', break_long_words)
register.filter('person_tag_descriptions_for_tag_text', person_tag_descriptions_for_tag_text)
