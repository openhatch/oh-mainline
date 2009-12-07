from django import template

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

def break_anywhere(value):
    new_value = ""
    for letter in value_escaped:
        new_value += letter + "!<wbr/>"
    return new_value

register.filter('gt', gt)
register.filter('lt', lt)
register.filter('gte', gte)
register.filter('lte', lte)
register.filter('length_gt', length_gt)
register.filter('length_lt', length_lt)
register.filter('length_gte', length_gte)
register.filter('length_lte', length_lte)
register.filter('break_anywhere', break_anywhere)
