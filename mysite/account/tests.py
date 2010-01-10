#{{{ imports
import os
import Image
import urllib
import mock

from mysite.profile.models import Person
from mysite.base.tests import make_twill_url, TwillTests
from mysite.profile.models import Person
import mysite.account.views
import mysite.account.forms

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test.client import Client
from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse
import django.core.mail

from django.conf import settings
from twill import commands as tc

from invitation.models import InvitationKey
#}}}

class Login(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    
    def test_login(self):
        user = authenticate(username='paulproteus',
                password="paulproteus's unbreakable password")
        self.assert_(user and user.is_active)

    def test_login_web(self):
        self.login_with_twill()

    def test_logout_web(self):
        self.test_login_web()
        url = 'http://openhatch.org/search/'
        url = make_twill_url(url)
        tc.go(url)
        tc.follow('log out')
        tc.find('ciao')
    # }}}

class LoginWithOpenID(TwillTests):
    #{{{
    fixtures = ['user-paulproteus']
    def test_login_creates_user_profile(self):
        # Front page
        url = 'http://openhatch.org/'

        # Even though we didn't add the person-paulproteus
        # fixture, a Person object is created.
        self.assert_(list(
            Person.objects.filter(user__username='paulproteus')))
    #}}}

class Signup(TwillTests):
    """ Tests for signup without invite code. """
    pass
    # }}}

class EditPassword(TwillTests):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def change_password(self, old_pass, new_pass,
            should_succeed = True):
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus'))
        tc.follow('settings')
        tc.follow('Password')
        tc.url('/account/settings/password')

        tc.fv('a_settings_tab_form', 'old_password', old_pass)
        tc.fv('a_settings_tab_form', 'new_password1', new_pass)
        tc.fv('a_settings_tab_form', 'new_password2', new_pass)
        tc.submit()

        # Try to log in with the new password now
        client = Client()
        username='paulproteus'
        success = client.login(username=username,
                password=new_pass)
        if should_succeed:
            success = success
        else:
            success = not success
        self.assert_(success)

    def test_change_password(self):
        self.login_with_twill()
        oldpass="paulproteus's unbreakable password"
        newpass='new'
        self.change_password(oldpass, newpass)

    def test_change_password_should_fail(self):
        self.login_with_twill()
        oldpass="wrong"
        newpass='new'
        self.change_password(oldpass, newpass,
                should_succeed = False)
#}}}

class EditContactInfo(TwillTests):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def test_edit_email_address(self):
        self.login_with_twill()
        

        _url = 'http://openhatch.org/account/settings/contact-info/'
        url = make_twill_url(_url)

        email = 'new@ema.il'

        # Go to contact info form
        tc.go(url)

        # Let's first ensure that "new@ema.il" doesn't appear on the page.
        # (We're about to add it.)
        tc.notfind('checked="checked"')
        tc.notfind(email)

        # Edit email
        tc.fv("a_settings_tab_form", 'edit_email-email', email)
        # Show email
        tc.fv("a_settings_tab_form", 'show_email-show_email', '1') # [1]
        tc.submit()

        # Form submission ought to redirect us back to the form.
        tc.url(url)

        # Was email successfully edited? 
        tc.find(email)

        # Was email visibility successfully edited? [2]
        tc.find('checked="checked"')

        # And does the email address show up on the profile?
        tc.go(make_twill_url(
                'http://openhatch.org/people/paulproteus'))
        tc.find(email)

        # 2. And when we uncheck, does it go away?
        
        # 2.1. Go to contact info form
        tc.go(url)

        # 2.2. Don't show email
        tc.fv("a_settings_tab_form", 'show_email-show_email', '0') # [1]
        tc.submit()

        # 2.3. Verify it's not on profile anymore
        tc.go(make_twill_url(
                'http://openhatch.org/people/paulproteus'))
        tc.notfind(email)

        # [1]: This email suggests that twill only accepts
        # *single quotes* around the '1'.
        # <http://lists.idyll.org/pipermail/twill/2006-February/000224.html>
        #
        # [2]: This assertion works b/c there's only one checkbox.
    #}}}

photos = [os.path.join(os.path.dirname(__file__),
                       '..', '..', 'sample-photo.' + ext)
                       for ext in ('png', 'jpg')]

def photo(f):
    filename = os.path.join(
        os.path.dirname(__file__),
        '..', f)
    assert os.path.exists(filename)
    return filename

class EditPhoto(TwillTests):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def test_set_avatar(self):
        self.login_with_twill()
        for image in [photo('static/sample-photo.png'),
                      photo('static/sample-photo.jpg')]:
            url = 'http://openhatch.org/people/paulproteus/'
            tc.go(make_twill_url(url))
            tc.follow('Change photo')
            tc.formfile('edit_photo', 'photo', image)
            tc.submit()
            # Now check that the photo == what we uploaded
            p = Person.objects.get(user__username='paulproteus')
            self.assert_(p.photo.read() ==
                         open(image).read())

            response = self.login_with_client().get(reverse(mysite.account.views.edit_photo))
            self.assertEqual( response.context[0]['photo_url'], p.photo.url,
                    "Test that once you've uploaded a photo via the photo editor, "
                    "the template's photo_url variable is correct.")
            self.assert_(p.photo_thumbnail)
            thumbnail_as_stored = Image.open(p.photo_thumbnail.file)
            w, h = thumbnail_as_stored.size
            self.assertEqual(w, 40)

    def test_set_avatar_too_wide(self):
        self.login_with_twill()
        for image in [photo('static/images/too-wide.jpg'),
                      photo('static/images/too-wide.png')]:
            url = 'http://openhatch.org/people/paulproteus/'
            tc.go(make_twill_url(url))
            tc.follow('Change photo')
            tc.formfile('edit_photo', 'photo', image)
            tc.submit()
            # Now check that the photo is 200px wide
            p = Person.objects.get(user__username='paulproteus')
            image_as_stored = Image.open(p.photo.file)
            w, h = image_as_stored.size
            self.assertEqual(w, 200)

    #}}}

class EditPhotoWithOldPerson(TwillTests):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus-with-blank-photo']
    def test_set_avatar(self):
        self.login_with_twill()
        for image in (photo('static/sample-photo.png'),
                      photo('static/sample-photo.jpg')):
            url = 'http://openhatch.org/people/paulproteus/'
            tc.go(make_twill_url(url))
            tc.follow('Change photo')
            tc.formfile('edit_photo', 'photo', image)
            tc.submit()
            # Now check that the photo == what we uploaded
            p = Person.objects.get(user__username='paulproteus')
            self.assert_(p.photo.read() ==
                    open(image).read())
    #}}}

class GuessLocationOnLogin(TwillTests):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    mock_ip = mock.Mock()
    mock_ip.return_value = "128.151.2.1"
    @mock.patch("mysite.base.middleware.get_user_ip", mock_ip)
    def test_guess_location_on_login(self):
        person = Person.objects.get(user__username="paulproteus")
        self.assertFalse(person.location_confirmed)
        self.assertFalse(person.location_display_name)
        
        client = self.login_with_client()
        response = client.get(reverse(mysite.profile.views.display_list_of_people))
        self.assertContains(response, "OpenHatch")
        person = Person.objects.get(user__username="paulproteus")
        self.assertEqual(person.location_display_name, "Rochester, NY, United States")
        self.assertContains(response, person.location_display_name)

    def test_yes_response(self):
        person = Person.objects.get(user__username="paulproteus")
        #logging in
        client = self.login_with_client()
        # sending http request to correct page for "yes" response
        response = client.post(reverse(mysite.account.views.confirm_location_suggestion_do))
        #asserting that we get back an http status code of 200
        person = Person.objects.get(user__username="paulproteus")
        self.assertEqual(response.status_code, 200)
        #asserting that database was updated
        self.assertTrue(person.location_confirmed)

    def test_dont_guess_response(self):
        person = Person.objects.get(user__username="paulproteus")
        #logging in
        client = self.login_with_client()
        # sending http request to correct page for "don't guess" response
        response = client.post(reverse(mysite.account.views.dont_guess_location_do))
        #asserting that we get back an http status code of 200
        person = Person.objects.get(user__username="paulproteus")
        self.assertEqual(response.status_code, 200)
        #asserting that database was updated
        self.assertTrue(person.dont_guess_my_location)

    @mock.patch("mysite.base.middleware.get_user_ip", mock_ip)
    def test_no_response(self):
        person = Person.objects.get(user__username="paulproteus")
        #logging in
        client = self.login_with_client()
        # sending http request to correct page for "no" response
        response = client.get(reverse(mysite.account.views.set_location), {'dont_suggest_location': 1})
        person = Person.objects.get(user__username="paulproteus")
        self.assert_(person.location_display_name)
        self.assertNotContains(response, person.location_display_name)

        
        




        
    #}}}

# vim: set nu:
