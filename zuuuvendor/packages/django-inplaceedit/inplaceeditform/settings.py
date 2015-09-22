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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


INPLACEEDIT_EDIT_EMPTY_VALUE = (getattr(settings, 'INPLACEEDIT_EDIT_EMPTY_VALUE', None) and
                                _(settings.INPLACEEDIT_EDIT_EMPTY_VALUE) or _('Doubleclick to edit'))
INPLACEEDIT_AUTO_SAVE = getattr(settings, 'INPLACEEDIT_AUTO_SAVE', False)
INPLACEEDIT_EVENT = getattr(settings, 'INPLACEEDIT_EVENT', 'dblclick')
INPLACEEDIT_DISABLE_CLICK = getattr(settings, 'INPLACEEDIT_DISABLE_CLICK', True)
INPLACEEDIT_EDIT_MESSAGE_TRANSLATION = (getattr(settings, 'INPLACEEDIT_EDIT_MESSAGE_TRANSLATION', None) and
                                        _(settings.INPLACEEDIT_EDIT_MESSAGE_TRANSLATION) or _('Write a translation'))
INPLACEEDIT_SUCCESS_TEXT = (getattr(settings, 'INPLACEEDIT_SUCCESS_TEXT', None) and
                            _(settings.INPLACEEDIT_SUCCESS_TEXT) or _('Successfully saved'))
INPLACEEDIT_UNSAVED_TEXT = (getattr(settings, 'INPLACEEDIT_UNSAVED_TEXT', None) and
                            _(settings.INPLACEEDIT_UNSAVED_TEXT) or _('You have unsaved changes!'))
INPLACE_ENABLE_CLASS = getattr(settings, 'INPLACE_ENABLE_CLASS', 'enable')
DEFAULT_INPLACE_EDIT_OPTIONS = getattr(settings, "DEFAULT_INPLACE_EDIT_OPTIONS", {})
DEFAULT_INPLACE_EDIT_OPTIONS_ONE_BY_ONE = getattr(settings, 'DEFAULT_INPLACE_EDIT_OPTIONS_ONE_BY_ONE', False)

ADAPTOR_INPLACEEDIT_EDIT = getattr(settings, 'ADAPTOR_INPLACEEDIT_EDIT', None)
ADAPTOR_INPLACEEDIT = getattr(settings, 'ADAPTOR_INPLACEEDIT', {})

INPLACE_GET_FIELD_URL = getattr(settings, 'INPLACE_GET_FIELD_URL', None)
INPLACE_SAVE_URL = getattr(settings, 'INPLACE_SAVE_URL', None)

INPLACE_FIELD_TYPES = getattr(settings, 'INPLACE_FIELD_TYPES', 'input, select, textarea')
INPLACE_FOCUS_WHEN_EDITING = getattr(settings, 'INPLACE_FOCUS_WHEN_EDITING', True)
