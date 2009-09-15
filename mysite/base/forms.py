from django_authopenid.forms import OpenidRegisterForm
import django.forms
from django.conf import settings
from invitation.models import InvitationKey

class OpenidRegisterFormWithInviteCode(OpenidRegisterForm):
    invite_code = django.forms.CharField(required=False,
                                         label='Invite code',
                                         error_messages={
            'invalid': 'You must enter a valid invite code.'})

    def clean_invite_code(self):
        import pdb
        pdb.set_trace()
        if settings.INVITE_MODE:
            if InvitationKey.objects.is_key_valid(self.cleaned_data['invite_code']):
                return self.cleaned_data['invite_code']
            raise django.forms.ValidationError(
                'You need a valid invite code for now.')
        else:
            return self.cleaned_data['invite_code']

