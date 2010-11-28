# Imports {{{
from django.http import HttpResponse, HttpResponseRedirect
import django.contrib.auth 
from django.contrib.auth.decorators import login_required
import django.contrib.auth.forms
from django.core.urlresolvers import reverse
import django_authopenid.views

from invitation.forms import InvitationKeyForm
from invitation.models import InvitationKey

import urllib
import logging

import mysite.base.views
import mysite.base.controllers
import mysite.account.forms
from mysite.base.helpers import render_response
import mysite.profile.views

# FIXME: We did this because this decorator used to live here
# and lots of other modules refer to it as mysite.account.views.view.
# Let's fix this soon.
from mysite.base.decorators import view
import django.contrib.auth.views
# }}}

def signup_do(request):
    # {{{
    post = {}
    post.update(dict(request.POST.items()))
    post['password2'] = post.get('password1', '')
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

def signup(request, signup_form=None):
    if signup_form is None:
        signup_form = mysite.account.forms.UserCreationFormWithEmail()

    return render_response(request, 'account/signup.html', {'form': signup_form})

@login_required
@view
def edit_photo(request, form=None, non_validation_error=False):
    """
    Set or change your profile photo.

    If non_validation_error is True, there was an error outside the scope of
    form validation, eg an exception was raised while processing the photo.
    """
    if form is None:
        form = mysite.account.forms.EditPhotoForm()
    data = mysite.profile.views.get_personal_data(request.user.get_profile())
    data['edit_photo_form'] = form

    if non_validation_error:
        data['non_validation_error'] = True

    return (request, 'account/edit_photo.html', data)

@login_required
def edit_photo_do(request, mock=None):
    person = request.user.get_profile()
    form = mysite.account.forms.EditPhotoForm(request.POST,
                                       request.FILES,
                                       instance=person)

    try:
        # Exceptions can be raised by the photo manipulation libraries while
        # "cleaning" the photo during form validation.
        valid = form.is_valid()
    except Exception, e:
            logging.error("%s while preparing the image: %s"
                          % (str(type(e)), str(e)))
            # Don't pass in the form. This gives the user an empty form and a
            # nice error message, instead of the displaying the details of the
            # error.
            return edit_photo(request, form=None, non_validation_error=True)

    if valid:
        person = form.save()
        person.generate_thumbnail_from_photo()

        return HttpResponseRedirect(
            reverse(mysite.profile.views.display_person_web, kwargs={
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
def edit_contact_info(request, edit_email_form=None, show_email_form=None, email_me_form=None):
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

    if email_me_form is None:
        email_me_form = mysite.account.forms.EmailMeForm(
            instance=request.user.get_profile(), prefix='email_me')
    data['email_me_form'] = email_me_form

    return (request, 'account/edit_contact_info.html', data)

@login_required
def edit_contact_info_do(request):
    # Handle "Edit email"
    edit_email_form = mysite.account.forms.EditEmailForm(
            request.POST, prefix='edit_email', instance=request.user)

    show_email_form = mysite.account.forms.ShowEmailForm(
            request.POST, prefix='show_email')

    email_me_form = mysite.account.forms.EmailMeForm(
            request.POST, prefix='email_me', instance=request.user.get_profile())

    # Email saving functionality requires two forms to both be
    # valid. This really ought to be the same form, anyway.
    if (edit_email_form.is_valid() and show_email_form.is_valid()):

        # Note that we don't need to check the validity of the EmailMeForm,
        # because it contains only an optional BooleanField.
        p = email_me_form.save()
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
def edit_name(request, edit_name_form = None):
    # {{{

    if edit_name_form is None:
        edit_name_form = mysite.account.forms.EditNameForm(instance=request.user)

    if request.GET.get('notification_id', None) == 'success':
        if request.user.first_name or request.user.last_name:
            account_notification = 'You have a new name.'
        else:
            account_notification = """You've removed your full name.
            We'll identify you by your username."""
    else:
        account_notification = ''

    return (request, 'account/edit_name.html',
            {'edit_name_form': edit_name_form,
             'account_notification': account_notification})
    # }}}

@login_required
def edit_name_do(request):
    user = request.user
    edit_name_form = mysite.account.forms.EditNameForm(
        request.POST, instance=user)
    if edit_name_form.is_valid():
        edit_name_form.save()

        # Enqueue a background task to re-index the person
        task = mysite.profile.tasks.ReindexPerson()
        task.delay(person_id=user.get_profile().id)

        return HttpResponseRedirect(reverse(edit_name) +
                                    '?notification_id=success')
    else:
        return edit_name(request,
                edit_name_form=edit_name_form)

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

        # Enqueue a background task to re-index the person
        task = mysite.profile.tasks.ReindexPerson()
        task.delay(person_id=user_profile.id)

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

@login_required
@view
def widget(request):
    data = {}
    data.update(mysite.base.controllers.get_uri_metadata_for_generating_absolute_links(
        request))
    return (request, 'account/widget.html', data)

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

### The following is copied here from django_authopenid, and then
### modified trivially in the POST handler.
@django_authopenid.views.not_authenticated
def register(request, template_name='authopenid/complete.html', 
             redirect_field_name=django.contrib.auth.REDIRECT_FIELD_NAME, 
             register_form=django_authopenid.forms.OpenidRegisterForm,
             auth_form=django.contrib.auth.forms.AuthenticationForm, 
             register_account=django_authopenid.views.register_account, send_email=False, 
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
                
                extra_profile_form = mysite.account.forms.SignUpIfYouWantToHelpForm(
                    request.POST, prefix='extra_profile_form')
                if extra_profile_form.is_valid():
                    person = user_.get_profile()
                    method2contact_info = {
                        'forwarder': 'You can reach me by email at $fwd',
                        'public_email': 'You can reach me by email at %s' % user_.email,
                        }
                    info = method2contact_info[extra_profile_form.cleaned_data[
                        'how_should_people_contact_you']]
                    person.contact_blurb = info
                    person.save()
                
        else:
            form2 = auth_form(data=request.POST)
            if form2.is_valid():
                user_ = form2.get_user()
        if user_ is not None:
            # associate the user to openid
            uassoc = django_authopenid.models.UserAssociation(
                        openid_url=str(openid_),
                        user_id=user_.id
            )
            uassoc.save(send_email=send_email)
            django.contrib.auth.login(request, user_)
            return HttpResponseRedirect(redirect_to) 
    
    return render_response(request, template_name, {
        'form1': form1,
        'form2': form2,
        'extra_profile_form': mysite.account.forms.SignUpIfYouWantToHelpForm(
            prefix='extra_profile_form'),
        redirect_field_name: redirect_to,
        'nickname': nickname,
        'email': email
    }, context_instance=django_authopenid.views._build_context(request, extra_context=extra_context))

# vim: ai ts=3 sts=4 et sw=4 nu
