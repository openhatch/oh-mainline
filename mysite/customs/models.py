# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
# Copyright (C) 2009, 2010 OpenHatch, Inc.
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

import csv
import datetime
from itertools import chain
import lxml.html # scraper library
import re
import reversion
import urllib2
import urllib

from django.db import models
from django.utils.encoding import smart_str
from model_utils.managers import InheritanceManager

import mysite.search.models

class RecentMessageFromCIA(models.Model):
    '''This model logs all messages from CIA.vc.
    At some point, we should examine how and when we want to flush this.'''
    # See http://cia.vc/stats/project/moin/.xml
    committer_identifier = models.CharField(max_length=255) # author, to cia.vc
    project_name = models.CharField(max_length=255) # project, to cia.vc
    path = models.CharField(max_length=255) # files, to cia.vc
    version = models.CharField(max_length=255) # version, to cia.vc
    message = models.CharField(max_length=255) # log, to cia.vc
    module = models.CharField(max_length=255) # module, to cia.vc
    branch = models.CharField(max_length=255) # branch, to cia.vc
    time_received = models.DateTimeField(auto_now_add=True)

class WebResponse(models.Model):
    '''This model abuses the databases as a network log. We store here
    successful and unsuccessful web requests so that we can refer to
    them later.'''
    # FIXME: It'd be nice to get the request's headers, not just the
    # server's response (despite the name of this class).
    text = models.TextField()
    url = models.TextField()
    status = models.IntegerField()
    response_headers = models.TextField() # a long multi-line string

    @staticmethod
    def create_from_browser(b):
        ret = WebResponse()

        # Seek to 0, just in case someone else tried to read before us
        b.response().seek(0)
        ret.text = b.response().read()

        ret.url = b.geturl()

        ret.status = 200 # Presumably it worked.

        # Use ''.join() on the response headers so we get a big ol' string
        ret.response_headers = ''.join(b.response()._headers.headers)

        return ret

    @staticmethod
    def create_from_http_error(error):
        return None

class TrackerModel(models.Model):
    '''This is the base Model that tracker types subclass.'''
    max_connections = models.IntegerField(blank=True, default=8,
            help_text="This is the maximum number of simultaneous connections that our bug importer will make to the tracker server.")
    objects = InheritanceManager()

    def get_base_url(self):
        # Implement this in a subclass
        raise NotImplementedError

class TrackerQueryModel(models.Model):
    '''This model just exists to provide a way to grab a QuerySet
    containing all tracker queries.'''
    last_polled = models.DateTimeField(default=datetime.datetime(1970, 1, 1))
    objects = InheritanceManager()

    def get_query_url(self):
        # Implement this in a subclass
        raise NotImplementedError

class BugzillaTrackerModel(TrackerModel):
    '''This model stores the data for individual Bugzilla trackers.'''
    tracker_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False)
    base_url = models.URLField(max_length=200, unique=True,
                               blank=False, null=False, verify_exists=False,
            help_text="This is the URL to the homepage of the Bugzilla tracker instance. Remove any homepage filenames such as 'index.cgi' from this.")
    bug_project_name_format = models.CharField(max_length=200, blank=False,
            help_text="Any string here will be used verbatim as the project name for each bug aside from the keys '{tracker_name}', '{component}' and '{product}', which are replaced with the tracker's name from above and the relevant data from each individual bug respectively.")
    QUERY_URL_TYPES = (
            ('xml', 'Bug XML query'),
            ('tracker', 'Tracker bug URL')
            )
    query_url_type = models.CharField(max_length=20, choices=QUERY_URL_TYPES, blank=False, default='xml',
            help_text="This field is deprecated, and will be removed once all Bugzilla trackers are in the asynchronous framework.")
    BITESIZED_TYPES = (
            (None, 'None'),
            ('key', 'Keyword'),
            ('wboard', 'Whiteboard tag')
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES, blank=False, default=None)
    bitesized_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a bite-sized bug. Separate multiple values with single commas (,) only.")
    DOCUMENTATION_TYPES = (
            (None, 'None'),
            ('key', 'Keyword'),
            ('comp', 'Component'),
            ('prod', 'Product')
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES, blank=False, default=None)
    documentation_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a documentation bug. Separate multiple values with single commas (,) only.")
    as_appears_in_distribution = models.CharField(max_length=200, blank=True, default='')

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def get_base_url(self):
        return self.base_url

    def create_class_that_can_actually_crawl_bugs(self):
        # FIXME: This is totally busted.
        # If you run the tests, you'll see that the project_name isn't somehow
        # flowing through, and I don't know why. :-(
        import mysite.customs.bugtrackers.bugzilla
        factory = mysite.customs.bugtrackers.bugzilla.bugzilla_tracker_factory(self)
        instance = factory()
        return instance

class BugzillaQueryModel(TrackerQueryModel):
    '''This model stores query or tracker URLs for BugzillaTracker objects.'''
    url = models.URLField(max_length=400,
                          blank=False, null=False)
    QUERY_TYPES = (
            ('xml', 'Bug XML query'),
            ('tracker', 'Tracker bug URL')
            )
    query_type = models.CharField(max_length=20, choices=QUERY_TYPES, blank=False, default='xml',
            help_text="We support two types of bug importing from Bugzilla - search queries that return an XML dump of all the bugs, and tracking bugs that depend on all the bugs to be imported here.")
    description = models.CharField(max_length=200, blank=True, default='')
    tracker = models.ForeignKey(BugzillaTrackerModel)

    def get_query_url(self):
        return self.url

reversion.register(BugzillaTrackerModel, follow=["bugzillaquerymodel_set"])
reversion.register(BugzillaQueryModel)

class GoogleTrackerModel(TrackerModel):
    '''This model stores the data for individual Google trackers.'''
    tracker_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False,
            help_text="This is the name that OpenHatch will use to identify the project.")
    google_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False,
            help_text="This is the name that Google uses to identify the project.")
    BITESIZED_TYPES = (
            (None, 'None'),
            ('label', 'Label'),
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES, blank=False, default=None)
    bitesized_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that marks a bug as being ideal for newcomers.")
    DOCUMENTATION_TYPES = (
            (None, 'None'),
            ('label', 'Label'),
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES, blank=False, default=None)
    documentation_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the label that marks a documentation bug.")

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def get_base_url(self):
        return 'http://code.google.com/p/%s/' % self.google_name

class GoogleQueryModel(TrackerQueryModel):
    '''This model stores queries for GoogleTracker objects.
    At present we only allow labels to be queried.'''
    label = models.CharField(max_length=200, blank=True, default='')
    description = models.CharField(max_length=200, blank=True, default='')
    tracker = models.ForeignKey(GoogleTrackerModel)

    def get_query_url(self):
        query_url = 'https://code.google.com/feeds/issues/p/%s/issues/full?can=open&max-results=10000' % self.tracker.google_name
        if self.label:
            query_url = '%s&label=%s' % (query_url, self.label)
        return query_url

reversion.register(GoogleTrackerModel, follow=["googlequerymodel_set"])
reversion.register(GoogleQueryModel)

class TracTimeline(models.Model):
    base_url = models.URLField(max_length=200, unique=True,
                               blank=False, null=False)
    last_polled = models.DateTimeField(default=datetime.datetime(1970, 1, 1))

    all_timelines = models.Manager()

    def get_times(self, bug_url):
        bug_times = self.tracbugtimes_set.get(canonical_bug_link = bug_url)
        return (bug_times.date_reported, bug_times.last_touched)

class TracBugTimes(models.Model):
    '''This model stores times for bugs extracted from Trac timelines.
    To be nice to the Trac servfers, this is updated all at once,
    before any bugs are updated. As such, it is possible for there
    to be entries here that do not yet correspond to Bugs in our
    database.'''
    canonical_bug_link = models.URLField(max_length=200, unique=True,
                                         blank=False, null=False)
    date_reported = models.DateTimeField(default=datetime.datetime(1970, 1, 1))
    last_touched = models.DateTimeField(default=datetime.datetime(1970, 1, 1))
    latest_timeline_status = models.CharField(max_length=15, blank=True, default='')
    timeline = models.ForeignKey(TracTimeline)

class TracTrackerModel(TrackerModel):
    '''This model stores the data for individual Trac trackers.'''
    tracker_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False)
    base_url = models.URLField(max_length=200, unique=True,
                               blank=False, null=False, verify_exists=False,
            help_text="This is the URL to the homepage of the Trac tracker instance. Remove any subpaths like 'ticket/' or 'query' from this.")
    bug_project_name_format = models.CharField(max_length=200, blank=False,
            help_text="Any string here will be used verbatim as the project name for each bug aside from the keys '{tracker_name}' and '{component}', which are replaced with the tracker's name from above and the relevant data from each individual bug respectively.")
    BITESIZED_TYPES = (
            (None, 'None'),
            ('keywords', 'Keyword')
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES, blank=False, default=None)
    bitesized_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a bite-sized bug. Separate multiple values with single commas (,) only.")
    DOCUMENTATION_TYPES = (
            (None, 'None'),
            ('keywords', 'Keyword'),
            ('component', 'Component')
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES, blank=False, null=True, default=None)
    documentation_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a documentation bug. Separate multiple values with single commas (,) only.")
    as_appears_in_distribution = models.CharField(max_length=200, blank=True, default='')
    old_trac = models.BooleanField(default=False)

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def get_base_url(self):
        return self.base_url

class TracQueryModel(TrackerQueryModel):
    '''This model stores query URLs for TracTracker objects.'''
    url = models.URLField(max_length=400,
                          blank=False, null=False)
    description = models.CharField(max_length=200, blank=True, default='')
    tracker = models.ForeignKey(TracTrackerModel)

    def get_query_url(self):
        return self.url

reversion.register(TracTrackerModel, follow=["tracquerymodel_set"])
reversion.register(TracQueryModel)
