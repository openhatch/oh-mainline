# -*- coding: utf-8 -*-
# Copyright 2007, 2008, 2009 by Benoît Chesneau <benoitc@e-engura.org>
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

import base64
import operator
import time
import urllib
try:
    from hashlib import md5 as _md5
except ImportError:
    import md5
    _md5 = md5.new
   
from django.db.models.query import Q
from django.conf import settings
from openid.association import Association as OIDAssociation
import openid.store.interface
import openid.store

from django_authopenid.models import Association, Nonce
from django_authopenid.utils import OpenID

class DjangoOpenIDStore(openid.store.interface.OpenIDStore):
    def __init__(self):
        self.max_nonce_age = 6 * 60 * 60 # Six hours
    
    def storeAssociation(self, server_url, association):
        assoc = Association(
            server_url = server_url,
            handle = association.handle,
            secret = base64.encodestring(association.secret),
            issued = association.issued,
            lifetime = association.lifetime,
            assoc_type = association.assoc_type
        )
        assoc.save()
    
    def getAssociation(self, server_url, handle=None):
        assocs = []
        if handle is not None:
            assocs = Association.objects.filter(
                server_url = server_url, handle = handle
            )
        else:
            assocs = Association.objects.filter(
                server_url = server_url
            )
        if not assocs:
            return None
        associations = []
        expired = []
        for assoc in assocs:
            association = OIDAssociation(
                assoc.handle, base64.decodestring(assoc.secret), assoc.issued,
                assoc.lifetime, assoc.assoc_type
            )
            if association.getExpiresIn() == 0:
                expired.append(assoc)
            else:
                associations.append((association.issued, association))
                
        for assoc in expired:
            assoc.delete()
        if not associations:
            return None
        associations.sort()
        return associations[-1][1]
    
    def removeAssociation(self, server_url, handle):
        assocs = list(Association.objects.filter(
            server_url = server_url, handle = handle
        ))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist

    def useNonce(self, server_url, timestamp, salt):
        if abs(timestamp - time.time()) > openid.store.nonce.SKEW:
            return False
        
        query = [
                Q(server_url__exact=server_url),
                Q(timestamp__exact=timestamp),
                Q(salt__exact=salt),
        ]
        try:
            ononce = Nonce.objects.get(reduce(operator.and_, query))
        except Nonce.DoesNotExist:
            ononce = Nonce(
                    server_url=server_url,
                    timestamp=timestamp,
                    salt=salt
            )
            ononce.save()
            return True

        return False
   
    def cleanupNonces(self, _now=None):
        if _now is None:
            _now = int(time.time())
        expired = Nonce.objects.filter(timestamp__lt=(_now - openid.store.nonce.SKEW))
        count = expired.count()
        if count:
            expired.delete()
        return count

    def cleanupAssociations(self):
        now = int(time.time())
        expired = Association.objects.extra(
            where=['issued + lifetime < %d' % now])
        count = expired.count()
        if count:
            expired.delete()
        return count

    def getAuthKey(self):
        # Use first AUTH_KEY_LEN characters of md5 hash of SECRET_KEY
        return _md5(settings.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]
    
    def isDumb(self):
        return False