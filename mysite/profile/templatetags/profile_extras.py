from django import template

register = template.Library()

# See Django document on inclusion tags
# <http://docs.djangoproject.com/en/dev/howto/custom-template-tags/#inclusion-tags>
@register.inclusion_tag('profile/contributors.html')
def show_other_contributors(project, user, count, **args):
    return {'contributors': project.get_n_other_contributors_than(count, user.get_profile())}
