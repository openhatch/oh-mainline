from django.core.management.base import BaseCommand
from twisted.web.client import getPage
from twisted.internet import reactor
import mysite.customs.profile_importers

import mysite.profile.models

class Command(BaseCommand):
    help = "Call this when you want to run a Twisted reactor."

    def create_tasks_from_dias(self):
        print 'For all Debian QA dias, enqueue them.'
        for dia in mysite.profile.models.DataImportAttempt.objects.filter(completed=False, source='db'):
            self.add_debianqa_dia_to_reactor(dia.query, dia.id)

    def add_debianqa_dia_to_reactor(self, query, dia_id):
        ### For now, only the 'db' == Debian == qa.debian.org DIAs are in a format where
        ### they can handle asynchronous operation.
        dqa = mysite.customs.profile_importers.DebianQA(query, dia_id)

        ### d is the "deferred" object. We create it using getPage(), and then
        ### we configure its next actions.
        d = getPage(dqa.getUrl())
        d.addCallback(dqa.handlePageContents)

    def handle(self, *args, **options):
        self.create_tasks_from_dias()
        print 'Starting Reactor...'
        reactor.run()
        print '...reactor finished!'
