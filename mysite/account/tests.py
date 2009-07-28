import base.tests 
from base.tests import make_twill_url
from profile.models import Person
from django.contrib.auth.models import User
from twill import commands as tc
from django.contrib.auth import authenticate

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
        tc.follow('Log out')
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
    fixtures = ['profile/user-paulproteus', 'profile/person-paulproteus']

    username = 'ziggy'
    email = 'ziggy@zig.gy'
    password = "ziggy's impregnable passkey"

    def test_create_user_from_front_page(self):
        """This test:
        * Creates a new user
        * Verifies that we are at ziggy's profile page"""
        base.tests.signup_with_twill(
                self.username, self.email, self.password)
        # Should be at ziggy's profile.
        tc.find(self.username)
        tc.find('profile')

    def test_create_duplicate_user_from_front_page(self):
        # The fixtures show that we have paulproteus already
        # registered
        duplicated_username='paulproteus'
        nondup_username='paulproteus2'
        email='pp@openhatch.org'
        password='new password'
        self.twill_signup(duplicated_username, email, password)
        # Should be back at the front page, with a message
        # saying that you need to pick a different username.
        tc.find('username_taken')
        self.twill_signup(nondup_username, email, password)
        tc.find(nondup_username)

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
        tc.find('need_email')
        # }}}

    def sign_up_with_email(self, email_address):
        # {{{
        # Verify there is no user named newuser
        username = 'newuser'
        email = 'new@us.er'
        password = 'password'
        self.assertFalse(list(
            Person.objects.filter(user__username=username)))

        # Try to create one (with email address)
        self.twill_signup(username, email, password)

        users = list(User.objects.filter(username=username))
        return users

        #}}}

    def test_signup_with_good_email_address(self):
        # {{{
        email_address = 'good@email.com'
        users = self.sign_up_with_email(email_address)
        self.assert_(users)
        self.assertEqual(users[0].email, email_address)
        # }}}

    def test_signup_with_bad_email_address(self):
        # {{{
        email_address = 'ThatsNoEmailAddress!'
        users = self.sign_up_with_email(email_address)
        self.assertFalse(users)
        # }}}

    # }}}
