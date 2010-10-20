from django.core.management.base import BaseCommand
from twisted.internet import reactor

class Command(BaseCommand):
    help = "Call this when you want to run a Twisted reactor."

    def handle(self, *args, **options):
        print 'Starting Reactor...'
        reactor.run()
        print '...reactor finished!'
