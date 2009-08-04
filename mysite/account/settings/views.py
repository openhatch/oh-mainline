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

@login_required
def settings(request)
    # {{{
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user

    return render_to_response('account/settings/settings.html', data)
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
            instance=request.user, prefix='edit-email')
    data['edit_email_form'] = edit_email_form
    
    if show_email_form is None:
        data['show_email_form'] = account.forms.ShowEmailForm(
                prefix='show-email')
    else:
        data['show_email_form'] = edit_password_form

    return render_to_response('account/settings/edit_contact_info.html', data)
    # }}}

@login_required
def edit_contact_info_do(request):
    # {{{

    # Handle "Edit email"
    edit_email_form = account.forms.EditEmailForm(
            request.POST, prefix='edit_email', instance=request.user)

    show_email_form = account.forms.ShowEmailForm(
            request.POST, prefix='show_email', instance=request.user)

    if form.is_valid():
        applog.debug('Changing email of user <%s> to <%s>' % (
                request.user, form.cleaned_data['email']))
        form.save()
    else:
        return edit_contact_info(request,
                edit_email_form=edit_email_form,
                show_email_form=show_email_form)
    return HttpResponseRedirect(reverse(edit_email_form))
    # }}}

@login_required
def edit_password(request, edit_password_form = None):
    # {{{
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    if edit_password_form is None:
        data['password_change_form'] = django.contrib.auth.forms.PasswordChangeForm({})
    else:
        data['password_change_form'] = edit_password_form

    return render_to_response('account/edit_password.html', data)
    # }}}

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
    return HttpResponseRedirect(reverse(edit_password))
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

# vim: ai ts=3 sts=4 et sw=4 nu
