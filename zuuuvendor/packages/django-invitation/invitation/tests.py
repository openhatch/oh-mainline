"""
Unit tests for django-invitation.

These tests assume that you've completed all the prerequisites for
getting django-invitation running in the default setup, to wit:

1. You have ``invitation`` in your ``INSTALLED_APPS`` setting.

2. You have created all of the templates mentioned in this
   application's documentation.

3. You have added the setting ``ACCOUNT_INVITATION_DAYS`` to your
   settings file.

4. You have URL patterns pointing to the invitation views.

"""

import datetime
import sha

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core import management
from django.core.urlresolvers import reverse
from django.test import TestCase

from invitation import forms
from invitation.models import InvitationKey

class InvitationTestCase(TestCase):
    """
    Base class for the test cases; this sets up one user and two keys -- one
    expired, one not -- which are used to exercise various parts of
    the application.
    
    """
    def setUp(self):
        self.sample_user = User.objects.create_user(username='alice',
                                                    password='secret',
                                                    email='alice@example.com')
        self.sample_key = InvitationKey.objects.create_invitation(user=self.sample_user)
        self.expired_key = InvitationKey.objects.create_invitation(user=self.sample_user)
        self.expired_key.date_invited -= datetime.timedelta(days=settings.ACCOUNT_INVITATION_DAYS + 1)
        self.expired_key.save()


class InvitationModelTests(InvitationTestCase):
    """
    Tests for the model-oriented functionality of django-registration,
    including ``RegistrationProfile`` and its custom manager.
    
    """
    def test_registration_profile_created(self):
        """
        Test that a ``InvitationKey`` is created for a new key.
        
        """
        self.assertEqual(InvitationKey.objects.count(), 2)

    def test_activation_email(self):
        """
        Test that user signup sends an activation email.
        
        """
        self.sample_key.send_to('bob@example.com')
        self.assertEqual(len(mail.outbox), 1)

    def test_key_expiration_condition(self):
        """
        Test that ``InvitationKey.key_expired()`` returns ``True`` for expired 
        keys, and ``False`` otherwise.
        
        """
        # Unexpired user returns False.
        self.failIf(self.sample_key.key_expired())

        # Expired user returns True.
        self.failUnless(self.expired_key.key_expired())

    def test_expired_user_deletion(self):
        """
        Test that
        ``RegistrationProfile.objects.delete_expired_users()`` deletes
        only inactive users whose activation window has expired.
        
        """
        InvitationKey.objects.delete_expired_keys()
        self.assertEqual(InvitationKey.objects.count(), 1)

    def test_management_command(self):
        """
        Test that ``manage.py cleanupinvitation`` functions
        correctly.
        
        """
        management.call_command('cleanupinvitation')
        self.assertEqual(InvitationKey.objects.count(), 1)


class InvitationFormTests(InvitationTestCase):
    """
    Tests for the forms and custom validation logic included in
    django-invitation.
    
    """
    def test_invitation_form(self):
        """
        Test that ``InvitationKeyForm`` enforces email constraints.
        
        """
        invalid_data_dicts = [
            # Invalid email.
            {
            'data': { 'email': 'example.com' },
            'error': ('email', [u"Enter a valid e-mail address."])
            },
            ]

        for invalid_dict in invalid_data_dicts:
            form = forms.InvitationKeyForm(data=invalid_dict['data'])
            self.failIf(form.is_valid())
            self.assertEqual(form.errors[invalid_dict['error'][0]], invalid_dict['error'][1])

        form = forms.InvitationKeyForm(data={ 'email': 'foo@example.com' })
        self.failUnless(form.is_valid())


class InvitationViewTests(InvitationTestCase):
    """
    Tests for the views included in django-invitation.
    
    """
    def test_invitation_view(self):
        """
        Test that the invitation view rejects invalid submissions,
        and creates a new key and redirects after a valid submission.
        
        """
        # You need to be logged in to send an invite.
        response = self.client.login(username='alice', password='secret')
        
        # Invalid email data fails.
        response = self.client.post(reverse('invitation_invite'),
                                    data={ 'email': 'example.com' })
        self.assertEqual(response.status_code, 200)
        self.failUnless(response.context['form'])
        self.failUnless(response.context['form'].errors)

        response = self.client.post(reverse('invitation_invite'),
                                    data={ 'email': 'foo@example.com' })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver%s' % reverse('invitation_complete'))
        self.assertEqual(InvitationKey.objects.count(), 3)
    
    def test_activated_view(self):
        """
        Test that the invited view invite the user from a valid
        key and fails if the key is invalid or has expired.
       
        """
        # Valid key puts use the invited template.
        response = self.client.get(reverse('invitation_invited',
                                           kwargs={ 'invitation_key': self.sample_key.key }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template.name, 'invitation/invited.html')

        # Expired key use the wrong key template.
        response = self.client.get(reverse('invitation_invited',
                                           kwargs={ 'invitation_key': self.expired_key.key }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template.name, 'invitation/wrong_invitation_key.html')

        # Invalid key use the wrong key template.
        response = self.client.get(reverse('invitation_invited',
                                           kwargs={ 'invitation_key': 'foo' }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template.name, 'invitation/wrong_invitation_key.html')

        # Nonexistent key use the wrong key template.
        response = self.client.get(reverse('invitation_invited',
                                           kwargs={ 'invitation_key': sha.new('foo').hexdigest() }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template.name, 'invitation/wrong_invitation_key.html')
