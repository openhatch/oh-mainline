from django.core.management.base import BaseCommand
from twisted.internet import reactor

import mysite.profile.models

class Command(BaseCommand):
    help = "Call this when you want to run a Twisted reactor."

    def create_tasks_from_dias(self):
        print 'Creating Deferreds from DIAs, and jamming them into the reactor...'
        for dia in mysite.profile.models.DataImportAttempt.objects.filter(completed=False):
            self.add_dia_to_reactor(dia)

    def add_dia_to_reactor(self, dia):
        pass

    def handle(self, *args, **options):
        self.create_tasks_from_dias()
        print 'Starting Reactor...'
        reactor.run()
        print '...reactor finished!'
