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


def authopenid(request):
    """
    Returns context variables required by apps that use django-authopenid.
    """
    if hasattr(request, 'openid'):
        openid = request.openid
    else:
        openid = None
        
    if hasattr(request, 'openids'):
        openids = request.openids
    else:
        openids = []
        
    if hasattr(request, 'associated_openids'):
        associated_openids = request.associated_openids
    else:
        associated_openids = []
        
    return {
        "openid": openid,
        "openids": openids,
        "associated_openids": associated_openids,
        "signin_with_openid": (openid is not None),
        "has_openids": (len(associated_openids) > 0)
    }