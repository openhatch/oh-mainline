# This file is part of OpenHatch.
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
import Image
import mock
import tempfile
import StringIO
import logging

from mysite.profile.models import Person
from mysite.base.tests import make_twill_url, TwillTests
import mysite.account.forms
from mysite.search.models import Project, ProjectInvolvementQuestion
import mysite.project.views
import mysite.account.views

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test.client import Client
from django.core.urlresolvers import reverse

from twill import commands as tc
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
        tc.notfind('log in')
        tc.follow('log out')
        tc.find('log in')
    # }}}

class LoginWithOpenID(TwillTests):
    #{{{
    fixtures = ['user-paulproteus']
    def test_login_creates_user_profile(self):
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
        # Opt out of the weekly emails. This way, the only "checked"
        # checkbox is the one for if the user's email address gets shown.
        paulproteus = Person.objects.get()
        paulproteus.email_me_weekly_re_projects = False
        paulproteus.save()

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
            tc.follow('photo')
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
            tc.follow('photo')
            tc.formfile('edit_photo', 'photo', image)
            tc.submit()
            # Now check that the photo is 200px wide
            p = Person.objects.get(user__username='paulproteus')
            image_as_stored = Image.open(p.photo.file)
            w, h = image_as_stored.size
            self.assertEqual(w, 200)

    def test_invalid_photo(self):
        """
        If the uploaded image is detected as being invalid, report a helpful
        message to the user. The photo is not added to the user's profile.
        """
        bad_image = tempfile.NamedTemporaryFile(delete=False)
        self.login_with_twill()

        try:
            bad_image.write("garbage")
            bad_image.close()

            tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
            tc.follow('photo')
            tc.formfile('edit_photo', 'photo', bad_image.name)
            tc.submit()
            tc.code(200)
            self.assert_("The file you uploaded was either not an image or a "
                         "corrupted image" in tc.show())

            p = Person.objects.get(user__username='paulproteus')
            self.assertFalse(p.photo.name)
        finally:
            os.unlink(bad_image.name)

    def test_image_processing_library_error(self):
        """
        If the image processing library errors while preparing a photo, report a
        helpful message to the user and log the error. The photo is not added
        to the user's profile.
        """
        # Get a copy of the error log.
        string_log = StringIO.StringIO()
        logger = logging.getLogger()
        my_log = logging.StreamHandler(string_log)
        logger.addHandler(my_log)
        logger.setLevel(logging.ERROR)

        self.login_with_twill()
        tc.go(make_twill_url('http://openhatch.org/people/paulproteus/'))
        tc.follow('photo')
        # This is a special image from issue166 that passes Django's image
        # validation tests but causes an exception during zlib decompression.
        tc.formfile('edit_photo', 'photo', photo('static/images/corrupted.png'))
        tc.submit()
        tc.code(200)

        self.assert_("Something went wrong while preparing this" in tc.show())
        p = Person.objects.get(user__username='paulproteus')
        self.assertFalse(p.photo.name)

        # an error message was logged during photo processing.
        self.assert_("zlib.error" in string_log.getvalue())
        logger.removeHandler(my_log)

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
            tc.follow('photo')
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
    mock_ip.return_value = "128.151.2.1" # Located in Rochester, New York, U.S.A.
    @mock.patch("mysite.base.middleware.get_user_ip", mock_ip)
    def test_guess_location_on_login(self):
        person = Person.objects.get(user__username="paulproteus")
        self.assertFalse(person.location_confirmed)
        self.assertFalse(person.location_display_name)
        
        client = self.login_with_client()
        response = client.get(reverse(mysite.profile.views.people))
        self.assertContains(response, "OpenHatch")
        person = Person.objects.get(user__username="paulproteus")
        self.assertEqual(person.location_display_name, "Rochester, NY, United States")

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

class SignupWithNoPassword(TwillTests):
    def test(self):
        POST_data = {'username': 'mister_roboto'}
        response = self.client.post(reverse(mysite.account.views.signup_do), POST_data)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(User.objects.count(), 0)

class LoginPageContainsUnsavedAnswer(TwillTests):
    
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
        response = self.client.post(reverse(mysite.project.views.create_answer_do), POST_data,
                                    follow=True)

        # Now, the session will know about the answer, but the answer will not be published.
        # Visit the login page, assert that the page contains the text of the answer.

        response = self.client.get(reverse('oh_login'))
        self.assertContains(response, POST_data['answer__text'])

# vim: set nu:
