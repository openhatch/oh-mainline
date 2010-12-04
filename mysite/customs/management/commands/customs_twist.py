from django.core.management.base import BaseCommand
import twisted.web.client
from twisted.internet import reactor, defer
import mysite.customs.profile_importers
import logging

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
        urls_and_callbacks = state_manager.getUrlsAndCallbacks()
        for data_dict in urls_and_callbacks:
            self.call_getPage_on_data_dict(state_manager, data_dict)

    def call_getPage_on_data_dict(self, state_manager, data_dict):
        logging.debug("Creating getPage for " + data_dict['url'])
        d = state_manager.createDeferredAndKeepTrackOfIt(data_dict['url'])
        self.running_deferreds += 1
        # wrap the callback
        wrapped_callback = mysite.customs.profile_importers.ImportActionWrapper(
            url=data_dict['url'],
            pi=state_manager,
            fn=data_dict['callback'])
        d.addCallback(wrapped_callback)

        if 'errback' in data_dict:
            # wrap the errback
            wrapped_errback = mysite.customs.profile_importers.ImportActionWrapper(
                url=data_dict['url'],
                pi=state_manager,
                fn=data_dict['errback'])
            d.addErrback(wrapped_errback)

        d.addCallback(self.decrement_deferred_count_and_maybe_quit)

    def decrement_deferred_count_and_maybe_quit(self, *args):
        self.running_deferreds -= 1
        if self.running_deferreds == 0:
            self.stop_the_reactor()
        if self.running_deferreds < 0:
            raise ValueError("Uh, number of running deferreds went negative.")

    def stop_the_reactor(self, *args):
        if self.already_enqueued_stop_command:
            return
        else:
            self.already_enqueued_stop_command = True
            reactor.callWhenRunning(lambda *args: reactor.stop())

    def handle(self, *args, **options):
        self.running_deferreds = 0
        self.already_enqueued_stop_command = False

        print "Creating getPage()-based deferreds..."
        self.create_tasks_from_dias()
        print 'Starting Reactor...'
        reactor.run()
        print '...reactor finished!'
