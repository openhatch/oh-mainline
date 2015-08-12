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
import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.translation import ugettext as _
from django.conf import settings
# needed for some linux distributions like debian
try:
    from openid.yadis import xri
except ImportError:
    from yadis import xri
    
from django_authopenid.models import UserAssociation

    
class OpenidSigninForm(forms.Form):
    """ signin form """
    openid_url = forms.CharField(max_length=255, 
            widget=forms.widgets.TextInput(attrs={'class': 'required openid'}))
            
    def clean_openid_url(self):
        """ test if openid is accepted """
        if 'openid_url' in self.cleaned_data:
            openid_url = self.cleaned_data['openid_url']
            if xri.identifierScheme(openid_url) == 'XRI' and getattr(
                settings, 'OPENID_DISALLOW_INAMES', False
                ):
                raise forms.ValidationError(_('i-names are not supported'))
            return self.cleaned_data['openid_url']

attrs_dict = { 'class': 'required login' }
username_re = re.compile(r'^\w+$')

class OpenidRegisterForm(forms.Form):
    """ openid signin form """
    username = forms.CharField(max_length=30, 
            widget=forms.widgets.TextInput(attrs=attrs_dict))
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, 
        maxlength=200)), label=u'Email address')
        
    def __init__(self, *args, **kwargs):
        super(OpenidRegisterForm, self).__init__(*args, **kwargs)
        self.user = None
    
    def clean_username(self):
        """ test if username is valid and exist in database """
        if 'username' in self.cleaned_data:
            if not username_re.search(self.cleaned_data['username']):
                raise forms.ValidationError(_("Usernames can only contain \
                    letters, numbers and underscores"))
            try:
                user = User.objects.get(
                        username__exact = self.cleaned_data['username']
                )
            except User.DoesNotExist:
                return self.cleaned_data['username']
            except User.MultipleObjectsReturned:
                raise forms.ValidationError(u'There is already more than one \
                    account registered with that username. Please try \
                    another.')
            self.user = user
            raise forms.ValidationError(_("This username is already \
                taken. Please choose another."))
            
    def clean_email(self):
        """For security reason one unique email in database"""
        if 'email' in self.cleaned_data:
            try:
                user = User.objects.get(email = self.cleaned_data['email'])
            except User.DoesNotExist:
                return self.cleaned_data['email']
            except User.MultipleObjectsReturned:
                raise forms.ValidationError(u'There is already more than one \
                    account registered with that e-mail address. Please try \
                    another.')
            raise forms.ValidationError(_("This email is already \
                registered in our database. Please choose another."))
                
                
class AssociateOpenID(forms.Form):
    """ new openid association form """
    openid_url = forms.CharField(max_length=255, 
            widget=forms.widgets.TextInput(attrs={'class': 'required openid'}))

    def __init__(self, user, *args, **kwargs):
        super(AssociateOpenID, self).__init__(*args, **kwargs)
        self.user = user
            
    def clean_openid_url(self):
        """ test if openid is accepted """
        if 'openid_url' in self.cleaned_data:
            openid_url = self.cleaned_data['openid_url']
            if xri.identifierScheme(openid_url) == 'XRI' and getattr(
                settings, 'OPENID_DISALLOW_INAMES', False
                ):
                raise forms.ValidationError(_('i-names are not supported'))
                
            try:
                rel = UserAssociation.objects.get(openid_url__exact=openid_url)
            except UserAssociation.DoesNotExist:
                return self.cleaned_data['openid_url']
            
            if rel.user != self.user:
                raise forms.ValidationError(_("This openid is already \
                    registered in our database by another account. Please choose another."))
                    
            raise forms.ValidationError(_("You already associated this openid to your account."))
            
class OpenidDissociateForm(OpenidSigninForm):
    """ form used to dissociate an openid. """
    openid_url = forms.CharField(max_length=255, widget=forms.widgets.HiddenInput())