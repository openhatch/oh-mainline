# This file is part of OpenHatch.
# Copyright (C) 2011 Jack Grigg
# Copyright (C) 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2012 Berry Phillips
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
import importlib
from types import NoneType
import django.db.models
from django.conf import settings

import mysite.customs.models
import mysite.profile.models

from mysite.search.models import Bug
from mysite.customs.core_bugimporters import AddTrackerForeignKeysToBugs
from mysite.customs.data_transits import trac_data_transit, bug_data_transit

tracker2importer = {
    # This first one catches any Bugs with bug.tracker = None and updates
    # that field. Then it passes the bugs back here for updating.
    NoneType:
        AddTrackerForeignKeysToBugs,
}

try:
    # These link specific subclasses of TrackerModel to the
    # relevant BugImporter class. This includes the hard-coded special
    # cases, where the TrackerModel is just a shell linking to the location
    # of the hard-coded class and the BugImporter is a special one that
    # handles them specifically.

    from bugimporters.google import GoogleBugImporter
    from bugimporters.trac import TracBugImporter
    from bugimporters.roundup import RoundupBugImporter
    from bugimporters.bugzilla import BugzillaBugImporter
    from bugimporters.launchpad import LaunchpadBugImporter

    tracker2importer.update({
        mysite.customs.models.BugzillaTrackerModel:
            BugzillaBugImporter,
        # Google Code Issue Tracker
        mysite.customs.models.GoogleTrackerModel:
            GoogleBugImporter,
        # Roundup
        mysite.customs.models.RoundupTrackerModel:
            RoundupBugImporter,
        # Trac
        mysite.customs.models.TracTrackerModel:
            TracBugImporter,
        # Launchpad
        mysite.customs.models.LaunchpadTrackerModel:
            LaunchpadBugImporter,
    })

except ImportError:
    # The bugimporters library isn't installed.
    logging.info(("The bugimporters libaray could not be loaded. "
            "It may not be installed."))
    pass


class Command(BaseCommand):
    help = "Call this when you want to run a Twisted reactor."

    def _get_importer_instance_for_tracker_model(self, tracker_model):
        '''This takes a TrackerModel as input, and returns an instantiated
        BugImporter subclass.'''
        # Some TrackerModel values have no corresponding BugImporter. Test
        # for that first so that we can bail early if needed.
        if tracker_model.__class__ not in tracker2importer:
            raise ValueError("That tracker_model has no corresponding importer")

        # Okay, so success is possible.
        # We keep the collection of running importers indexed by the type of
        # TrackerModel. If we already such an importer running, we can
        # look it up and grab it from that collection.
        custom_parser = getattr(tracker_model, 'custom_parser', None)
        key = (tracker_model, custom_parser)
        if key not in self.running_importers:
            # Find the custom parser class, if specified.
            custom_parser_class = None

            if custom_parser:
                try:
                    module_part, custom_parser_class_name = (
                        tracker_model.custom_parser.rsplit('.', 1))
                    module = importlib.import_module(
                        'bugimporters.' + module_part)
                    custom_parser_class = getattr(module, custom_parser_class_name)
                except Exception:
                    logging.error("Uh oh, failed trying to grab %s", custom_parser)
                    logging.exception("We failed to import the requested custom importer.")

            data_transits = {'bug': bug_data_transit, 'trac': trac_data_transit}

            # Okay, at this point we're going to have to create it. Note that
            # when we create it, we store it in the self.running_importers dict
            # so that later calls to this will find it.
            bug_importer_subclass = tracker2importer[tracker_model.__class__]
            bug_importer_instance = bug_importer_subclass(
                    tracker_model, self, bug_parser=custom_parser_class,
                    data_transits=data_transits)

            self.running_importers[key] = bug_importer_instance

        return self.running_importers[key]

    def update_trackers(self):
        print "For all tracker queries we know about, enqueue the stale ones."
        # Fetch a list of Queries that are stale.
        queries = mysite.customs.models.TrackerQueryModel.objects.filter(
                last_polled__lt=datetime.datetime.utcnow() - datetime.timedelta(
                days=settings.TRACKER_POLL_INTERVAL)
                ).select_subclasses()
        # Convert this list to a dictionary of TrackerModels.
        tm_list = [(query, query.tracker) for query in queries if hasattr(query, 'tracker')]
        tm_dict = defaultdict(list)
        [tm_dict[k].append(v) for v, k in tm_list]
        # For each TrackerModel, process its stale Queries.
        for tm, queries in tm_dict.items():
            try:
                importer = self._get_importer_instance_for_tracker_model(tm)
            except ValueError:
                continue
            importer.process_queries(queries)

    def update_bugs_without_a_bug_tracker(self, bug_list=None):
        '''This method enqueues work to refresh bugs that have no bug_tracker
        object attached.'''
        if bug_list is None:
            bug_list = Bug.all_bugs.filter(
                last_polled__lt=datetime.datetime.utcnow()-datetime.timedelta(days=settings.TRACKER_POLL_INTERVAL)).filter(
                django.db.models.Q(tracker_id=None))
        return self.update_bugs(bug_list=bug_list)

    def update_bugs(self, bug_list = None):
        print "For all Bugs we know of, enqueue the stale ones...",

        # Initialize mapping of TrackerModel => list of Bug objects to work on
        tm_dict = defaultdict(list)

        # If we have been specifically passed Bugs to update, add those to tm_dict
        if bug_list:
            bugs = bug_list
            # Convert this list to a dictionary of TrackerModels.
            for bug in bug_list:
                tm_dict[bug.tracker].append(bug)
        else:
            logging.info("Calculating tracker<->bug refreshes that need to happen...")
            # For each TrackerModel, get a list of Bugs that need refreshing
            tracker_models = mysite.customs.models.TrackerModel.objects.select_subclasses()
            for tracker_model in tracker_models:
                # Fetch a list of all Bugs that are stale.
                bugs = Bug.all_bugs.filter(last_polled__lt=
                                           datetime.datetime.utcnow()-datetime.timedelta(days=-settings.TRACKER_POLL_INTERVAL)
                                           ).filter(tracker_id=tracker_model.id)
                tm_dict[tracker_model] = bugs
                logging.info("Enqueued %d bugs for tracker '%s'", len(bugs), tracker_model)

        # For each TrackerModel, process its stale Bugs.
        for tm, bugs in tm_dict.items():
            try:
                importer = self._get_importer_instance_for_tracker_model(tm)
            except ValueError:
                logging.info("Skipping this tracker model: %s", tm)
                continue

            # Give the importer bug URLs to process.
            bug_urls = [bug.canonical_bug_link for bug in bugs]
            # Put the bug list in the form required for process_bugs.
            # The second entry of the tuple is None as we obviously have no data yet.
            bug_list = [(bug_url, None) for bug_url in bug_urls]
            importer.process_bugs(bug_list)
            print "%d bugs enqueued." % (len(bug_list),)

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

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.running_deferreds = 0
        self.running_importers = {}
        self.already_enqueued_stop_command = False
        self.active_dia_pks = set()

    def handle(self, use_reactor=True, *args, **options):
        # Hack: This tells our update_the_person_index_from_project()
        # to skip its work. Some of the work we do during bug import updates the
        # Project objects, but we do not need to reindex the Person objects.
        # So we store a flag in the settings object saying we should skip that.
        django.conf.settings.SKIP_PERSON_REINDEX_ON_PROJECT_SAVE = True

        print "Creating getPage()-based deferreds..."
        self.create_tasks_from_dias()
        self.update_bugs_without_a_bug_tracker()
        self.update_trackers()
        self.update_bugs()
        if self.running_deferreds:
            print 'Starting Reactor...'
            assert use_reactor
            twisted.internet.reactor.run()
            print '...reactor finished!'
