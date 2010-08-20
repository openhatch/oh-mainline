from django.conf import settings
from mysite.missions.models import IrcMissionSession
from mysite.missions.base import controllers

from ircbot import SingleServerIRCBot

class IrcMissionBot(SingleServerIRCBot):

    def __init__(self):
        SingleServerIRCBot.__init__(self, [settings.IRC_MISSION_SERVER],
            settings.IRC_MISSIONBOT_NICK, settings.IRC_MISSIONBOT_REALNAME)
        self.channel = settings.IRC_MISSION_CHANNEL
        self.active_sessions = {}

    def on_nicknameinuse(self, conn, event):
        conn.nick(conn.get_nickname() + '_')

    def on_welcome(self, conn, event):
        conn.join(self.channel)
        IrcMissionSession.objects.all().delete()

    def setup_session(self, nick, conn):
        # Someone has joined the channel.
        password = controllers.make_password()
        IrcMissionSession(nick=nick, password=password).save()
        conn.notice(nick,
          'Hello, %(nick)s! To start the mission, here are the words to type into the mission page: %(password)s'
            % {'nick': nick, 'password': password})

    def destroy_session(self, nick):
        IrcMissionSession.objects.filter(nick=nick).delete()
        if nick in self.active_sessions:
            del self.active_sessions[nick]

    def on_join(self, conn, event):
        nick = event.source().split('!')[0]
        channel = event.target()
        if channel == self.channel and nick != conn.get_nickname():
            self.setup_session(nick, conn)

    def on_namreply(self, conn, event):
        channel = event.arguments()[1]
        nicks = event.arguments()[2].split()
        for nick in nicks:
            if nick[0] in '@+':
                nick = nick[1:]  # remove op/voice prefix
            self.setup_session(nick, conn)

    def on_part(self, conn, event):
        nick = event.source().split('!')[0]
        channel = event.target()
        if channel == self.channel:
            self.destroy_session(nick)

    def on_kick(self, conn, event):
        nick = event.arguments()[0]
        channel = event.target()
        if channel == self.channel:
            self.destroy_session(nick)
