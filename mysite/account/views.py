# Imports {{{
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
import django.contrib.auth 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django_authopenid.forms import OpenidSigninForm

import urllib


import account.forms
import base.views
from profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag, DataImportAttempt
from profile.views import get_personal_data
# }}}

def login(request):
    # {{{
    notification = notification_id = None
    if request.GET.get('msg', None) == 'oops':
        notification_id = "oops"
        notification = "Couldn't find that pair of username and password. "
        notification += "Did you type your password correctly?"
    if request.GET.get('next', None) is not None:
        notification_id = "next"
        notification = "You've got to be logged in to do that!"
    return render_to_response('account/login.html', {
        'notification_id': notification_id,
        'notification': notification,
        } )
    # }}}

def login_do(request):
    # {{{
    try:
        username = request.POST['login_username']
        password = request.POST['login_password']
    except KeyError:
        return HttpResponseServerError("Missing username or password.")
    user = django.contrib.auth.authenticate(
            username=username, password=password)
    if user is not None:
        django.contrib.auth.login(request, user)
        return HttpResponseRedirect('/people/%s' % urllib.quote(username))
    else:
        return HttpResponseRedirect('/account/login/?msg=oops')
    # }}}

def signup_do(request):
    # {{{
    post = {}
    post.update(dict(request.POST.items()))
    post['password2'] = post['password1'] 
    signup_form = account.forms.UserCreationFormWithEmail(post)
    if signup_form.is_valid():

        user = signup_form.save()

        # create a linked person
        person = Person(user=user)
        person.save()

        username = request.POST['username']
        password = request.POST['password1']

        # authenticate and login
        user = django.contrib.auth.authenticate(
                username=username,
                password=password)
        django.contrib.auth.login(request, user)

        # redirect to profile
        return HttpResponseRedirect(
                '/people/%s/' % urllib.quote(username))

    else:
        return base.views.homepage(request, signup_form=signup_form)
    # }}}

def logout(request):
    # {{{
    django.contrib.auth.logout(request)
    return HttpResponseRedirect("/?msg=ciao#tab=login")
    # }}}

@login_required
def edit_password(request, form = None):
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    if form is None:
        data['passwordchangeform'] = django.contrib.auth.forms.PasswordChangeForm({})
    else:
        data['passwordchangeform'] = form
    return render_to_response('account/edit_password.html',
                              data)

@login_required
def edit_password_do(request):
    form = django.contrib.auth.forms.PasswordChangeForm(
            request.user, request.POST)
    if form.is_valid():
        form.save() 
        return HttpResponseRedirect('/account/edit/')
    else:
        return edit_password(request, form)
# -*- coding: utf-8 -*-
from django.contrib.auth.forms import *
from django.shortcuts import render_to_response as render
from django.template import RequestContext, loader, Context

from django_authopenid.forms import *


def openid_etc_login(request):
    form1 = OpenidSigninForm()
    form2 = AuthenticationForm()
    return render("account/openid_etc_login.html", {
        'form1': form1,
        'form2': form2
    }, context_instance=RequestContext(request))

def catch_me(request):
    import pdb
    pdb.set_trace()
