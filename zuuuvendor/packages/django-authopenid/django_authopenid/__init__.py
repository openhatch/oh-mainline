# -*- coding: utf-8 -*-
# Copyright 2007, 2008,2009 by Benoît Chesneau <benoitc@e-engura.org>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Django authentification application to *with openid using django auth contrib/.

This application allow a user to connect to you website with :
 * legacy account : username/password
 * openid url
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    from django.utils.importlib import import_module
except ImportError:
    # version < 1.1
    from django_authopenid.utils.importlib import import_module

__version__ = "1.0.1"

# get openidstore to use.
if not hasattr(settings, 'OPENID_STORE') or not settings.OPENID_STORE:
    settings.OPENID_STORE = 'django_authopenid.openid_store.DjangoOpenIDStore'
    
def load_store(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing openid store %s: "%s"' % (module, e))
    except ValueError, e:
        raise ImproperlyConfigured('Error importing openid store. Is OPENID_STORE '
        'a correctly defined list or tuple?')        
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" '
        'openid store' % (module, attr))
    return cls
    
DjangoOpenIDStore = load_store(settings.OPENID_STORE)