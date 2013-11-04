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
import mock
import tempfile
import StringIO
import logging
from django.utils.unittest.case import skip

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
from django.utils.unittest import skipIf

from twill import commands as tc
import mysite.base.depends
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

class ProfileGetsCreatedWhenUserIsCreated(TwillTests):
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

@skip("Email address is edited in different place now")
class EditContactInfo(TwillTests):
    #{{{
    fixtures = ['user-paulproteus', 'person-paulproteus']
    def test_edit_email_address(self):
        # Opt out of the periodic emails. This way, the only "checked"
        # checkbox is the one for if the user's email address gets shown.
        paulproteus = Person.objects.get()
        paulproteus.email_me_re_projects = False
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
        tc.submit()

        # Form submission ought to redirect us back to the form.
        tc.url(url)

        # Was email successfully edited? 
        tc.find(email)

        # And does the email address show up on the profile?
        tc.go(make_twill_url(
                'http://openhatch.org/people/paulproteus'))
        tc.find(email)

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

@skipIf(not mysite.base.depends.Image, "Skipping photo-related tests because PIL is missing. Look in ADVANCED_INSTALLATION.mkd for information.")
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
            thumbnail_as_stored = mysite.base.depends.Image.open(p.photo_thumbnail.file)
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
            image_as_stored = mysite.base.depends.Image.open(p.photo.file)
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

@skipIf(not mysite.base.depends.Image, "Skipping photo-related tests because PIL is missing. Look in ADVANCED_INSTALLATION.mkd for information.")
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
    @skipIf(not mysite.profile.view_helpers.geoip_city_database_available(), "Skipping because high-resolution GeoIP data not available.")
    @mock.patch("mysite.base.middleware.get_user_ip", mock_ip)
    def test_guess_location_on_accessing_edit_location_form(self):
        person = Person.objects.get(user__username="paulproteus")
        self.assertFalse(person.location_confirmed)
        self.assertEqual('Inaccessible Island',
                         person.get_public_location_or_default())

        client = self.login_with_client()
        response = client.get(reverse(mysite.account.views.set_location))
        self.assertContains(response, "OpenHatch")
        person = Person.objects.get(user__username="paulproteus")
        self.assertContains(response, "Rochester, NY, United States")

    mock_ip = mock.Mock()
    mock_ip.return_value = "128.151.2.1" # Located in Rochester, New York, U.S.A.
    @skipIf(not mysite.profile.view_helpers.geoip_city_database_available(), "Skipping because high-resolution GeoIP data not available.")
    @mock.patch("mysite.base.middleware.get_user_ip", mock_ip)
    def test_do_not_guess_if_have_location_set(self):
        person = Person.objects.get(user__username="paulproteus")
        person.location_display_name = 'The White House'
        person.latitude=38.898748
        person.longitude=-77.037684
        person.location_confirmed = True
        person.save()

        client = self.login_with_client()
        response = client.get(reverse(mysite.account.views.set_location))
        self.assertContains(response, "OpenHatch")
        person = Person.objects.get(user__username="paulproteus")
        self.assertNotContains(response, "Rochester, NY, United States")
        self.assertContains(response, "The White House")

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

    #}}}

class ClearSessionsOnPasswordChange(TwillTests):
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
                data={'old_password': password, 'new_password1': new_password,
                    'new_password2': new_password})

        self.assertTrue(self.user_logged_in(client1.session))
        self.assertFalse(self.user_logged_in(client2.session))


# vim: set nu:
