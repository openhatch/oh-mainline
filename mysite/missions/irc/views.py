# This file is part of OpenHatch.
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


from mysite.missions.base import Mission, MissionBaseView
from mysite.missions.base.views import (
    MissionPageState,
    view,
    login_required
)

from mysite.missions.base.view_helpers import (
    mission_completed,
    set_mission_completed,
)

from mysite.missions.irc import forms
from mysite.missions.models import IrcMissionSession

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings

@login_required
@view
def irc_mission(request, passed_data={}):
    data = {
      'this_mission_page_short_name': 'Using IRC',
      'mission_name': 'Using IRC',
      'session_password_form': forms.IrcSessionPasswordForm(),
      'session_password_error_message': '',

      'irc_netname': settings.IRC_MISSION_SERVER_PRETTYNAME,
      'irc_server': settings.IRC_MISSION_SERVER[0],
      'irc_port': settings.IRC_MISSION_SERVER[1],
      'irc_channel': settings.IRC_MISSION_CHANNEL,
      'irc_botnick': settings.IRC_MISSIONBOT_NICK,
    }
    try:
        data['active_session'] = IrcMissionSession.objects.get(person=request.user.get_profile())
    except IrcMissionSession.DoesNotExist:
        data['active_session'] = None
    data.update(passed_data)
    return (request, 'missions/irc/irc.html', data)

@login_required
def irc_session_password_submit(request):
    data = {}
    if request.method == 'POST':
        form = forms.IrcSessionPasswordForm(request.POST)
        if form.is_valid():
            try:
                session = IrcMissionSession.objects.get(nick=form.cleaned_data['nick'])
            except IrcMissionSession.DoesNotExist:
                data['session_password_error_message'] = 'The bot does not see that nick in the channel.'
            else:
                if session.password == form.cleaned_data['password']:
                    session.person = request.user.get_profile()
                    session.save()
                    return HttpResponseRedirect(reverse(irc_mission))
                else:
                    data['session_password_error_message'] = 'The secret words are incorrect.'
        data['session_password_form'] = form
    return irc_mission(request, data)

@view
def about(request, passed_data={}):
    state = IRCMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'About'
    return (request, 'missions/irc/about.html',
            state.as_dict_for_template_context())

@view
def joining(request, passed_data={}):
    state = IRCMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Joining IRC'
    data = state.as_dict_for_template_context()
    return (request, 'missions/irc/joining.html',
            state.as_dict_for_template_context())

@view
def irc_secrets(request, passed_data={}):
    state = IRCMissionPageState(request, passed_data)
    state.this_mission_page_short_name = 'Using irc passwords'
    data = state.as_dict_for_template_context()
    return (request, 'missions/irc/irc_secrets.html',
            state.as_dict_for_template_context())


# State Manager


class IRCMissionPageState(MissionPageState):

    def __init__(self, request, passed_data):
        super(IRCMissionPageState, self).__init__(
            request, passed_data, 'Using IRC')

    def as_dict_for_template_context(self):
        (data, person) = self.get_base_data_dict_and_person()
        if person:
            data.update({
                'irc_joining_done': mission_completed(person, 'irc_joining'),
                'irc_session_password_submit_done': mission_completed(person, 'irc_secrets'),
                })
        return data
