# Imports {{{
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
import django.contrib.auth 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import mock
from django_authopenid.forms import OpenidSigninForm
from django.core.urlresolvers import reverse

import urllib
import logging


import account.forms
import base.views
from profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag, DataImportAttempt
from profile.views import get_personal_data
# }}}

applog = logging.getLogger('applog')

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
def edit_photo(request, form = None):
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    if form is None:
        form = account.forms.EditPhotoForm()
    data['edit_photo_form'] = form
    return render_to_response('account/edit_photo.html', data)

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
    return HttpResponseRedirect('/account/edit/photo')

def catch_me(request):
    import pdb
    pdb.set_trace()

@login_required
def settings(request):
    # {{{
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user

    return render_to_response('account/settings.html', data)
    # }}}

@login_required
def edit_contact_info(request, edit_email_form = None, show_email_form = None):
    # {{{
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user

    # Store edit_email_form in data[], even if we weren't passed one
    if edit_email_form is None:
        edit_email_form = account.forms.EditEmailForm(
            instance=request.user, prefix='edit_email')
    data['edit_email_form'] = edit_email_form
    
    if show_email_form is None:
        show_email = request.user.get_profile().show_email
        prefix = "show_email"
        data['show_email_form'] = account.forms.ShowEmailForm(
                initial={'show_email': show_email}, prefix=prefix)
    else:
        data['show_email_form'] = show_email_form

    return render_to_response('account/edit_contact_info.html', data)
    # }}}

@login_required
def edit_contact_info_do(request):
    # {{{

    # Handle "Edit email"
    edit_email_form = account.forms.EditEmailForm(
            request.POST, prefix='edit_email', instance=request.user)

    show_email_form = account.forms.ShowEmailForm(
            request.POST, prefix='show_email')

    if edit_email_form.is_valid() and show_email_form.is_valid():
        p = request.user.get_profile()
        p.show_email = show_email_form.cleaned_data['show_email']
        p.save()

        applog.debug('Changing email of user <%s> to <%s>' % (
                request.user, edit_email_form.cleaned_data['email']))
        edit_email_form.save()

        return HttpResponseRedirect(reverse(edit_contact_info))
    else:
        return edit_contact_info(request,
                edit_email_form=edit_email_form,
                show_email_form=show_email_form)
    # }}}

@login_required
def change_password(request, change_password_form = None):
    # {{{
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    if change_password_form is None:
        data['change_password_form'] = django.contrib.auth.forms.PasswordChangeForm({})
    else:
        data['change_password_form'] = change_password_form

    return render_to_response('account/change_password.html', data)
    # }}}

@login_required
def change_password_do(request):
    # {{{
    form = django.contrib.auth.forms.PasswordChangeForm(
            request.user, request.POST)
    if form.is_valid():
        form.save() 
        return HttpResponseRedirect(reverse(change_password))
    else:
        return change_password(request, change_password_form=form)
    # }}}

@login_required
def show_email(request, show_email_form = None):
    # {{{
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    return render_to_response('account/show_email.html', data)
    # }}}

@login_required
def show_email_do(request):
    # {{{
    # Check if request.POST contains show_email_address
    form = account.forms.ShowEmailForm(request.POST)
    if form.is_valid():
        profile = request.user.get_profile()
        profile.show_email = form.cleaned_data['show_email']
        profile.save()
    return HttpResponseRedirect(reverse(change_password))
    # }}}

# vim: ai ts=3 sts=4 et sw=4 nu
