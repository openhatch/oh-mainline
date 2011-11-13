from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from registration.views import register as registration_register
from registration.forms import RegistrationForm

from invitation.models import InvitationKey
from invitation.forms import InvitationKeyForm

is_key_valid = InvitationKey.objects.is_key_valid

# TODO: move the authorization control to a dedicated decorator

def invited(request, invitation_key=None):
    if 'INVITE_MODE' in settings.get_all_members() and settings.INVITE_MODE:
        if invitation_key and is_key_valid(invitation_key):
            template = 'invitation/invited.html'
        else:
            template = 'invitation/wrong_invitation_key.html'
        return direct_to_template(request, template, {'invitation_key': invitation_key})
    else:
        return HttpResponseRedirect(reverse('registration_register'))

def register(request, success_url=None,
            form_class=RegistrationForm, profile_callback=None,
            template_name='registration/registration_form.html',
            extra_context=None):
    if 'INVITE_MODE' in settings.get_all_members() and settings.INVITE_MODE:
        if 'invitation_key' in request.REQUEST \
            and is_key_valid(request.REQUEST['invitation_key']):
            if extra_context is None:
                extra_context = {'invitation_key': request.REQUEST['invitation_key']}
            else:
                extra_context.update({'invitation_key': invitation_key})
            return registration_register(request, success_url, form_class, 
                        profile_callback, template_name, extra_context)
        else:
            return direct_to_template(request, 'invitation/wrong_invitation_key.html')
    else:
        return registration_register(request, success_url, form_class, 
                            profile_callback, template_name, extra_context)

def invite(request, success_url=None,
            form_class=InvitationKeyForm,
            template_name='invitation/invitation_form.html',):
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            invitation = InvitationKey.objects.create_invitation(request.user)
            invitation.send_to(form.cleaned_data["email"])
            # success_url needs to be dynamically generated here; setting a
            # a default value using reverse() will cause circular-import
            # problems with the default URLConf for this application, which
            # imports this file.
            return HttpResponseRedirect(success_url or reverse('invitation_complete'))
    else:
        form = form_class()
    return direct_to_template(request, template_name, {
        'form': form,
        'remaining_invitations': InvitationKey.objects.remaining_invitations_for_user(request.user),
    })
invite = login_required(invite)
