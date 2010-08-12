from django.conf import settings

from ircbot import SingleServerIRCBot

class IrcMissionBot(SingleServerIRCBot):

    def __init__(self):
        SingleServerIRCBot.__init__(self, [settings.IRC_MISSION_SERVER],
            settings.IRC_MISSIONBOT_NICK, settings.IRC_MISSIONBOT_REALNAME)
        self.channel = settings.IRC_MISSION_CHANNEL

    def on_nicknameinuse(self, conn, event):
        conn.nick(conn.get_nickname() + '_')

    def on_welcome(self, conn, event):
        conn.join(self.channel)
