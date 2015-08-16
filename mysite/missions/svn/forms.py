# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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

import os
import patch

from django.forms import Form, ValidationError

from mysite.missions.base.view_helpers import get_mission_data_path
from mysite.missions.svn import view_helpers


class CheckoutForm(Form):
    """
    Mission form for checkout step to see if a user corrrectly checked out
    the svn repo
    """
    secret_word = django.forms.CharField(
        error_messages={'required': 'No secret word was given.'}
    )
    SECRET_WORD_FILE = 'word.txt'

    def __init__(self, username=None, *args, **kwargs):
        """ Initalize checkout form and set username """
        super(CheckoutForm, self).__init__(*args, **kwargs)
        self.username = username

    def clean_secret_word(self):
        """
        Gets secret word from svn trunk and checks if user submitted
        word is the same. Raise error if the words do not match
        """
        secret_word_trunk = view_helpers.SvnRepository(self.username).cat('/trunk/' + self.SECRET_WORD_FILE).strip()
        if self.cleaned_data['secret_word'] != secret_word_trunk:
            raise ValidationError, 'The secret word is incorrect.'


class DiffForm(Form):
    """
    Mission step's form to see if a user's svn diff is correct
    """
    diff = django.forms.CharField(
        error_messages={'required': 'No svn diff output was given.'},
        widget=django.forms.Textarea()
    )
    FILE_TO_BE_PATCHED = 'README'
    NEW_CONTENT = os.path.join(get_mission_data_path('svn'),
                               'README-new-for-svn-diff')

    def __init__(self, username=None, wcdir=None, request=None,
                 *args, **kwargs):
        super(DiffForm, self).__init__(request, *args, **kwargs)

        self.username = username
        self.wcdir = wcdir
        if wcdir:
            self.file_to_patch = os.path.join(wcdir, self.FILE_TO_BE_PATCHED)
        self.the_patch = None
        self.new_content = None

    def clean_diff(self):
        """
        Validate the diff form.
        This function will be invoked by django.form.Forms.is_valid(), and
        will raise the exception ValidationError
        """
        self.the_patch = patch.fromstring(self.cleaned_data['diff'])
        # Check that the submitted diff patches the correct number of files
        if len(self.the_patch.hunks) != 1:
            raise ValidationError, 'The patch affects more than one file.'

        # Check that the filename it patches is correct.
        if self.FILE_TO_BE_PATCHED not in self.cleaned_data['diff']:
            raise ValidationError, 'The patch affects the wrong file.'

        # Now we need to generate a working copy to apply the patch to.
        # We can also use this working copy to commit the patch if it's OK.
        repo = view_helpers.SvnRepository(self.username)
        view_helpers.subproc_check_output(
            ['svn', 'co', repo.file_trunk_url(), self.wcdir])

        # Check that it will apply correctly to the working copy.
        if not self.the_patch._match_file_hunks(self.file_to_patch, self.the_patch.hunks[0]):
            raise ValidationError, 'The patch will not apply correctly to the lastest revision.'

        # Check that the resulting file matches what is expected.
        self.new_content = ''.join(
            self.the_patch.patch_stream(open(self.file_to_patch), self.the_patch.hunks[0]))
        if self.new_content != open(self.NEW_CONTENT).read():
            raise ValidationError, 'The file resulting from patching does not have the correct contents.'

    def commit_diff(self):
        """ Commit the diff form and the patch. """
        open(self.file_to_patch, 'w').write(self.new_content)
        commit_message = '''Fix a typo in %s. Thanks for reporting this, %s!''' % (self.FILE_TO_BE_PATCHED, self.username)
        view_helpers.subproc_check_output(['svn', 'commit', '-m', commit_message, '--username', 'mr_bad', self.wcdir])
