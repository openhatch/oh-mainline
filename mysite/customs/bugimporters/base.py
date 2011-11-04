# This file is part of OpenHatch.
# Copyright (C) 2011 Jack Grigg
# Copyright (C) 2011 OpenHatch, Inc.
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

import twisted.web.client
import logging

from mysite.customs.models import TrackerModel
from mysite.search.models import Bug

class BugImporter(object):
    #####################################################
    # Importer functions that don't require overloading #
    #####################################################
    def add_url_to_waiting_list(self, url, callback, c_args={}, errback=None, e_args={}):
        # FIXME: change default errback to a basic logging one.
        self.waiting_urls[url] = (callback, c_args, errback, e_args)

    def get_next_waiting_url(self):
        # If there are no more waiting URLs, returns None.
        # Otherwise, returns a (url, callback, c_args, errback, e_args) tuple.
        try:
            url, (callback, c_args, errback, e_args) = self.waiting_urls.popitem()
        except KeyError:
            return None
        return (url, callback, c_args, errback, e_args)

    def add_url_to_deferred_list(self, url):
        # If the URL has previously been added to the reactor, returns None.
        # Otherwise, returns the Deferred passed back by the getPage call.
        if self.deferred_urls.get(url, None):
            # URL has already been added to the reactor by this importer
            return None
        else:
            # Record that we have added this URL
            self.deferred_urls[url] = 1
            self.rm.running_deferreds += 1
            # Return the Deferred passed back by the getPage call
            if type(url) == unicode:
                url = url.encode('utf-8')
            return twisted.web.client.getPage(url)

    def remove_url_from_deferred_list(self, result, url):
        self.deferred_urls[url] -= 1
        self.rm.decrement_deferred_count()
        if self.urls_we_are_waiting_on[url] < 0:
            # FIXME: log error with Twisted
            #logging.error("Eeek, " + url + " went negative.")
            pass

    def has_spare_connections(self):
        # If we are not yet waiting on the maximum number of URLs, return True.
        # Otherwise, return False.
        max_conns = (self.tm.max_connections if self.tm.max_connections else 8)
        return (sum(self.deferred_urls.values()) < max_conns)

    def push_urls_onto_reactor(self, result=None):
        if not self.waiting_urls and sum(self.deferred_urls.values()) < 1:
            # There are no more URLs to process, so finish.
            self.determine_if_finished()
        else:
            # If we have space, push some more URLs on.
            while self.waiting_urls and self.has_spare_connections():
                # Get the next URL.
                url, callback, c_args, errback, e_args = self.get_next_waiting_url()
                # Add the URL to the reactor.
                d = self.add_url_to_deferred_list(url)
                if d:
                    # Add the supplied callback and errback.
                    d.addCallback(callback, **c_args)
                    d.addErrback(errback, **e_args)
                    # Remove the URL from our deferred list.
                    d.addBoth(self.remove_url_from_deferred_list, url)
                    # Push some more URLs on.
                    d.addBoth(self.push_urls_onto_reactor)

    ###################################################
    # Importer functions that may require overloading #
    ###################################################
    def __init__(self, tracker_model, reactor_manager, bug_parser=None):
        # Store the tracker model
        self.tm = tracker_model
        # Store the reactor manager
        self.rm = reactor_manager
        # Create a dictionary that maps URLs to a callback/errback pair. This
        # dictionary is used to store URLs that have been found and require
        # downloading, along with the callback and errback that handle the
        # resultant data.
        self.waiting_urls = {}
        # Create a dictionary that maps URLs to a number. This means that not
        # only can we check how many URLs are currently active (and so check
        # we are not over the limit for this tracker) but by storing all URLs
        # that have been fetched in this session we can prevent double-ups
        # e.g. if somehow we attempt to download a bug URL both in the initial
        # tracker refresh and the later Bug refresh.
        self.deferred_urls= {}
        # Take an optional bug_parser to usee with this importer.
        self.bug_parser = bug_parser

    def finish_import(self):
        # This importer has finished, so let the reactor manager know that it
        # may be able to stop the reactor.
        self.rm.maybe_quit()

    ##########################################################
    # Importer functions that definitely require overloading #
    ##########################################################
    def process_queries(self, queries):
        # Implement this in a subclass
        raise NotImplementedError

    def process_bugs(self, bug_urls):
        # Implement this in a subclass
        raise NotImplementedError

    def determine_if_finished(self):
        # Implement this in a subclass
        raise NotImplementedError

class AddTrackerForeignKeysToBugs(object):
    def __init__(self, tracker_model, reactor_manager, bug_parser=None):
        # Store the tracker model
        self.tm = tracker_model
        # Store the reactor manager
        self.rm = reactor_manager

    def process_bugs(self, list_of_url_data_pairs):
        # Unzip the list of bugs and discard the data field.
        bug_urls = [bug_url for (bug_url, bug_data) in list_of_url_data_pairs]
        # Fetch a list of all Bugs that are stale.
        bugs = Bug.all_bugs.filter(
                canonical_bug_link__in = bug_urls)
        tms = TrackerModel.objects.all().select_subclasses()
        # For each TrackerModel, process its stale Bugs.
        bugs_to_retry = []
        for bug in bugs:
            tms_shortlist = [tm for tm in tms if tm.get_base_url() in bug.canonical_bug_link]
            # Check that we actually got something back, otherwise bug.tracker would get
            # set to None, and self.rm.update_bugs would send it right back here, causing
            # infinite recursion.
            if len(tms_shortlist) > 0:
                # Ideally this should now just be one object, so just take the first.
                bug.tracker = tms_shortlist[0]
                bug.save()
                bugs_to_retry.append(bug)
        # For the Bugs that now have TrackerModels, update them.
        if bugs_to_retry:
            self.rm.update_bugs(bugs_to_retry)
