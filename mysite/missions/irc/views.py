from mysite.base.decorators import view
from mysite.missions.irc import forms
from mysite.missions.models import IrcMissionSession

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
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
