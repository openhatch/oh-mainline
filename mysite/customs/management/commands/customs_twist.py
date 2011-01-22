# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 OpenHatch
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

from django.core.management.base import BaseCommand
import twisted.web.client
import twisted.internet
import mysite.customs.profile_importers
import logging

import mysite.profile.models

MAX_DIAS = 10

class Command(BaseCommand):
    help = "Call this when you want to run a Twisted reactor."

    def create_tasks_from_dias(self, max = 20):
        print 'For all DIAs we know how to process with Twisted: enqueue them.'
        enqueued_dias_count = 0

        for dia in mysite.profile.models.DataImportAttempt.objects.filter(completed=False):
            # If for some reason this dia is one we are working on, skip past it.
            if dia.pk in self.active_dia_pks:
                continue

            # If we have done too much work, just stop enqueuing DIAs.
            if enqueued_dias_count >= max:
                print 'Stopped after enqueuing', max, 'dias.'
                return
            if dia.source in mysite.customs.profile_importers.SOURCE_TO_CLASS:
                self.active_dia_pks.add(dia.id)
                cls = mysite.customs.profile_importers.SOURCE_TO_CLASS[dia.source]
                self.add_dia_to_reactor(cls, dia.query, dia.id)
                enqueued_dias_count += 1

    def add_dia_to_reactor(self, cls, query, dia_id):
        state_manager = cls(query, dia_id, self)

        ### d is the "deferred" object. We create it using getPage(), and then
        ### we configure its next actions.
        urls_and_callbacks = state_manager.getUrlsAndCallbacks()
        for data_dict in urls_and_callbacks:
            self.call_getPage_on_data_dict(state_manager, data_dict)

    def call_getPage_on_data_dict(self, state_manager, data_dict):
        url = data_dict['url']
        callback = data_dict['callback']
        errback = data_dict.get('errback', None)
        
        logging.debug("Creating getPage for " + url)

        # First, actually create the Deferred.
        d = twisted.web.client.getPage(url)
        
        # Then, keep track of it.
        state_manager.urls_we_are_waiting_on[url] += 1
        self.running_deferreds += 1
        
        # wrap the callback
        wrapped_callback = mysite.customs.profile_importers.ImportActionWrapper(
            url=url,
            pi=state_manager,
            fn=callback)
        d.addCallback(wrapped_callback)

        if errback is not None:
            # wrap the errback
            wrapped_errback = mysite.customs.profile_importers.ImportActionWrapper(
                url=url,
                pi=state_manager,
                fn=errback)
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
            twisted.internet.reactor.callWhenRunning(lambda *args: twisted.internet.reactor.stop())

    def handle(self, use_reactor=True, *args, **options):
        self.running_deferreds = 0
        self.already_enqueued_stop_command = False
        self.active_dia_pks = set()

        print "Creating getPage()-based deferreds..."
        self.create_tasks_from_dias()
        if self.running_deferreds:
            print 'Starting Reactor...'
            assert use_reactor
            twisted.internet.reactor.run()
            print '...reactor finished!'
