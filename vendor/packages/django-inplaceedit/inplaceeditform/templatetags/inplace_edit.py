# Copyright (c) 2010-2013 by Yaco Sistemas <goinnn@gmail.com> or <pmartin@yaco.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this programe.  If not, see <http://www.gnu.org/licenses/>.

import json

from django import template
from django.core.urlresolvers import reverse
from django.template import Library, Variable

from inplaceeditform import settings as inplace_settings
from inplaceeditform.commons import get_adaptor_class, get_static_url, get_admin_static_url
from inplaceeditform.tag_utils import RenderWithArgsAndKwargsNode, parse_args_kwargs

register = Library()


def inplace_js(context, activate_inplaceedit=True, toolbar=False):
    request = context['request']
    request.inplace_js_rendered = True
    return {
        'STATIC_URL': get_static_url(),
        'ADMIN_MEDIA_PREFIX': get_admin_static_url(),
        'activate_inplaceedit': activate_inplaceedit,
        'auto_save': json.dumps(inplace_settings.INPLACEEDIT_AUTO_SAVE),
        'event': inplace_settings.INPLACEEDIT_EVENT,
        'disable_click': json.dumps(inplace_settings.INPLACEEDIT_DISABLE_CLICK),
        'toolbar': toolbar,
        'enable_class': inplace_settings.INPLACE_ENABLE_CLASS,
        'success_text': inplace_settings.INPLACEEDIT_SUCCESS_TEXT,
        'unsaved_changes': inplace_settings.INPLACEEDIT_UNSAVED_TEXT,
        'inplace_get_field_url': inplace_settings.INPLACE_GET_FIELD_URL or reverse('inplace_get_field'),
        'inplace_save_url': inplace_settings.INPLACE_SAVE_URL or reverse('inplace_save'),
        'field_types': inplace_settings.INPLACE_FIELD_TYPES,
        'focus_when_editing': json.dumps(inplace_settings.INPLACE_FOCUS_WHEN_EDITING),
        'inplace_js_extra': getattr(request, 'inplace_js_extra', '')
    }
register.inclusion_tag("inplaceeditform/inplace_js.html", takes_context=True)(inplace_js)


def inplace_css(context, toolbar=False):
    request = context['request']
    request.inplace_css_rendered = True
    return {
        'STATIC_URL': get_static_url(),
        'ADMIN_MEDIA_PREFIX': get_admin_static_url(),
        'toolbar': toolbar,
        'inplace_js_extra': getattr(request, 'inplace_css_extra', '')
    }
register.inclusion_tag("inplaceeditform/inplace_css.html", takes_context=True)(inplace_css)


def inplace_static(context):
    return {
        'STATIC_URL': get_static_url(),
        'ADMIN_MEDIA_PREFIX': get_admin_static_url(),
        'toolbar': False,
        'request': context['request']
    }
register.inclusion_tag("inplaceeditform/inplace_static.html", takes_context=True)(inplace_static)


#to old django versions
def inplace_media(context):
    return inplace_static(context)
register.inclusion_tag("inplaceeditform/inplace_static.html", takes_context=True)(inplace_media)


def inplace_toolbar(context):
    return {
        'STATIC_URL': get_static_url(),
        'ADMIN_MEDIA_PREFIX': get_admin_static_url(),
        'toolbar': True,
        'request': context['request']
    }
register.inclusion_tag("inplaceeditform/inplace_static.html", takes_context=True)(inplace_toolbar)


class InplaceEditNode(RenderWithArgsAndKwargsNode):

    def prepare_context(self, args, kwargs, context):
        expression_to_show = args[0]
        tokens_to_show = expression_to_show.split('|')
        obj_field_name, filters_to_show = tokens_to_show[0], '|'.join(tokens_to_show[1:])
        obj_field_name_split = obj_field_name.split(".")
        obj_context = '.'.join(obj_field_name_split[:-1])
        field_name = obj_field_name_split[-1]
        obj = Variable(obj_context).resolve(context)
        adaptor = kwargs.get('adaptor', None)
        class_adaptor = get_adaptor_class(adaptor, obj, field_name)
        request = context.get('request')

        config = class_adaptor.get_config(request, **kwargs)

        adaptor_field = class_adaptor(request, obj, field_name,
                                      filters_to_show,
                                      config)

        context = {
            'adaptor_field': adaptor_field,
        }
        return context


@register.tag
def inplace_edit(parser, token):
    args, kwargs = parse_args_kwargs(parser, token)
    return InplaceEditNode(args, kwargs, 'inplaceeditform/inplace_edit.html')


@register.tag(name='eval')
def do_eval(parser, token):
    "Usage: {% eval %}1 + 1{% endeval %}"

    nodelist = parser.parse(('endeval',))

    class EvalNode(template.Node):
        def render(self, context):
            return template.Template(nodelist.render(context)).render(template.Context(context))
    parser.delete_first_token()
    return EvalNode()
