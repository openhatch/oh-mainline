from django import template
import re
from django.utils.html import escape

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

# From <http://code.djangoproject.com/wiki/BasicComparisonFilters>
def gt(value, arg):
    "Returns a boolean of whether the value is greater than the argument"
    return value > int(arg)

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

def break_long_words(value):
    assert type(value) == unicode
    re_too_many_letters_in_a_row = re.compile(r'([\w]{8}|[\_^/])', re.UNICODE)

    # if the word is really long, insert a <wbr> occasionally.
    return "<wbr>".join(re_too_many_letters_in_a_row.split(value))

register.filter('gt', gt)
register.filter('lt', lt)
register.filter('gte', gte)
register.filter('lte', lte)
register.filter('length_gt', length_gt)
register.filter('length_lt', length_lt)
register.filter('length_gte', length_gte)
register.filter('length_lte', length_lte)
register.filter('break_long_words', break_long_words)
