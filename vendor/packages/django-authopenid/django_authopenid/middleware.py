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

from django_authopenid.utils.mimeparse import best_match
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from django_authopenid.models import UserAssociation
from django_authopenid.views import xrdf

__all__ = ["OpenIDMiddleware"]

class OpenIDMiddleware(object):
    """
    Populate request.openid. This comes either from cookie or from
    session, depending on the presence of OPENID_USE_SESSIONS.
    """
    def process_request(self, request):
        request.openid = request.session.get('openid', None)
        request.openids = request.session.get('openids', [])
        
        rels = UserAssociation.objects.filter(user__id=request.user.id)
        request.associated_openids = [rel.openid_url for rel in rels]
    
    def process_response(self, request, response):
        if response.status_code != 200 or len(response.content) < 200:
            return response
        path = request.get_full_path()
        if path == "/" and request.META.has_key('HTTP_ACCEPT') and \
                best_match(['text/html', 'application/xrds+xml'], 
                    request.META['HTTP_ACCEPT']) == 'application/xrds+xml':
            response = xrdf(request)
        return response