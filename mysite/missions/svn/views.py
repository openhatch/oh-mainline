# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
# Copyright (C) 2010 OpenHatch
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

from mysite.missions.base.views import *
from mysite.missions.svn import forms, controllers

### POST handlers
###
### Forms submit to this, and we use these to validate input and/or
### modify the information stored about the user, such as recording
### that a mission was successfully completed.
@login_required
def resetrepo(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    controllers.SvnRepository(request.user.username).reset()
    controllers.unset_mission_completed(request.user.get_profile(), 'svn_checkout')
    controllers.unset_mission_completed(request.user.get_profile(), 'svn_diff')
    controllers.unset_mission_completed(request.user.get_profile(), 'svn_commit')
    if 'stay_on_this_page' in request.GET:
        return HttpResponseRedirect(reverse(main_page))
    else:
        return HttpResponseRedirect(reverse(checkout))

@login_required
def diff_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['svn_diff_form'] = forms.DiffForm()
    data['svn_diff_error_message'] = ''
    if request.method == 'POST':
        form = forms.DiffForm(request.POST)
        if form.is_valid():
            try:
                controllers.SvnDiffMission.validate_diff_and_commit_if_ok(request.user.username, form.cleaned_data['diff'])
                controllers.set_mission_completed(request.user.get_profile(), 'svn_diff')
                return HttpResponseRedirect(reverse(diff))
            except controllers.IncorrectPatch, e:
                data['svn_diff_error_message'] = str(e)
        data['svn_diff_form'] = form
    return diff(request, data)

@login_required
def checkout_submit(request):
    # Initialize data array and some default values.
    data = {}
    data['svn_checkout_form'] = forms.CheckoutForm()
    data['svn_checkout_error_message'] = ''
    if request.method == 'POST':
        form = forms.CheckoutForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['secret_word'] == controllers.SvnCheckoutMission.get_secret_word(request.user.username):
                controllers.set_mission_completed(request.user.get_profile(), 'svn_checkout')
                return HttpResponseRedirect(reverse(checkout))
            else:
                data['svn_checkout_error_message'] = 'The secret word is incorrect.'
        data['svn_checkout_form'] = form
    return checkout(request, data)

### State manager
class SvnMissionPageState(MissionPageState):
    def __init__(self, request, passed_data):
        super(SvnMissionPageState, self).__init__(request, passed_data, 'Using Subversion')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            repo = controllers.SvnRepository(self.request.user.username)
            data.update({
                'repository_exists': repo.exists(),
                'svn_checkout_done': controllers.mission_completed(person, 'svn_checkout'),
                'svn_diff_done': controllers.mission_completed(person, 'svn_diff'),
                'svn_commit_done': controllers.mission_completed(person, 'svn_commit'),
            })
            if data['repository_exists']:
              data.update({
                'checkout_url': repo.public_trunk_url(),
                'secret_word_file': controllers.SvnCheckoutMission.SECRET_WORD_FILE,
                'file_for_svn_diff': controllers.SvnDiffMission.FILE_TO_BE_PATCHED,
                'new_secret_word': controllers.SvnCommitMission.NEW_SECRET_WORD,
                'commit_username': self.request.user.username,
                'commit_password': repo.get_password()
              })
        return data

### Normal GET handlers. These are usually pretty short.

@view
def main_page(request, passed_data = None):
    state = SvnMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Start page'
    return (request, 'missions/svn/main_page.html',
            state.as_dict_for_template_context())

@view
def long_description(request, passed_data = None):
    state = SvnMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'About Subversion'
    return (request, 'missions/svn/about_svn.html',
            state.as_dict_for_template_context())

@login_required
@view
def checkout(request, passed_data = None):
    state = SvnMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Checking out'
    return (request, 'missions/svn/checkout.html',
            state.as_dict_for_template_context())

@login_required
@view
def diff(request, passed_data = None):
    state = SvnMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Diffing your changes'
    state.mission_step_prerequisite = 'svn_checkout'
    return (request, 'missions/svn/diff.html',
            state.as_dict_for_template_context())

@login_required
@view
def commit(request, passed_data = None):
    state = SvnMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Committing your changes'
    state.mission_step_prerequisite = 'svn_diff'
    return (request, 'missions/svn/commit.html',
            state.as_dict_for_template_context())

@login_required
def commit_poll(request):
    return HttpResponse(simplejson.dumps(controllers.mission_completed(request.user.get_profile(), 'svn_commit')))
