#{{{ imports
import os
import Image

from mysite.profile.models import Person
from mysite.base.tests import make_twill_url, TwillTests
from mysite.profile.models import Person
import mysite.account.views

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test.client import Client
from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse

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
        url = 'http://openhatch.org/'
        url = make_twill_url(url)
        tc.go(url)
        tc.fv('login','login_username',"paulproteus")
        tc.fv('login','login_password',"paulproteus's unbreakable password")
        tc.submit()
        tc.find('paulproteus')

    def test_logout_web(self):
        self.test_login_web()
        url = 'http://openhatch.org/search/'
        url = make_twill_url(url)
        tc.go(url)
        tc.follow('log out')
        tc.find('ciao')

    def test_login_bad_password_web(self):
        url = 'http://openhatch.org/'
        tc.go(make_twill_url('http://openhatch.org/account/logout'))
        url = make_twill_url(url)
        tc.go(url)
        tc.fv('login','login_username',"paulproteus")
        tc.fv('login','login_password',"not actually paulproteus's unbreakable password")
        tc.submit()
        tc.notfind('is_authenticated indeed')
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
        # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    username = 'ziggy'
    email = 'ziggy@zig.gy'
    password = "ziggy's impregnable passkey"

    def test_create_user_from_front_page(self):
        """This test:
        * Creates a new user
        * Verifies that we are at ziggy's profile page"""
        self.signup_with_twill(
                self.username, self.email, self.password)
        # Should be at ziggy's profile.
        tc.find(self.username)
        tc.find('profile')

    def test_create_duplicate_user_from_front_page(self):
        # The fixtures show that we have paulproteus already
        # registered
        duplicated_username='paulproteus'
        email='pp@openhatch.org'
        password='new password'

        # There's already somebody with this username.
        User.objects.get(username=duplicated_username)

        # Try to sign up.
        self.signup_with_twill(duplicated_username, email, password)

        # Assert there's still only one user with this username.
        User.objects.get(username=duplicated_username)

    def test_signup_on_front_page_lets_person_sign_back_in(self):
        ''' The point of this test is to: * Create the account for ziggy * Log out * Log back in as him '''
        self.test_create_user_from_front_page()
        tc.follow('logout')
        tc.go(make_twill_url('http://openhatch.org/'))
        tc.fv('login', 'login_username', self.username)
        tc.fv('login', 'login_password', self.password)
        tc.submit()
        # Should be back at ziggy's profile
        tc.find(self.username)
        tc.find('profile')

    def test_signing_up_forces_email_address_setting(self):
        # {{{
        # Verify there is no user named newuser
        username = 'newuser'
        password = 'password'
        self.assertFalse(list(
            Person.objects.filter(user__username=username)))

        # Try to create a user, emaillessly
        tc.go(make_twill_url('http://openhatch.org/'))
        tc.fv('create_profile', 'username', username)
        tc.fv('create_profile', 'password', password)
        tc.submit()

        # Still false! You need an email address.
        self.assertFalse(list(
            Person.objects.filter(user__username=username)))
        # }}}

    def signup_with_email(self, email):
        # {{{
        # Verify there is no user named newuser
        username = 'newuser'
        password = 'password'
        self.assertFalse(list(
            Person.objects.filter(user__username=username)))

        # Try to create one (with email address)
        self.signup_with_twill(username, email, password)

        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        # }}}

    def test_signup_with_good_email_address(self):
        # {{{
        email_address = 'good@email.com'
        user = self.signup_with_email(email_address)
        self.assert_(user)
        self.assertEqual(user.email, email_address)
        # }}}

    def test_signup_with_bad_email_address(self):
        # {{{
        email_address = 'ThatsNoEmailAddress!'
        user = self.signup_with_email(email_address)
        self.assertFalse(user)
        # }}}

    # }}}

class EditPassword(TwillTests):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def change_password(self, old_pass, new_pass,
            should_succeed = True):
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus'))
        tc.follow('settings')
        tc.follow('Change your password')
        tc.url('/account/settings/password')

        tc.find('Change password')
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

        tc.notfind('checked="checked"')
        tc.notfind(email)

        # Edit email
        tc.fv(1, 'edit_email-email', email)
        # Show email
        tc.fv(1, 'show_email-show_email', '1') # [1]
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
        tc.fv(1, 'show_email-show_email', '0') # [1]
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
        for image in [photo('static/sample-photo.png'),
                      photo('static/sample-photo.jpg')]:
            self.login_with_twill()
            url = 'http://openhatch.org/people/paulproteus/'
            tc.go(make_twill_url(url))
            tc.follow('Change photo')
            tc.formfile('edit_photo', 'photo', image)
            tc.submit()
            # Now check that the photo == what we uploaded
            p = Person.objects.get(user__username='paulproteus')
            self.assert_(p.photo.read() ==
                         open(image).read())

    def test_set_avatar_too_wide(self):
        for image in [photo('static/images/too-wide.jpg'),
                      photo('static/images/too-wide.png')]:
            self.login_with_twill()
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
        for image in (photo('static/sample-photo.png'),
                      photo('static/sample-photo.jpg')):
            self.login_with_twill()
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

class SignupRequiresInvite(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        settings.INVITE_MODE = True

    def tearDown(self):
        settings.INVITE_MODE = False

    def test_signup_without_invite(self):
        client = Client()
        r = client.post(reverse(mysite.account.views.signup_do),
                        {'username': 'bob',
                         'email': 'new@ema.il',
                         'password1': 'newpassword'})
        # watch it fail
        self.assertFalse(list(User.objects.filter(username='bob')))

    def test_signup_with_invite(self):
        # Make a good invite code from paulproteus.
        invite_code = InvitationKey.objects.create_invitation(
            User.objects.get(username='paulproteus')).key
        client = Client()
        r = client.post(reverse(mysite.account.views.signup_do),
                        {'username': 'bob',
                         'email': 'new@ema.il',
                         'password1': 'newpassword',
                         'invite_code': invite_code})
        # watch it succeed
        self.assert_(list(User.objects.filter(username='bob')))

# vim: set nu:
