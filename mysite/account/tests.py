import base.tests 
from base.tests import make_twill_url
from profile.models import Person

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test.client import Client

from twill import commands as tc

class Login(base.tests.TwillTests):
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
        url = make_twill_url(url)
        tc.go(url)
        tc.fv('login','login_username',"paulproteus")
        tc.fv('login','login_password',"not actually paulproteus's unbreakable password")
        tc.submit()
        tc.find("oops")
    # }}}

class Signup(base.tests.TwillTests):
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

class EditPassword(base.tests.TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def change_password(self, old_pass, new_pass,
            should_succeed = True):
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus'))
        tc.follow('settings')
        tc.find('Change password')
        tc.fv('change_password', 'old_password',
                old_pass)
        tc.fv('change_password', 'new_password1', new_pass)
        tc.fv('change_password', 'new_password2', new_pass)
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

class EditPhoto(base.tests.TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def test_set_avatar(self):
        self.login_with_twill()
        url = 'http://openhatch.org/people/paulproteus/'
        tc.go(make_twill_url(url))
        tc.follow('Change photo')
        tc.formfile('edit_photo', 'photo', 'static/sample-photo.png')
        tc.submit()
        

class LoginWithOpenId(base.tests.TwillTests):
    fixtures = ['user-paulproteus']
    def test_login_creates_user_profile(self):
        # Front page
        url = 'http://openhatch.org/'

        # Even though we didn't add the person-paulproteus
        # fixture, a Person object is created.
        self.assert_(list(
            Person.objects.filter(user__username='paulproteus')))

