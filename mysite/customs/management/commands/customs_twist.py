from django.core.management.base import BaseCommand
import twisted.web.client
from twisted.internet import reactor
import mysite.customs.profile_importers

import mysite.profile.models

class Command(BaseCommand):
    help = "Call this when you want to run a Twisted reactor."

    def create_tasks_from_dias(self):
        print 'For all DIAs we know how to process with Twisted: enqueue them.'
        for dia in mysite.profile.models.DataImportAttempt.objects.filter(completed=False):
            if dia.source in mysite.customs.profile_importers.SOURCE_TO_CLASS:
                cls = mysite.customs.profile_importers.SOURCE_TO_CLASS[dia.source]
                self.add_dia_to_reactor(cls, dia.query, dia.id)

    def add_dia_to_reactor(self, cls, query, dia_id):
        ### For now, only the 'db' == Debian == qa.debian.org DIAs are in a format where
        ### they can handle asynchronous operation.
        state_manager = cls(query, dia_id)

        ### d is the "deferred" object. We create it using getPage(), and then
        ### we configure its next actions.
        url = state_manager.getUrl()
        d = twisted.web.client.getPage(url)
        d.addCallback(state_manager.handlePageContents)
        d.addErrback(state_manager.handleError)

    def handle(self, *args, **options):
        self.create_tasks_from_dias()
        print 'Starting Reactor...'
        reactor.run()
        print '...reactor finished!'
