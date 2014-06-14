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

from django import template
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.conf import settings

from inplaceeditform import settings as inplace_settings
from inplaceeditform.adaptors import ADAPTOR_INPLACEEDIT as DEFAULT_ADAPTOR_INPLACEEDIT

has_transmeta = False
DEFAULT_VALUE = ''
try:
    import transmeta
    has_transmeta = True
except ImportError:
    pass


def get_dict_from_obj(obj):
    '''
    Edit to get the dict even when the object is a GenericRelatedObjectManager.
    Added the try except.
    '''
    obj_dict = obj.__dict__
    obj_dict_result = obj_dict.copy()
    for key, value in obj_dict.items():
        if key.endswith('_id'):
            key2 = key.replace('_id', '')
            try:
                field, model, direct, m2m = obj._meta.get_field_by_name(key2)
                if isinstance(field, ForeignKey):
                    obj_dict_result[key2] = obj_dict_result[key]
                    del obj_dict_result[key]
            except FieldDoesNotExist:
                pass
    manytomany_list = obj._meta.many_to_many
    for manytomany in manytomany_list:
        ids = [obj_rel.id for obj_rel in manytomany.value_from_object(obj).select_related()]
        if ids:
            obj_dict_result[manytomany.name] = ids
    return obj_dict_result


def apply_filters(value, filters, load_tags=None):
    if filters:
        filters_str = '|%s' % '|'.join(filters)
        load_tags = load_tags or []
        if load_tags:
            load_tags_str = "{%% load %s %%}" % ' '.join(load_tags)
        else:
            load_tags_str = ""
        value = template.Template("""%s{{ value%s }}""" % (load_tags_str, filters_str)).render(template.Context({'value': value}))
    return value


def import_module(name, package=None):
    try:
        from django.utils.importlib import import_module
        return import_module(name, package)
    except ImportError:
        path = [m for m in name.split('.')]
        return __import__(name, {}, {}, path[-1])


def get_adaptor_class(adaptor=None, obj=None, field_name=None):
    if not adaptor:
        try:
            field = obj._meta.get_field_by_name(field_name)[0]
        except FieldDoesNotExist:
            if has_transmeta:
                field = obj._meta.get_field_by_name(transmeta.get_real_fieldname(field_name))[0]
        if isinstance(field, models.URLField):
            adaptor = 'url'
        elif isinstance(field, models.EmailField):
            adaptor = 'email'
        elif isinstance(field, models.CharField):
            adaptor = 'text'
            if getattr(field, 'choices', None):
                adaptor = 'choices'
        elif isinstance(field, models.TextField):
            adaptor = 'textarea'
        elif isinstance(field, models.NullBooleanField):
            adaptor = 'nullboolean'
        elif isinstance(field, models.BooleanField):
            adaptor = 'boolean'
        elif isinstance(field, models.DateTimeField):
            adaptor = 'datetime'
        elif isinstance(field, models.DateField):
            adaptor = 'date'
        elif isinstance(field, models.TimeField):
            adaptor = 'time'
        elif isinstance(field, models.IntegerField):
            adaptor = 'integer'
        elif isinstance(field, models.FloatField):
            adaptor = 'float'
        elif isinstance(field, models.DecimalField):
            adaptor = 'decimal'
        elif isinstance(field, ForeignKey):
            adaptor = 'fk'
        elif isinstance(field, ManyToManyField):
            adaptor = 'm2mcomma'
        elif isinstance(field, models.ImageField):
            adaptor = 'image'
        elif isinstance(field, models.FileField):
            adaptor = 'file'
    from inplaceeditform.fields import BaseAdaptorField
    path_adaptor = adaptor and (inplace_settings.ADAPTOR_INPLACEEDIT.get(adaptor, None) or
                                DEFAULT_ADAPTOR_INPLACEEDIT.get(adaptor, None))
    if not path_adaptor and adaptor:
        return get_adaptor_class(obj=obj, field_name=field_name)
    elif not path_adaptor:
        return BaseAdaptorField
    path_module, class_adaptor = ('.'.join(path_adaptor.split('.')[:-1]), path_adaptor.split('.')[-1])
    return getattr(import_module(path_module), class_adaptor)


def get_static_url(subfix='inplaceeditform'):
    static_url = getattr(settings, 'STATIC_URL', None)
    if static_url:
        return static_url
    else:  # To old django versions
        return '%s%s/' % (getattr(settings, 'MEDIA_URL', None), subfix)


def get_admin_static_url():
    """
    Return the ADMIN_MEDIA_PREFIX if it is in the settings.py else get
    the static url from the previous function and add /admin/.
    """
    return getattr(settings, 'ADMIN_MEDIA_PREFIX', get_static_url() + "admin/")
