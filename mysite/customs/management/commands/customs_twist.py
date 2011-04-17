# This file is part of OpenHatch.
# Copyright (C) 2011 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
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

from collections import defaultdict
from django.core.management.base import BaseCommand
import twisted.web.client
import twisted.internet
import mysite.customs.profile_importers
import datetime
import logging
from types import NoneType

import mysite.customs.models
import mysite.customs.bugimporters.base
import mysite.customs.bugimporters.bugzilla
import mysite.customs.bugimporters.google
import mysite.customs.bugimporters.roundup
import mysite.customs.bugimporters.trac
import mysite.profile.models
from mysite.search.models import Bug

tracker2importer = {
        # This first one catches any Bugs with bug.tracker = None and updates
        # that field. Then it passes the bugs back here for updating.
        NoneType:
            mysite.customs.bugimporters.base.AddTrackerForeignKeysToBugs,

        # The rest of these link specific subclasses of TrackerModel to the
        # relevant BugImporter class. This includes the hard-coded special
        # cases, where the TrackerModel is just a shell linking to the location
        # of the hard-coded class and the BugImporter is a special one that
        # handles them specifically.

        # Bugzilla
        mysite.customs.models.BugzillaTrackerModel:
            mysite.customs.bugimporters.bugzilla.BugzillaBugImporter,
        # Google Code Issue Tracker
        mysite.customs.models.GoogleTrackerModel:
            mysite.customs.bugimporters.google.GoogleBugImporter,
        # Roundup1
        mysite.customs.models.RoundupTrackerModel:
            mysite.customs.bugimporters.roundup.RoundupBugImporter,
        # Trac
        mysite.customs.models.TracTrackerModel:
            mysite.customs.bugimporters.trac.TracBugImporter,
        }

class Command(BaseCommand):
    help = "Call this when you want to run a Twisted reactor."

    def update_trackers(self):
        print "For all tracker queries we know about, enqueue the stale ones."
        # Fetch a list of Queries that are stale.
        queries = mysite.customs.models.TrackerQueryModel.objects.filter(
                last_polled__lt=datetime.datetime.utcnow()-datetime.timedelta(days=1)
                ).select_subclasses()
        # Convert this list to a dictionary of TrackerModules.
        tm_list = [(query, query.tracker) for query in queries if hasattr(query, 'tracker')]
        tm_dict = defaultdict(list)
        [tm_dict[k].append(v) for v, k in tm_list]
        # For each TrackerModel, process its stale Queries.
        for tm, queries in tm_dict.items():
            try:
                icls = tracker2importer[tm.__class__]
            except KeyError:
                # This TrackerModule doesn't have a BugImporter yet.
                continue
            else:
                # See if there is already an importer running for this tracker.
                im = self.running_importers.get(tm, None)
                if not im:
                    # There isn't, so create one.
                    im = icls(tm, self)
                    # And store it.
                    self.running_importers[tm] = im
                # Give the importer queries to process.
                im.process_queries(queries)

    def update_bugs(self, bug_list = None):
        print "For all Bugs we know of, enqueue the stale ones."
        # Check if we have been specifically passed Bugs to update.
        if bug_list:
            bugs = bug_list
        else:
            # Fetch a list of all Bugs that are stale.
            bugs = Bug.all_bugs.filter(
                    last_polled__lt=datetime.datetime.utcnow()-datetime.timedelta(days=1))
        # Convert this list to a dictionary of TrackerModules.
        tm_list = [(bug, bug.tracker) for bug in bugs]
        tm_dict = defaultdict(list)
        [tm_dict[k].append(v) for v, k in tm_list]
        # For each TrackerModel, process its stale Bugs.
        for tm, bugs in tm_dict.items():
            try:
                icls = tracker2importer[tm.__class__]
            except KeyError:
                # This TrackerModule doesn't have a BugImporter yet.
                continue
            else:
                # See if there is already an importer running for this tracker.
                im = self.running_importers.get(tm, None)
                if not im:
                    # There isn't, so create one.
                    im = icls(tm, self)
                    # And store it.
                    self.running_importers[tm] = im
                # Give the importer bug URLs to process.
                bug_urls = [bug.canonical_bug_link for bug in bugs]
                # Put the bug list in the form required for process_bugs.
                # The second entry of the tuple is None as we obviously have no data yet.
                bug_list = [(bug_url, None) for bug_url in bug_urls]
                im.process_bugs(bug_list)

    def create_tasks_from_dias(self, max = 8):
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
        if type(url) == unicode:
            url = url.encode('utf-8')
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
        self.decrement_deferred_count()
        self.maybe_quit()

    def decrement_deferred_count(self, *args):
        self.running_deferreds -= 1
        if self.running_deferreds < 0:
            raise ValueError("Uh, number of running deferreds went negative.")

    def maybe_quit(self, *args):
        if self.running_deferreds == 0:
            self.stop_the_reactor()

    def stop_the_reactor(self, *args):
        if self.already_enqueued_stop_command:
            return
        else:
            self.already_enqueued_stop_command = True
            twisted.internet.reactor.callWhenRunning(lambda *args: twisted.internet.reactor.stop())

    def handle(self, use_reactor=True, *args, **options):
        self.running_deferreds = 0
        self.running_importers = {}
        self.already_enqueued_stop_command = False
        self.active_dia_pks = set()

        print "Creating getPage()-based deferreds..."
        self.create_tasks_from_dias()
        self.update_trackers()
        self.update_bugs()
        if self.running_deferreds:
            print 'Starting Reactor...'
            assert use_reactor
            twisted.internet.reactor.run()
            print '...reactor finished!'
