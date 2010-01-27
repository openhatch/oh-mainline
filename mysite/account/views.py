# Imports {{{
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
import django.contrib.auth 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django_authopenid.forms import OpenidSigninForm
from django.core.urlresolvers import reverse

from invitation.forms import InvitationKeyForm
from invitation.models import InvitationKey

import urllib
import mock
import logging

from mysite.account.forms import InvitationRequestForm
import mysite.base.views
import mysite.base.controllers
from mysite.base.controllers import get_notification_from_request
from mysite.profile.models import Person, Tag, TagType, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag, DataImportAttempt

# FIXME: We did this because this decorator used to live here
# and lots of other modules refer to it as mysite.account.views.view.
# Let's fix this soon.
from mysite.base.decorators import view
# }}}

def signup_do(request):
    # {{{
    post = {}
    post.update(dict(request.POST.items()))
    post['password2'] = post['password1'] 
    signup_form = mysite.account.forms.UserCreationFormWithEmail(post)
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
        return mysite.account.views.signup(request, signup_form=signup_form)
    # }}}

def signup(request, signup_form=None, invite_code=''):
    # {{{
    if signup_form is None:
        signup_form = mysite.account.forms.UserCreationFormWithEmail(
            initial={'invite_code': invite_code})

    return render_to_response('account/signup.html',
                              {'form': signup_form})
    # }}}

def logout(request):
    # {{{
    django.contrib.auth.logout(request)
    return HttpResponseRedirect("/?msg=ciao#tab=login")
    # }}}

@login_required
@view
def edit_photo(request, form = None):
    if form is None:
        form = mysite.account.forms.EditPhotoForm()
    data = mysite.profile.views.get_personal_data(request.user.get_profile())
    data['edit_photo_form'] = form
    return (request, 'account/edit_photo.html', data)

@login_required
def edit_photo_do(request, mock=None):
    person = request.user.get_profile()
    data = mysite.profile.views.get_personal_data(person)
    form = mysite.account.forms.EditPhotoForm(request.POST,
                                       request.FILES,
                                       instance=person)
    if form.is_valid():
        person = form.save()
        person.generate_thumbnail_from_photo()

        return HttpResponseRedirect(reverse(mysite.profile.views.display_person_web, kwargs={
            'user_to_display__username': request.user.username
            }))
    else:
        return edit_photo(request, form)

def catch_me(request):
    failboat # NameError

@login_required
@view
def settings(request):
    # {{{
    data = {}
    return (request, 'account/settings.html', data)
    # }}}

@login_required
@view
def edit_contact_info(request, edit_email_form = None, show_email_form = None,
                      ):
    # {{{

    data = {}

    if request.GET.get('notification_id', None) == 'success':
        data['account_notification'] = 'Settings saved.'
    else:
        data['account_notification'] = ''

    # Store edit_email_form in data[], even if we weren't passed one
    if edit_email_form is None:
        edit_email_form = mysite.account.forms.EditEmailForm(
            instance=request.user, prefix='edit_email')
    data['edit_email_form'] = edit_email_form
    
    if show_email_form is None:
        show_email = request.user.get_profile().show_email
        prefix = "show_email"
        data['show_email_form'] =  mysite.account.forms.ShowEmailForm(
                initial={'show_email': show_email}, prefix=prefix)
    else:
        data['show_email_form'] = show_email_form

    return (request, 'account/edit_contact_info.html', data)
    # }}}

@login_required
def edit_contact_info_do(request):
    # {{{
    # Handle "Edit email"
    edit_email_form = mysite.account.forms.EditEmailForm(
            request.POST, prefix='edit_email', instance=request.user)

    show_email_form = mysite.account.forms.ShowEmailForm(
            request.POST, prefix='show_email')

    # Email saving functionality requires two forms to both be
    # valid. This really ought to be the same form, anyway.
    if (edit_email_form.is_valid() and show_email_form.is_valid()):
        p = request.user.get_profile()
        p.show_email = show_email_form.cleaned_data['show_email']
        p.save()

        logging.debug('Changing email of user <%s> to <%s>' % (
                request.user, edit_email_form.cleaned_data['email']))
        edit_email_form.save()

        return HttpResponseRedirect(reverse(edit_contact_info) +
                                    '?notification_id=success')
    else:
        return edit_contact_info(request,
                edit_email_form=edit_email_form,
                show_email_form=show_email_form)
    # }}}

@login_required
@view
def change_password(request, change_password_form = None):
    # {{{

    if change_password_form is None:
        change_password_form = django.contrib.auth.forms.PasswordChangeForm({})

    change_password_form.fields['old_password'].label = "Current password"
    change_password_form.fields['new_password2'].label = "Type it again"

    if request.GET.get('notification_id', None) == 'success':
        account_notification = 'Your password has been changed.'
    else:
        account_notification = ''

    return (request, 'account/change_password.html',
            {'change_password_form': change_password_form,
             'account_notification': account_notification})
    # }}}

@login_required
@view
def set_location(request, edit_location_form = None):
    # {{{
    data = {}
    initial = {}

    if request.GET.get('dont_suggest_location', None) == '1':
        data['dont_suggest_location'] = True
        initial['location_display_name'] = ''

    # Initialize edit location form
    if edit_location_form is None:
        edit_location_form = mysite.account.forms.EditLocationForm(
                prefix='edit_location', instance=request.user.get_profile(), initial = initial)

    data['edit_location_form'] = edit_location_form

    if request.GET.get('notification_id', None) == 'success':
        data['account_notification'] = 'Saved.'
    else:
        data['account_notification'] = ''

    return (request, 'account/set_location.html', data)
    # }}}

@login_required
def set_location_do(request):
    user_profile = request.user.get_profile()
    edit_location_form = mysite.account.forms.EditLocationForm(
        request.POST,
        instance=user_profile, prefix='edit_location')
    if edit_location_form.is_valid():
        user_profile.location_confirmed = True
        user_profile.save()
        edit_location_form.save()
        return HttpResponseRedirect(reverse(set_location) +
                                    '?notification_id=success')
    else:
        return set_location(request,
                edit_location_form=edit_location_form)
       
@login_required
def confirm_location_suggestion_do(request):
    person = request.user.get_profile()
    person.location_confirmed = True
    person.save()
    return HttpResponse()

@login_required
def dont_guess_location_do(request):
    person = request.user.get_profile()
    person.dont_guess_my_location = True
    person.location_display_name = ''
    person.save()
    return HttpResponse()

@login_required
def change_password_do(request):
    # {{{
    form = django.contrib.auth.forms.PasswordChangeForm(
            request.user, request.POST)
    if form.is_valid():
        form.save() 
        return HttpResponseRedirect(
            reverse(change_password) + '?notification_id=success')
    else:
        return change_password(request, change_password_form=form)
    # }}}

@view
def widget(request):
    return (request, 'account/widget.html', {})

@login_required
@view
def invite_someone(request, form=None,success_message=''):
    if form is None:
        invite_someone_form = InvitationKeyForm()
    else:
        invite_someone_form = form

    remaining_invites = InvitationKey.objects.remaining_invitations_for_user(
        request.user)

    return (request, 'account/invite_someone.html', {
            'success_message': success_message,
            'invite_someone_form': invite_someone_form,
            'remaining_invites': remaining_invites})

@login_required
def invite_someone_do(request):
    remaining_invitations = InvitationKey.objects.remaining_invitations_for_user(
        request.user)

    form = InvitationKeyForm(data=request.POST)
    if form.is_valid():
        if remaining_invitations > 0:
            invitation = InvitationKey.objects.create_invitation(request.user)
            invitation.send_to(form.cleaned_data["email"])
            # Yay! Redirect back to invite page, with message saying who
            # was just invited.
            return HttpResponseRedirect(
                reverse(invite_someone) + '?invited=' +
                urllib.quote(form.cleaned_data['email']))
        else: # yes, there's an email; no, the guy can't invite
            return invite_someone(request, form=form,
                                  error_message='No more invites.')
    else:
        return invite_someone(request, form=form)

def request_invitation(request):
    invitation_request_form = mysite.account.forms.InvitationRequestForm(request.POST)
    if invitation_request_form.is_valid():
        invitation_request_form.save()

        # Send user back to homepage with a notification
        url = "%s?%s#%s" % (
                reverse(mysite.base.views.homepage),
                urllib.urlencode({
                    'invitation_requested_for': 
                    invitation_request_form.cleaned_data['email']}),
                "tab=request_invitation"
                )
        return HttpResponseRedirect(url)
    else:
        return mysite.base.views.homepage(request, 
                invitation_request_form=invitation_request_form,
                initial_tab_open='request_invitation')

# vim: ai ts=3 sts=4 et sw=4 nu
