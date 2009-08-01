# Imports {{{
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
import django.contrib.auth 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import mock
from django_authopenid.forms import OpenidSigninForm

import urllib


import account.forms
import base.views
from profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag, DataImportAttempt
from profile.views import get_personal_data
# }}}

def login(request):
    # {{{
    if request.user.is_authenticated():
        # always, if the user is logged in, redirect to his profile page
        return HttpResponseRedirect('/people/%s/' %
                                    urllib.quote(request.user.username))
    data = {}
    data['notifications'] = base.controllers.get_notification_from_request(
            request)
    return render_to_response('account/login.html', data)
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
def edit_password(request, edit_password_form = None):
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    if edit_password_form is None:
        data['passwordchangeform'] = django.contrib.auth.forms.PasswordChangeForm({})
    else:
        data['passwordchangeform'] = edit_password_form

    # Always show an Edit email form
    data['show_email_form'] = account.forms.ShowEmailForm(
        {'show_email': request.user.get_profile().show_email})

    return render_to_response('account/edit_password.html',
                              data)

@login_required
def edit_password_do(request):
    # {{{
    form = django.contrib.auth.forms.PasswordChangeForm(
            request.user, request.POST)
    if form.is_valid():
        form.save() 
        return HttpResponseRedirect('/people/%s/?msg=edit_password_done' % urllib.quote(request.user.username))
    else:
        return edit_password(request, edit_password_form=form)
    # }}}

@login_required
def show_email_do(request):
    # Check if request.POST contains show_email_address
    form = account.forms.ShowEmailForm(request.POST)
    if form.is_valid():
        profile = request.user.get_profile()
        profile.show_email = form.cleaned_data['show_email']
        profile.save()
    return HttpResponseRedirect('/account/edit/password/')

@login_required
def edit_photo(request, form = None):
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    if form is None:
        form = account.forms.EditPhotoForm()
    data['edit_photo_form'] = form
    return render_to_response('account/edit_photo.html',
                              data)

@login_required
def edit_photo_do(request, mock=None):
    data = get_personal_data(
            request.user.get_profile())
    person = request.user.get_profile()
    form = account.forms.EditPhotoForm(request.POST,
                                       request.FILES,
                                       instance=person)
    if form.is_valid():
        form.save()
    return edit_photo(request, form = form)

def catch_me(request):
    import pdb
    pdb.set_trace()

# vim: ai ts=3 sts=4 et sw=4 nu
