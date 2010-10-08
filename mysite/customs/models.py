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

import mysite.search.models
import mysite.customs.ohloh

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

class BugzillaTracker(models.Model):
    '''This model stores the data for individual Bugzilla trackers.'''
    project_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False)
    base_url = models.URLField(max_length=200, unique=True,
                               blank=False, null=False, verify_exists=False,
            help_text="This is the URL to the homepage of the Bugzilla tracker instance. Remove any homepage filenames such as 'index.cgi' from this.")
    bug_project_name_format = models.CharField(max_length=200, blank=False,
            help_text="Any string here will be used verbatim as the project name for each bug aside from the keys '{project}', '{component}' and '{product}', which are replaced with the relevant data from each individual bug.")
    QUERY_URL_TYPES = (
            ('xml', 'Bug XML query'),
            ('tracker', 'Tracker bug URL')
            )
    query_url_type = models.CharField(max_length=20, choices=QUERY_URL_TYPES, blank=False, default='xml',
            help_text="We support two types of bug importing - either from search queries that return an XML dump of all the bugs, or tracking bugs that depend on all the bugs to be imported here. Any number of a particular type can be used, but as yet a single tracker cannot have both types.")
    BITESIZED_TYPES = (
            (None, 'None'),
            ('key', 'Keyword'),
            ('wboard', 'Whiteboard tag')
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES, blank=False, default=None)
    bitesized_text = models.CharField(max_length=200, blank=True, default='')
    DOCUMENTATION_TYPES = (
            (None, 'None'),
            ('key', 'Keyword'),
            ('comp', 'Component'),
            ('prod', 'Product')
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES, blank=False, default=None)
    documentation_text = models.CharField(max_length=200, blank=True, default='')
    as_appears_in_distribution = models.CharField(max_length=200, blank=True, default='')

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.project_name))

class BugzillaUrl(models.Model):
    '''This model stores query or tracker URLs for BugzillaTracker objects.'''
    url = models.URLField(max_length=400,
                          blank=False, null=False)
    description = models.CharField(max_length=200, blank=True, default='')
    tracker = models.ForeignKey(BugzillaTracker)

reversion.register(BugzillaTracker, follow=["bugzillaurl_set"])
reversion.register(BugzillaUrl)

class GoogleTracker(models.Model):
    '''This model stores the data for individual Bugzilla trackers.'''
    project_name = models.CharField(max_length=200, unique=True,
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
        return smart_str('%s' % (self.project_name))

class GoogleQuery(models.Model):
    '''This model stores queries for GoogleTracker objects.
    At present we only allow labels to be queried.'''
    label = models.CharField(max_length=200, blank=True, default='')
    description = models.CharField(max_length=200, blank=True, default='')
    tracker = models.ForeignKey(GoogleTracker)

reversion.register(GoogleTracker, follow=["googlequery_set"])
reversion.register(GoogleQuery)
