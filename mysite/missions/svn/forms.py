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

from django import forms

from mysite.missions.base.view_helpers import get_mission_data_path
from mysite.missions.svn import view_helpers


class CheckoutForm(forms.Form):
    """
    A form for the svn mission's 'checkout repo' step to see if the user
    correctly checked out the svn repo and its files
    """
    SECRET_WORD_FILE = 'word.txt'

    secret_word = forms.CharField(
        error_messages={'required': 'No secret word was given.'}
    )

    def __init__(self, username=None, *args, **kwargs):
        """ Initialize checkout form and set username """
        super(CheckoutForm, self).__init__(*args, **kwargs)
        self.username = username

    def clean_secret_word(self):
        """
        Gets secret word from svn trunk and checks if user submitted
        word is the same. Raise error if the words do not match
        """
        secret_word_trunk = view_helpers.SvnRepository(self.username).cat('/trunk/' + self.SECRET_WORD_FILE).strip()
        if self.cleaned_data['secret_word'] != secret_word_trunk:
            raise forms.ValidationError('The secret word is incorrect.')


class DiffForm(forms.Form):
    """
    A form for the svn mission's 'diff' step to see if the user creates the
    correct `diff` output
    """
    FILE_TO_BE_PATCHED = 'README'
    NEW_CONTENT = os.path.join(get_mission_data_path('svn'),
                               'README-new-for-svn-diff')

    diff = forms.CharField(
        error_messages={'required': 'No svn diff output was given.'},
        widget=forms.Textarea()
    )

    def __init__(self, username=None, working_directory=None, request=None, *args, **kwargs):
        """ Initialize diff form """
        super(DiffForm, self).__init__(request, *args, **kwargs)

        self.username = username
        self.working_directory = working_directory
        if working_directory:
            self.file_to_patch = os.path.join(working_directory, self.FILE_TO_BE_PATCHED)

        # Initialize proposed_patch and proposed_content
        self.proposed_patch = None
        self.proposed_content = None

    def clean_diff(self):
        """
        Clean and validate the proposed patch contents of the `diff` form.
        This function will be invoked by django.form.Forms.is_valid(), and
        will raise the exception ValidationError
        """
        self.proposed_patch = patch.fromstring(self.cleaned_data['diff'])

        # Check that proposed patch affects the correct number of files
        if len(self.proposed_patch.hunks) != 1:
            raise forms.ValidationError('The patch affects more than one file.')

        # Check that proposed patch has the correct filename.
        if (self.file_to_patch != self.FILE_TO_BE_PATCHED) or (self.file_to_patch.target[0] != self.FILE_TO_BE_PATCHED):
            raise forms.ValidationError('The patch affects the wrong file.')

        # Get a mission user's working copy of the svn repo
        repo = view_helpers.SvnRepository(self.username)
        svn_checkout_command = ['svn', 'co', repo.file_trunk_url(), self.working_directory]
        view_helpers.subproc_check_output(svn_checkout_command)

        # Check if proposed patch will apply correctly to the working copy.
        if not self.proposed_patch._match_file_hunks(self.file_to_patch, self.proposed_patch.hunks[0]):
            raise forms.ValidationError('The patch will not apply correctly to the latest revision.')

        # Check that the resulting file matches what is expected.
        self.proposed_content = ''.join(self.proposed_patch.patch_stream(open(self.file_to_patch), self.proposed_patch.hunks[0]))
        if self.proposed_content != open(self.NEW_CONTENT).read():
            raise forms.ValidationError('The file resulting from patching does not have the correct contents.')

    def commit_diff(self):
        """ Commit the proposed patch to the mission user's svn repo. """
        open(self.file_to_patch, 'w').write(self.proposed_content)
        commit_message = "Fix a typo in {0:s}. Thanks for reporting this, {1:s}!".format(self.file_to_patch, self.username)
        svn_commit_command = ['svn', 'commit', '-m', commit_message, '--username', 'mr_bad', self.working_directory]
        view_helpers.subproc_check_output(svn_commit_command)
