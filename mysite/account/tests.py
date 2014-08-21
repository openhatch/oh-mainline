# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 Jessica McKellar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#{{{ imports
import os
import mock
import tempfile
import StringIO
import logging
from webtest import Upload

from mysite.profile.models import Person
import mysite.account.forms
from mysite.search.models import Project, ProjectInvolvementQuestion
import mysite.project.views
import mysite.account.views

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.utils.unittest import skipIf

from django_webtest import WebTest
import mysite.base.depends
#}}}


class Login(WebTest):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_login(self):
        user = authenticate(username='paulproteus',
                            password="paulproteus's unbreakable password")
        self.assert_(user and user.is_active)

    def test_logout_web(self):
        username = 'paulproteus'
        search_page = self.app.get('/search/', user=username)
        response = search_page.click('log out')
        self.assertEqual(response.status_code, 302)

    def test_logout_no_open_redirect(self):
        client = Client()
        # All test cases should redirect to the OpenHatch root.
        # Verify existing logout still behaves as before:
        response  = client.get('/account/logout/?next=/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/')
        # Verify appended redirect url is ignored:
        # Before the fix for issue 952, urlparse() redirected this url to
        # /account/logout/.
        response  = client.get('/account/logout/?next=http://www.example.com')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/')
        # Verify appended redirect url is ignored
        # Before the fix for issue 952, urlparse() redirected this url to
        # example.com.
        response  = client.get('/account/logout/?next=http:///www.example.com')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/')
    # }}}


class ProfileGetsCreatedWhenUserIsCreated(WebTest):

    """django-authopenid only creates User objects, but we need Person objects
    in all such cases. Test that creating a User will automatically create
    a Person in our project."""

    def test_login_creates_person_profile(self):
        # Create a user object
        u = User.objects.create(username='paulproteus')
        u.save()
        # Even though we didn't add the person-paulproteus
        # fixture, a Person object is created.
        self.assert_(list(Person.objects.filter(user__username='paulproteus')))


class Signup(WebTest):

    """ Tests for signup without invite code. """
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_usernames_case_sensitive(self):
        username = 'paulproteus'
        signup_page = self.app.get('/account/signup/')
        signup_form = signup_page.form
        self.assertNotIn('already got a user in our database with that username', signup_form.text)
        signup_form['username'] = 'paulproteus'
        signup_form['email'] = 'someone@somewhere.com'
        signup_form['password1'] = 'blahblahblah'
        signup_form['password2'] = 'blahblahblah'
        response = signup_form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn('already got a user in our database with that username', response.content)

    def test_usernames_case_insensitive(self):
        username = 'paulproteus'
        signup_page = self.app.get('/account/signup/')
        signup_form = signup_page.form
        self.assertNotIn('already got a user in our database with that username', signup_form.text)
        signup_form['username'] = 'PaulProteus'
        signup_form['email'] = 'someone@somewhere.com'
        signup_form['password1'] = 'blahblahblah'
        signup_form['password2'] = 'blahblahblah'
        response = signup_form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn('already got a user in our database with that username', response.content)

    def test_reserved_username(self):
        username = 'paulproteus'
        signup_page = self.app.get('/account/signup/', user=username)
        signup_form = signup_page.form
        self.assertNotIn('That username is reserved.', signup_form.text)
        signup_form['username'] = 'admin'
        signup_form['email'] = 'someone@somewhere.com'
        signup_form['password1'] = 'blahblahblah'
        signup_form['password2'] = 'blahblahblah'
        response = signup_form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn('That username is reserved.', response.content)


class EditPassword(WebTest):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def change_password(self, old_pass, new_pass,
                        should_succeed=True):

        ## Refactored below
        # From a sample user profile page, go into the reset password page
        user = 'paulproteus'
        paulproteus_page = self.app.get('/people/%s/' % (user,), user=user)
        settings_page = paulproteus_page.click("settings", index=0)
        reset_pw_page = settings_page.click("Password", index=0)

        # Change password on the password reset form
        reset_pw_form = reset_pw_page.form
        reset_pw_form['old_password'] = old_pass
        reset_pw_form['new_password1'] = new_pass
        reset_pw_form['new_password2'] = new_pass
        form_response = reset_pw_form.submit()

        # Try to log in with the new password now
        client = Client()
        username = 'paulproteus'
        actual_should_succeed = client.login(username=username, password=new_pass)
        self.assertEqual(actual_should_succeed, should_succeed)

    def test_change_password(self):
        old_pass = "paulproteus's unbreakable password"
        new_pass = 'new'
        self.change_password(old_pass=old_pass, new_pass=new_pass)

    def test_change_password_should_fail(self):
        oldpass = "wrong"
        newpass = 'new'
        self.change_password(oldpass, newpass,
                             should_succeed=False)
#}}}


class EditContactInfo(WebTest):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_edit_email_address(self):
        # Opt out of the periodic emails. This way, the only "checked"
        # checkbox is the one for if the user's email address gets shown.
        user = "paulproteus"
        paulproteus = Person.objects.get()
        paulproteus.email_me_re_projects = False
        paulproteus.save()

        contact_info_page = self.app.get("/account/settings/contact-info/", user=user)
        current_pw = "paulproteus's unbreakable password"
        new_email = 'new@ema.il'

        # Let's first ensure that "new@ema.il" doesn't appear on the page. We're about to add it.
        # Test that the email is initially not visible on user profile page
        paulproteus_page = self.app.get('/people/%s/' % (user,), user=user)
        assert new_email not in paulproteus_page

        # Change email address and make sure it's publicly visible
        contact_info_form = contact_info_page.form
        contact_info_form['edit_email-email'] = new_email
        contact_info_form['show_email-show_email'].checked = True
        contact_info_form.submit()
        self.assertEqual(paulproteus.user.email, new_email)
        # Test that the email is publicly visible on user profile page
        paulproteus_page = self.app.get('/people/%s/' % (user,), user=user)
        assert new_email in paulproteus_page

        # Test that the email is not publicly displayble
        contact_info_page = self.app.get('/account/settings/contact-info/', user=user)
        contact_info_form['show_email-show_email'].checked = False
        contact_info_form.submit()
        # Test that the email is no longer visible on user profile page
        paulproteus_page = self.app.get('/people/%s/' % (user,), user=user)
        assert new_email not in paulproteus_page

photos = [os.path.join(os.path.dirname(__file__),
                       '..', '..', 'sample-photo.' + ext)
          for ext in ('png', 'jpg')]


def photo(f):
    filename = os.path.join(
        os.path.dirname(__file__),
        '..', f)
    assert os.path.exists(filename)
    return filename



@skipIf(not mysite.base.depends.Image, "Skipping photo-related tests because PIL is missing. Look in ADVANCED_INSTALLATION.mkd for information.")
class EditPhoto(WebTest):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def login_with_client(self, username='paulproteus',
                          password="paulproteus's unbreakable password"):
        client = Client()
        success = client.login(username=username,
                               password=password)
        self.assert_(success)
        return client

    def test_set_avatar(self):
        username = 'paulproteus'
        for image in [photo('static/sample-photo.png'),
                      photo('static/sample-photo.jpg')]:
            paulproteus_page = self.app.get('/people/%s/' % (username,), user=username)
            photo_page = paulproteus_page.click(href='/account/edit/photo/')
            photo_form = photo_page.form
            photo_form['photo'] = Upload(image)
            photo_form.submit()

            # Now check that the photo == what we uploaded
            p = Person.objects.get(user__username=username)
            self.assert_(p.photo.read() == open(image).read())

            response = self.login_with_client().get(
                reverse(mysite.account.views.edit_photo))
            self.assertEqual(response.context[0]['photo_url'], p.photo.url,
                             "Test that once you've uploaded a photo via the photo editor, "
                             "the template's photo_url variable is correct.")
            self.assert_(p.photo_thumbnail)
            thumbnail_as_stored = mysite.base.depends.Image.open(
                p.photo_thumbnail.file)
            w, h = thumbnail_as_stored.size
            self.assertEqual(w, 40)

    def test_set_avatar_too_wide(self):
        username = 'paulproteus'
        for image in [photo('static/images/too-wide.jpg'),
                      photo('static/images/too-wide.png')]:
            paulproteus_page = self.app.get('/people/%s/' % (username,), user=username)
            photo_page = paulproteus_page.click(href='/account/edit/photo/')
            photo_form = photo_page.form
            photo_form['photo'] = Upload(image)
            photo_form.submit()

            # Now check that the photo is 200px wide
            p = Person.objects.get(user__username=username)
            image_as_stored = mysite.base.depends.Image.open(p.photo.file)
            w, h = image_as_stored.size
            self.assertEqual(w, 200)

    def test_invalid_photo(self):
        """
        If the uploaded image is detected as being invalid, report a helpful
        message to the user. The photo is not added to the user's profile.
        """
        username = 'paulproteus'
        bad_image = tempfile.NamedTemporaryFile(delete=False)

        try:
            bad_image.write("garbage")
            bad_image.close()

            paulproteus_page = self.app.get('/people/%s/' % (username,), user=username)
            photo_page = paulproteus_page.click(href='/account/edit/photo/')
            photo_form = photo_page.form
            photo_form['photo'] = Upload(bad_image.name)
            form_response = photo_form.submit()
            self.assertEqual(form_response.status_code, 200)
            self.assertIn("The file you uploaded was either not an image or a corrupted image", form_response.content)

            # Test that user test object has no photo attribute
            p = Person.objects.get(user__username=username)
            self.assertFalse(p.photo.name)
        finally:
            os.unlink(bad_image.name)


@skipIf(not mysite.base.depends.Image, "Skipping photo-related tests because PIL is missing. Look in ADVANCED_INSTALLATION.mkd for information.")
class EditPhotoWithOldPerson(WebTest):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus-with-blank-photo']

    def test_set_avatar(self):
        username = 'paulproteus'
        for image in (photo('static/sample-photo.png'), photo('static/sample-photo.jpg')):
            paulproteus_page = self.app.get('/people/paulproteus/', user=username)
            photo_page= paulproteus_page.click(href='/account/edit/photo')
            photo_form = photo_page.form
            photo_form['photo'] = Upload(image)
            photo_response = photo_form.submit()

        # Now check that the photo == what we uploaded
        p = Person.objects.get(user__username=username)
        self.assert_(p.photo.read() == open(image).read())


class SignupWithNoPassword(WebTest):

    def test(self):
        POST_data = {'username': 'mister_roboto'}
        response = self.client.post(
            reverse(mysite.account.views.signup_do), POST_data)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(User.objects.count(), 0)


class LoginPageContainsUnsavedAnswer(WebTest):

    def test(self):
        # Create an answer whose author isn't specified. This replicates the
        # situation where the user isn't logged in.
        p = Project.create_dummy(name='Myproject')
        q = ProjectInvolvementQuestion.create_dummy(
            key_string='where_to_start', is_bug_style=False)

        # Do a GET on the project page to prove cookies work.
        self.client.get(p.get_url())

        # POST some text to the answer creation post handler
        POST_data = {
            'project__pk': p.pk,
            'question__pk': q.pk,
                'answer__text': """Help produce official documentation, share the solution to a problem, or check, proof and test other documents for accuracy.""",
        }
        response = self.client.post(
            reverse(mysite.project.views.create_answer_do), POST_data,
            follow=True)

        # Now, the session will know about the answer, but the answer will not be published.
        # Visit the login page, assert that the page contains the text of the
        # answer.

        response = self.client.get(reverse('oh_login'))
        self.assertContains(response, POST_data['answer__text'])


class ClearSessionsOnPasswordChange(WebTest):
    fixtures = ['user-paulproteus']

    def user_logged_in(self, session):
        return '_auth_user_id' in session

    def test(self):
        client1 = Client()
        client2 = Client()

        username = "paulproteus"
        password = "paulproteus's unbreakable password"
        new_password = "new password"

        client1.login(username=username, password=password)
        client2.login(username=username, password=password)

        self.assertTrue(self.user_logged_in(client1.session))
        self.assertTrue(self.user_logged_in(client2.session))

        client1.post(reverse(mysite.account.views.change_password_do),
                     data={
                         'old_password': password, 'new_password1': new_password,
                         'new_password2': new_password})

        self.assertTrue(self.user_logged_in(client1.session))
        self.assertFalse(self.user_logged_in(client2.session))


# vim: set nu:
