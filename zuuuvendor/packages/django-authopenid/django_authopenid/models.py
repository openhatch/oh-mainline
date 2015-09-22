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

import os
import random
import sys
import time
try:
    from hashlib import md5 as _md5
except ImportError:
    import md5
    _md5 = md5.new


from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_authopenid.signals import oid_associate

__all__ = ['Nonce', 'Association', 'UserAssociation']

class Nonce(models.Model):
    """ openid nonce """
    server_url = models.CharField(max_length=255)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=40)
    
    def __unicode__(self):
        return u"Nonce: %s" % self.id

class Association(models.Model):
    """ association openid url and lifetime """
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255) # Stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)
    
    def __unicode__(self):
        return u"Association: %s, %s" % (self.server_url, self.handle)

class UserAssociation(models.Model):
    """ 
    model to manage association between openid and user 
    """
    openid_url = models.CharField(primary_key=True, blank=False,
                            max_length=255, verbose_name=_('OpenID URL'))
    user = models.ForeignKey(User, verbose_name=_('User'))
    
    def __unicode__(self):
        return "Openid %s with user %s" % (self.openid_url, self.user)
        
    def save(self, send_email=True):
        super(UserAssociation, self).save()
        if send_email:
            from django.core.mail import send_mail
            current_site = Site.objects.get_current()
            subject = render_to_string('authopenid/associate_email_subject.txt',
                                       { 'site': current_site,
                                         'user': self.user})
            message = render_to_string('authopenid/associate_email.txt',
                                       { 'site': current_site,
                                         'user': self.user,
                                         'openid': self.openid_url
                                        })

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, 
                    [self.user.email], fail_silently=True)
        oid_associate.send(sender=self, user=self.user, openid=self.openid_url)
        

    class Meta:
        verbose_name = _('user association')
        verbose_name_plural = _('user associations')
