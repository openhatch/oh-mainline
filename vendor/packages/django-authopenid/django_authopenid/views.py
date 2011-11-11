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
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import *
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response as render
from django.template import RequestContext, loader, Context


from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

from django.utils.http import urlquote_plus
from django.core.mail import send_mail

from openid.consumer.consumer import Consumer, \
    SUCCESS, CANCEL, FAILURE, SETUP_NEEDED
from openid.consumer.discover import DiscoveryFailure
from openid.extensions import sreg, ax
# needed for some linux distributions like debian
try:
    from openid.yadis import xri
except ImportError:
    from yadis import xri

import re
import urllib

from django_authopenid import DjangoOpenIDStore
from django_authopenid.forms import *
from django_authopenid.models import UserAssociation
from django_authopenid.signals import oid_register
from django_authopenid.utils import *

def _build_context(request, extra_context=None):
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return context    
    
def ask_openid(request, openid_url, redirect_to, on_failure=None):
    """ basic function to ask openid and return response """
    on_failure = on_failure or signin_failure
    sreg_req = None
    ax_req = None
    
    trust_root = getattr(
        settings, 'OPENID_TRUST_ROOT', get_url_host(request) + '/'
    )
    if xri.identifierScheme(openid_url) == 'XRI' and getattr(
            settings, 'OPENID_DISALLOW_INAMES', False
    ):
        msg = _("i-names are not supported")
        return on_failure(request, msg)
    consumer = Consumer(request.session, DjangoOpenIDStore())
    try:
        auth_request = consumer.begin(openid_url)
    except DiscoveryFailure:
        msg = _("The OpenID %s was invalid") % openid_url
        return on_failure(request, msg)
    
    # get capabilities
    use_ax, use_sreg = discover_extensions(openid_url)
    if use_sreg:
        # set sreg extension
        # we always ask for nickname and email
        sreg_attrs = getattr(settings, 'OPENID_SREG', {})
        sreg_attrs.update({ "optional": ['nickname', 'email'] })
        sreg_req = sreg.SRegRequest(**sreg_attrs)
    if use_ax:
        # set ax extension
        # we always ask for nickname and email
        ax_req = ax.FetchRequest()
        ax_req.add(ax.AttrInfo('http://schema.openid.net/contact/email', 
                                alias='email', required=True))
        ax_req.add(ax.AttrInfo('http://schema.openid.net/namePerson/friendly', 
                                alias='nickname', required=True))
                      
        # add custom ax attrs          
        ax_attrs = getattr(settings, 'OPENID_AX', [])
        for attr in ax_attrs:
            if len(attr) == 2:
                ax_req.add(ax.AttrInfo(attr[0], required=alias[1]))
            else:
                ax_req.add(ax.AttrInfo(attr[0]))
       
    if sreg_req is not None:
        auth_request.addExtension(sreg_req)
    if ax_req is not None:
        auth_request.addExtension(ax_req)
    
    redirect_url = auth_request.redirectURL(trust_root, redirect_to)
    return HttpResponseRedirect(redirect_url)

def complete(request, on_success=None, on_failure=None, return_to=None, 
    **kwargs):
    """ complete openid signin """
    on_success = on_success or default_on_success
    on_failure = on_failure or default_on_failure
    
    consumer = Consumer(request.session, DjangoOpenIDStore())
    # make sure params are encoded in utf8
    params = dict((k,smart_unicode(v)) for k, v in request.GET.items())
    openid_response = consumer.complete(params, return_to)
            
    if openid_response.status == SUCCESS:
        return on_success(request, openid_response.identity_url,
                openid_response, **kwargs)
    elif openid_response.status == CANCEL:
        return on_failure(request, 'The request was canceled', **kwargs)
    elif openid_response.status == FAILURE:
        return on_failure(request, openid_response.message, **kwargs)
    elif openid_response.status == SETUP_NEEDED:
        return on_failure(request, 'Setup needed', **kwargs)
    else:
        assert False, "Bad openid status: %s" % openid_response.status

def default_on_success(request, identity_url, openid_response, **kwargs):
    """ default action on openid signin success """
    request.session['openid'] = from_openid_response(openid_response)
    return HttpResponseRedirect(clean_next(request.GET.get('next')))

def default_on_failure(request, message, **kwargs):
    """ default failure action on signin """
    return render('openid_failure.html', {
        'message': message
    })


def not_authenticated(func):
    """ decorator that redirect user to next page if
    he is already logged."""
    def decorated(request, *args, **kwargs):
        if request.user.is_authenticated():
            next = request.GET.get("next", "/")
            return HttpResponseRedirect(next)
        return func(request, *args, **kwargs)
    return decorated

def signin_success(request, identity_url, openid_response,
        redirect_field_name=REDIRECT_FIELD_NAME, **kwargs):
    """
    openid signin success.

    If the openid is already registered, the user is redirected to 
    url set par next or in settings with OPENID_REDIRECT_NEXT variable.
    If none of these urls are set user is redirectd to /.

    if openid isn't registered user is redirected to register page.
    """

    openid_ = from_openid_response(openid_response)
    
    openids = request.session.get('openids', [])
    openids.append(openid_)
    request.session['openids'] = openids
    request.session['openid'] = openid_
    try:
        rel = UserAssociation.objects.get(openid_url__exact = str(openid_))
    except:
        # try to register this new user
        redirect_to = request.REQUEST.get(redirect_field_name, '')
        if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL
        return HttpResponseRedirect(
            "%s?%s" % (reverse('user_register'),
            urllib.urlencode({ redirect_field_name: redirect_to }))
        )
    user_ = rel.user
    if user_.is_active:
        user_.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user_)
        
    redirect_to = request.GET.get(redirect_field_name, '')
    if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
        redirect_to = settings.LOGIN_REDIRECT_URL
    return HttpResponseRedirect(redirect_to)
    
def signin_failure(request, message, template_name='authopenid/signin.html',
        redirect_field_name=REDIRECT_FIELD_NAME, openid_form=OpenidSigninForm, 
        auth_form=AuthenticationForm, extra_context=None, **kwargs):
    """
    falure with openid signin. Go back to signin page.
    
    :attr request: request object
    :attr template_name: string, name of template to use, default is 
    'authopenid/signin.html'
    :attr redirect_field_name: string, field name used for redirect. by default
    'next'
    :attr openid_form: form use for openid signin, by default `OpenidSigninForm`
    :attr auth_form: form object used for legacy authentification. 
    by default AuthentificationForm form auser auth contrib.
    :attr extra_context: A dictionary of variables to add to the template 
    context. Any callable object in this dictionary will be called to produce 
    the end result which appears in the context.
    """
    return render(template_name, {
        'msg': message,
        'form1': openid_form(),
        'form2': auth_form(),
        redirect_field_name: request.REQUEST.get(redirect_field_name, '')
    }, context_instance=_build_context(request, extra_context))


@not_authenticated
def signin(request, template_name='authopenid/signin.html', 
        redirect_field_name=REDIRECT_FIELD_NAME, openid_form=OpenidSigninForm,
        auth_form=AuthenticationForm, on_failure=None, extra_context=None):
    """Signin page. It manage the legacy authentification (user/password)  
    and authentification with openid.

    :attr request: request object
    :attr template_name: string, name of template to use
    :attr redirect_field_name: string, field name used for redirect. by 
    default 'next'
    :attr openid_form: form use for openid signin, by default 
    `OpenidSigninForm`
    :attr auth_form: form object used for legacy authentification. 
    By default AuthentificationForm form auser auth contrib.
    :attr extra_context: A dictionary of variables to add to the 
    template context. Any callable object in this dictionary will 
    be called to produce the end result which appears in the context.
    """
    if on_failure is None:
        on_failure = signin_failure
        
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    form1 = openid_form()
    form2 = auth_form()
    if request.POST:
        if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL     
        if 'openid_url' in request.POST.keys():
            form1 = openid_form(data=request.POST)
            if form1.is_valid():
                redirect_url = "%s%s?%s" % (
                        get_url_host(request),
                        reverse('user_complete_signin'), 
                        urllib.urlencode({ redirect_field_name: redirect_to })
                )
                return ask_openid(request, 
                        form1.cleaned_data['openid_url'], 
                        redirect_url, 
                        on_failure=on_failure)
        else:
            # perform normal django authentification
            form2 = auth_form(data=request.POST)
            if form2.is_valid():
                login(request, form2.get_user())
                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()
                return HttpResponseRedirect(redirect_to)
    return render(template_name, {
        'form1': form1,
        'form2': form2,
        redirect_field_name: redirect_to,
        'msg':  request.GET.get('msg','')
    }, context_instance=_build_context(request, extra_context=extra_context))

def complete_signin(request, redirect_field_name=REDIRECT_FIELD_NAME,  
        openid_form=OpenidSigninForm, auth_form=AuthenticationForm, 
        on_success=signin_success, on_failure=signin_failure, 
        extra_context=None):
    """
    in case of complete signin with openid 

    :attr request: request object
    :attr openid_form: form use for openid signin, by default 
    `OpenidSigninForm`
    :attr auth_form: form object used for legacy authentification. 
    by default AuthentificationForm form auser auth contrib.
    :attr on_success: callbale, function used when openid auth success
    :attr on_failure: callable, function used when openid auth failed.
    :attr extra_context: A dictionary of variables to add to the template 
    context.
    Any callable object in this dictionary will be called to produce the
    end result which appears in the context.  
    """
    return complete(request, on_success, on_failure,
            get_url_host(request) + reverse('user_complete_signin'),
            redirect_field_name=redirect_field_name, openid_form=openid_form, 
            auth_form=auth_form, extra_context=extra_context)

def is_association_exist(openid_url):
    """ test if an openid is already in database """
    is_exist = True
    try:
        uassoc = UserAssociation.objects.get(openid_url__exact = openid_url)
    except:
        is_exist = False
    return is_exist
    
def register_account(form, _openid):
    """ create an account """
    user = User.objects.create_user(form.cleaned_data['username'], 
                            form.cleaned_data['email'])
    user.backend = "django.contrib.auth.backends.ModelBackend"
    oid_register.send(sender=user, openid=_openid)
    return user

@not_authenticated
def register(request, template_name='authopenid/complete.html', 
            redirect_field_name=REDIRECT_FIELD_NAME, 
            register_form=OpenidRegisterForm, auth_form=AuthenticationForm, 
            register_account=register_account, send_email=True, 
            extra_context=None):
    """
    register an openid.

    If user is already a member he can associate its openid with 
    its account.

    A new account could also be created and automaticaly associated
    to the openid.

    :attr request: request object
    :attr template_name: string, name of template to use, 
    'authopenid/complete.html' by default
    :attr redirect_field_name: string, field name used for redirect. by default 
    'next'
    :attr register_form: form use to create a new account. By default 
    `OpenidRegisterForm`
    :attr auth_form: form object used for legacy authentification. 
    by default `OpenidVerifyForm` form auser auth contrib.
    :attr register_account: callback used to create a new account from openid. 
    It take the register_form as param.
    :attr send_email: boolean, by default True. If True, an email will be sent 
    to the user.
    :attr extra_context: A dictionary of variables to add to the template 
    context. Any callable object in this dictionary will be called to produce 
    the end result which appears in the context.
    """
    is_redirect = False
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    openid_ = request.session.get('openid', None)
    if openid_ is None or not openid_:
        return HttpResponseRedirect("%s?%s" % (reverse('user_signin'),
                                urllib.urlencode({ 
                                redirect_field_name: redirect_to })))

    nickname = ''
    email = ''
    if openid_.sreg is not None:
        nickname = openid_.sreg.get('nickname', '')
        email = openid_.sreg.get('email', '')
    if openid_.ax is not None and not nickname or not email:
        if openid_.ax.get('http://schema.openid.net/namePerson/friendly', False):
            nickname = openid_.ax.get('http://schema.openid.net/namePerson/friendly')[0]
        if openid_.ax.get('http://schema.openid.net/contact/email', False):
            email = openid_.ax.get('http://schema.openid.net/contact/email')[0]
        
    
    form1 = register_form(initial={
        'username': nickname,
        'email': email,
    }) 
    form2 = auth_form(initial={ 
        'username': nickname,
    })
    
    if request.POST:
        user_ = None
        if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL
        if 'email' in request.POST.keys():
            form1 = register_form(data=request.POST)
            if form1.is_valid():
                user_ = register_account(form1, openid_)
        else:
            form2 = auth_form(data=request.POST)
            if form2.is_valid():
                user_ = form2.get_user()
        if user_ is not None:
            # associate the user to openid
            uassoc = UserAssociation(
                        openid_url=str(openid_),
                        user_id=user_.id
            )
            uassoc.save(send_email=send_email)
            login(request, user_)    
            return HttpResponseRedirect(redirect_to) 
    
    return render(template_name, {
        'form1': form1,
        'form2': form2,
        redirect_field_name: redirect_to,
        'nickname': nickname,
        'email': email
    }, context_instance=_build_context(request, extra_context=extra_context))

@login_required
def signout(request):
    """
    signout from the website. Remove openid from session and kill it.
    """
    try:
        del request.session['openid']
    except KeyError:
        pass
    next = clean_next(request.GET.get('next'))
    logout(request)
    
    return HttpResponseRedirect(next)
    
def xrdf(request, template_name='authopenid/yadis.xrdf'):
    """ view used to process the xrdf file"""
    
    url_host = get_url_host(request)
    return_to = [
        "%s%s" % (url_host, reverse('user_complete_signin'))
    ]
    response = render(template_name, { 
        'return_to': return_to 
        }, context_instance=RequestContext(request))
        
        
    response['Content-Type'] = "application/xrds+xml"
    response['X-XRDS-Location']= request.build_absolute_uri(reverse('oid_xrdf'))
    return response    
        
@login_required
def password_change(request, 
        template_name='authopenid/password_change_form.html', 
        set_password_form=SetPasswordForm, 
        change_password_form=PasswordChangeForm, post_change_redirect=None, 
        extra_context=None):
    """
    View that allow a user to add a password to its account or change it.

    :attr request: request object
    :attr template_name: string, name of template to use, 
    'authopenid/password_change_form.html' by default
    :attr set_password_form: form use to create a new password. By default 
    ``django.contrib.auth.forms.SetPasswordForm``
    :attr change_password_form: form objectto change passworf. 
    by default `django.contrib.auth.forms.SetPasswordForm.PasswordChangeForm` 
    form auser auth contrib.
    :attr post_change_redirect: url used to redirect user after password change.
    It take the register_form as param.
    :attr extra_context: A dictionary of variables to add to the template context. 
    Any callable object in this dictionary will be called to produce the
    end result which appears in the context.
    """
    if post_change_redirect is None:
        post_change_redirect = settings.LOGIN_REDIRECT_URL

    set_password = False
    if request.user.has_usable_password():
        change_form = change_password_form
    else:
        set_password = True
        change_form = set_password_form

    if request.POST:
        form = change_form(request.user, request.POST)
        if form.is_valid():
            form.save()
            msg = urllib.quote(_("Password changed"))
            redirect_to = "%s?%s" % (post_change_redirect, 
                                urllib.urlencode({ "msg": msg }))
            return HttpResponseRedirect(redirect_to)
    else:
        form = change_form(request.user)

    return render(template_name, {
        'form': form,
        'set_password': set_password
    }, context_instance=_build_context(request, extra_context=extra_context))

@login_required
def associate_failure(request, message, 
        template_failure="authopenid/associate.html", 
        openid_form=AssociateOpenID, redirect_name=None, 
        extra_context=None, **kwargs):
        
    """ function used when new openid association fail"""
    
    return render(template_failure, {
        'form': openid_form(request.user),
        'msg': message,
    }, context_instance=_build_context(request, extra_context=extra_context))

@login_required
def associate_success(request, identity_url, openid_response,
        redirect_field_name=REDIRECT_FIELD_NAME, send_email=True, **kwargs):
    """ 
    function used when new openid association success. redirect the user
    """
    openid_ = from_openid_response(openid_response)
    openids = request.session.get('openids', [])
    openids.append(openid_)
    request.session['openids'] = openids
    uassoc = UserAssociation(
                openid_url=str(openid_),
                user_id=request.user.id
    )
    uassoc.save(send_email=send_email)
    
    redirect_to = request.GET.get(redirect_field_name, '')
    if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
        redirect_to = settings.LOGIN_REDIRECT_URL
    return HttpResponseRedirect(redirect_to)

@login_required
def complete_associate(request, redirect_field_name=REDIRECT_FIELD_NAME,
        template_failure='authopenid/associate.html', 
        openid_form=AssociateOpenID, redirect_name=None, 
        on_success=associate_success, on_failure=associate_failure,
        send_email=True, extra_context=None):
        
    """ in case of complete association with openid """
        
    return complete(request, on_success, on_failure,
            get_url_host(request) + reverse('user_complete_associate'),
            redirect_field_name=redirect_field_name, openid_form=openid_form, 
            template_failure=template_failure, redirect_name=redirect_name, 
            send_email=send_email, extra_context=extra_context)
    
@login_required
def associate(request, template_name='authopenid/associate.html', 
        openid_form=AssociateOpenID, redirect_field_name=REDIRECT_FIELD_NAME,
        on_failure=associate_failure, extra_context=None):
        
    """View that allow a user to associate a new openid to its account.
    
    :attr request: request object
    :attr template_name: string, name of template to use, 
    'authopenid/associate.html' by default
    :attr openid_form: form use enter openid url. By default 
    ``django_authopenid.forms.AssociateOpenID``
    :attr redirect_field_name: string, field name used for redirect. 
    by default 'next'
    :attr on_success: callbale, function used when openid auth success
    :attr on_failure: callable, function used when openid auth failed. 
    by default ``django_authopenid.views.associate_failure`
    :attr extra_context: A dictionary of variables to add to the template
    context. A callable object in this dictionary will be called to produce 
    the end result which appears in the context.
    """
    
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    if request.POST:            
        form = openid_form(request.user, data=request.POST)
        if form.is_valid():
            if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL
            redirect_url = "%s%s?%s" % (
                    get_url_host(request),
                    reverse('user_complete_associate'),
                    urllib.urlencode({ redirect_field_name: redirect_to })
            )
            return ask_openid(request, 
                    form.cleaned_data['openid_url'], 
                    redirect_url, 
                    on_failure=on_failure)
    else:
        form = openid_form(request.user)
    return render(template_name, {
        'form': form,
        redirect_field_name: redirect_to
    }, context_instance=_build_context(request, extra_context=extra_context))     
    
@login_required
def dissociate(request, template_name="authopenid/dissociate.html",
        dissociate_form=OpenidDissociateForm, 
        redirect_field_name=REDIRECT_FIELD_NAME, 
        default_redirect=settings.LOGIN_REDIRECT_URL, extra_context=None):
        
    """ view used to dissociate an openid from an account """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
        redirect_to = default_redirect
        
    # get list of associated openids
    rels = UserAssociation.objects.filter(user__id=request.user.id)
    associated_openids = [rel.openid_url for rel in rels]
    if len(associated_openids) == 1 and not request.user.has_usable_password():
        msg = _("You can't remove this openid. "
        "You should set a password first.")
        return HttpResponseRedirect("%s?%s" % (redirect_to,
            urllib.urlencode({ "msg": msg })))
    
    if request.POST:
        form = dissociate_form(request.POST)
        if form.is_valid():
            openid_url = form.cleaned_data['openid_url']
            msg = ""
            if openid_url not in associated_openids:
                msg = _("%s is not associated to your account") % openid_url
            
            if not msg:
                UserAssociation.objects.get(openid_url__exact=openid_url).delete()
                if openid_url == request.session.get('openid_url'):
                    del request.session['openid_url']
                msg = _("openid removed.")
            return HttpResponseRedirect("%s?%s" % (redirect_to,
                urllib.urlencode({ "msg": msg })))
    else:
        openid_url = request.GET.get('openid_url', '')
        if not openid_url:
            msg = _("Invalid OpenID url.")
            return HttpResponseRedirect("%s?%s" % (redirect_to,
                urllib.urlencode({ "msg": msg })))
        form = dissociate_form(initial={ 'openid_url': openid_url })
    return render(template_name, {
            "form": form,
            "openid_url": openid_url
    }, context_instance=_build_context(request, extra_context=extra_context))
