from django.core.management import BaseCommand, CommandError
from mysite.missions.irc.ircmissionbot import IrcMissionBot

class Command(BaseCommand):
    args = ''
    help = 'IRC bot for IRC missions'

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError, 'This command does not take arguments.'

        IrcMissionBot().start()
