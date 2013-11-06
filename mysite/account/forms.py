# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010 OpenHatch, Inc.
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

import django.contrib.auth.forms
from django.contrib.auth.models import User
import django.forms
from mysite.profile.models import Person, FormQuestion, CardDisplayedQuestion, ListDisplayedQuestion
import StringIO
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import InMemoryUploadedFile
import logging
import mysite.base.depends

RESERVED_USERNAMES =  (
        'admin',
        'anonymous',
        'sufjan',
        'Spam cleanup script',
        )

class InsertVolunteerForm(django.forms.Form):
    first_name = django.forms.CharField()
    last_name = django.forms.CharField()
    email = django.forms.EmailField()
    company_event_organization = django.forms.CharField()
    hfoss_organizations_that_interest_you = django.forms.MultipleChoiceField()
    causes_you_want_to_contribute_to = django.forms.MultipleChoiceField()
    how_much_time_would_you_like_to_commit_to_volunteering = django.forms.CharField()
    skills = django.forms.MultipleChoiceField()
    linkedin_profile_url = django.forms.CharField()
    have_you_previously_contributed_to_open_source_projects = django.forms.CharField()
    github_profile___username = django.forms.CharField()
    google_code = django.forms.CharField()
    other = django.forms.CharField()
    languages = django.forms.MultipleChoiceField()
    Experience_level = django.forms.CharField()
    what_languages = django.forms.CharField()
    how_did_you_hear_about_socialcoding4good = django.forms.MultipleChoiceField()
    yes = django.forms.CharField()
    comments = django.forms.CharField()

class UserCreationFormWithEmail(django.contrib.auth.forms.UserCreationForm):
    username = django.forms.RegexField(label="Username", max_length=30, regex=r'^\w+$',
        help_text = "<span class='help_text'>Pick a username with length < 31 characters. Stick to letters, digits and underscores.</span>",
        error_messages = {'invalid': "Stick to letters, digits and underscores.", 'required': "Gotta pick a username!"})
    email = django.forms.EmailField(error_messages={
        'required': "Your email address is required. We promise to use it respectfully.",
        'invalid': "This email address looks fishy. Real, or malarkey?"})
    class Meta:
        model = django.contrib.auth.models.User
        fields = ('username', 'email', 'password1')

    def __init__(self, *args, **kw):
        super(django.contrib.auth.forms.UserCreationForm,
                self).__init__(*args, **kw)

        custom_error_messages = {}
        custom_error_messages_dict = {
                "A user with that username already exists.": "Oops, we've already got a user in our database with that username. Pick another one!",
                "A user with that email already exists.": "We've already got a user in our database with that email address. Have you signed up before?",
                }

        for fieldname in self.errors:
            for index, error_text in enumerate(self.errors[fieldname]):
                uet = unicode(error_text)
                self.errors[fieldname][index] = custom_error_messages_dict.get(uet, uet)

    def clean_username(self):
        username = super(UserCreationFormWithEmail, self).clean_username()
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            if username not in RESERVED_USERNAMES:
                return username
            raise django.forms.ValidationError(
                "That username is reserved.")
        raise django.forms.ValidationError(
            "A user with that username already exists.")

    def clean_email(self):
        """Verify that their email is unique."""
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise django.forms.ValidationError(
            "A user with that email already exists.")

class ShowEmailForm(django.forms.Form):
    show_email = django.forms.BooleanField(required=False, label="Make email publicly visible?")

class EditEmailForm(django.forms.ModelForm):
    class Meta:
        model = django.contrib.auth.models.User
        fields = ('email',)

    def clean_email(self):
        """Verify that their email is unique."""
        email = self.cleaned_data["email"]
        other_users_with_this_email = list(
                User.objects.filter(email=email).exclude(
                    username=self.instance.username))
        if not other_users_with_this_email:
            return email
        else:
            raise django.forms.ValidationError(
                "A user with that email already exists.")

class EditLocationForm(django.forms.ModelForm):
    class Meta:
        model = Person
        fields = ('location_display_name',)
    def clean_location_display_name(self):
        address = self.cleaned_data['location_display_name'].strip()
        # Synchronously try to geocode it. This will prime the cache, and
        # make sure the geocoding would succeed, so this method does not
        # have to be the one to store it.
        try:
            mysite.base.view_helpers.cached_geocoding_in_json(address)
        except Exception:
            logging.exception("When geocoding, caught an exception")
            raise django.forms.ValidationError(
                "An error occurred while geocoding. Make sure the address is a valid place. If you think this is our error, contact us.")
        return address

class EditNameForm(django.forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username')

class EditPhotoForm(django.forms.ModelForm):
    class Meta:
        model = Person
        fields = ('photo',)
    
    def clean_photo(self):
        ### If PIL is missing, proceed by providing the default
        ### profile image.
        if not mysite.base.depends.Image:
            ## FIXME This is fail-safe, not fail-secure, behavior.
            ## If an image is too big, and the Python Imaging Library
            ## is not installed, we simply do not resize it.E
            logging.info("NOTE: We cannot resize this image, so we are going to pass it through. See ADVANCED_INSTALLATION.mkd for information on PIL.")
            return self.cleaned_data['photo']

        # Safe copy of data...
        self.cleaned_data['photo'].seek(0)
        data = self.cleaned_data['photo'].read()
        self.cleaned_data['photo'].seek(0)
        data_fd = StringIO.StringIO(data)

        w, h = get_image_dimensions(data_fd)
        if w > 200:
            # Scale it down.
            too_big = mysite.base.depends.Image.open(StringIO.StringIO(data))
            format = too_big.format
            new_w = int(200)
            new_h = int((h * 1.0 / w) * 200)

            smaller = too_big.resize((new_w, new_h),
                                     mysite.base.depends.Image.ANTIALIAS)

            # "Save" it to memory
            new_image_fd = StringIO.StringIO()
            smaller.save(new_image_fd, format=format)
            new_image_fd.seek(0)

            old = self.cleaned_data['photo']

            new_image_uploaded_file = InMemoryUploadedFile(
                new_image_fd, '', old.name,
                old.content_type, new_image_fd.len, old.charset)

            # Modify the self.cleaned_data[]
            self.cleaned_data['photo'] = new_image_uploaded_file
        return self.cleaned_data['photo']

class SignUpIfYouWantToHelpForm(django.forms.Form):
    how_should_people_contact_you = django.forms.ChoiceField(
            initial='forwarder',
            widget=django.forms.RadioSelect,
            label="You've expressed interest in helping out a project. How can people from that project contact you?",
            choices=(
                ('forwarder', 'By email, but mask my email address using an automatic forwarder (like Craigslist)'),
                ('public_email', 'By email; just display my real email address'),
                ))

class EmailMeForm(django.forms.ModelForm):
    class Meta:
        model = Person
        fields = ('email_me_re_projects',)


class EditFieldsForm(django.forms.Form):
    questions = []

    def __init__(self, *args, **kwargs):
        self.questions = FormQuestion.objects.all()
        super(EditFieldsForm, self).__init__(*args, **kwargs)

        for question in self.questions:
            self.fields['question_%s' % question.id] = django.forms.CharField(label=question.display_name,
                                                                              max_length=100,
                                                                              min_length=1,
                                                                              required=True,
                                                                              initial=question.display_name)


class EditFieldsDisplayedInSearchForm(django.forms.Form):
    questions = []
    displayed_fields = []
    type = None

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop(u'user')
        self.questions = FormQuestion.objects.all()
        self.type = kwargs.pop(u'type')
        if self.type == 'cards':
            self.displayed_fields = CardDisplayedQuestion.objects.filter(person__user__pk=self.user.id)
        else:
            self.displayed_fields = ListDisplayedQuestion.objects.filter(person__user__pk=self.user.id)
        super(EditFieldsDisplayedInSearchForm, self).__init__(*args, **kwargs)

        choices = [(question.id, question.display_name) for question in self.questions]
        initial = [field.question.id for field in self.displayed_fields]
        self.fields['questions_%s' % self.type] = django.forms.MultipleChoiceField(widget=django.forms.CheckboxSelectMultiple,
                                                                                   choices=choices,
                                                                                   initial=initial,
                                                                                   required=False)
