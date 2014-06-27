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
import sys

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.forms import ValidationError
from django.shortcuts import get_object_or_404

from inplaceeditform.commons import (get_dict_from_obj, apply_filters,
                                     get_adaptor_class)

MIMETYPE_RESPONSE = 'text'

if sys.version_info[0] >= 2:
    unicode = str


def save_ajax(request):
    if not request.method == 'POST':
        return _get_http_response({'errors': 'It is not a POST request'})
    adaptor = _get_adaptor(request, 'POST')
    if not adaptor:
        return _get_http_response({'errors': 'Params insufficient'})
    if not adaptor.can_edit():
        return _get_http_response({'errors': 'You can not edit this content'})
    value = adaptor.loads_to_post(request)
    new_data = get_dict_from_obj(adaptor.obj)
    form_class = adaptor.get_form_class()
    field_name = adaptor.field_name
    form = form_class(data=new_data, instance=adaptor.obj)
    try:
        value_edit = adaptor.get_value_editor(value)
        value_edit_with_filter = apply_filters(value_edit, adaptor.filters_to_edit)
        new_data[field_name] = value_edit_with_filter
        if form.is_valid():
            adaptor.save(value_edit_with_filter)
            return _get_http_response({'errors': False,
                                       'value': adaptor.render_value_edit()})
        messages = []  # The error is for another field that you are editing
        for field_name_error, errors_field in form.errors.items():
            for error in errors_field:
                messages.append("%s: %s" % (field_name_error, unicode(error)))
        message_i18n = ','.join(messages)
        return _get_http_response({'errors': message_i18n})
    except ValidationError as error:  # The error is for a field that you are editing
        message_i18n = ', '.join([u"%s" % m for m in error.messages])
        return _get_http_response({'errors': message_i18n})


def get_field(request):
    if not request.method == 'GET':
        return _get_http_response({'errors': 'It is not a GET request'})
    adaptor = _get_adaptor(request, 'GET')
    if not adaptor:
        return _get_http_response({'errors': 'Params insufficient'})
    if not adaptor.can_edit():
        return _get_http_response({'errors': 'You can not edit this content'})
    field_render = adaptor.render_field()
    field_media_render = adaptor.render_media_field()
    return _get_http_response({'field_render': field_render,
                               'field_media_render': field_media_render})


def _get_adaptor(request, method='GET'):
    request_params = getattr(request, method)
    field_name = request_params.get('field_name', None)
    obj_id = request_params.get('obj_id', None)

    app_label = request_params.get('app_label', None)
    module_name = request_params.get('module_name', None)

    if not field_name or not obj_id or not app_label and module_name:
        return None

    contenttype = ContentType.objects.get(app_label=app_label,
                                          model=module_name)

    model_class = contenttype.model_class()
    obj = get_object_or_404(model_class,
                            pk=obj_id)
    adaptor = request_params.get('adaptor', None)
    class_adaptor = get_adaptor_class(adaptor, obj, field_name)

    filters_to_show = request_params.get('filters_to_show', None)

    kwargs = _convert_params_in_config(request_params, ('field_name',
                                                        'obj_id',
                                                        'app_label',
                                                        'module_name',
                                                        'filters_to_show',
                                                        'adaptor'))
    config = class_adaptor.get_config(request, **kwargs)
    adaptor_field = class_adaptor(request, obj, field_name,
                                  filters_to_show,
                                  config)
    return adaptor_field


def _convert_params_in_config(request_params, exclude_params=None):
    exclude_params = exclude_params or []
    config = {}
    options_widget = {}
    for key, value in request_params.items():
        if key not in exclude_params:
            if key.startswith('__widget_'):
                key = key.replace('__widget_', '')
                options_widget[key] = value
            else:
                config[str(key)] = value
    config['widget_options'] = options_widget
    return config


def _get_http_response(context, mimetype=MIMETYPE_RESPONSE):
    return HttpResponse(json.dumps(context),
                        MIMETYPE_RESPONSE)
