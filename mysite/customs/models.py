import urllib2
import urllib
import re
import lxml.html # scraper library
from itertools import chain
import csv
import datetime
from django.db import models
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
                               blank=False, null=False)
    bug_project_name_format = models.CharField(max_length=200, blank=False)
    QUERY_URL_TYPES = (
            ('xml', 'Bug XML query'),
            ('tracker', 'Tracker bug URL')
            )
    query_url_type = models.CharField(max_length=20, choices=QUERY_URL_TYPES)
    BITESIZED_TYPES = (
            (None, 'None'),
            ('key', 'Keyword'),
            ('wboard', 'Whiteboard tag')
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES)
    bitesized_text = models.CharField(max_length=200, blank=True, default='')
    DOCUMENTATION_TYPES = (
            (None, 'None'),
            ('key', 'Keyword'),
            ('comp', 'Component'),
            ('prod', 'Product')
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES)
    documentation_text = models.CharField(max_length=200, blank=True, default='')
    as_appears_in_distribution = models.CharField(max_length=200, blank=True, default='')

    all_trackers = models.Manager()

class BugzillaURL(models.Model):
    '''This model stores query or tracker URLs for BugzillaTracker objects.'''
    url = models.URLField(max_length=300, unique=True,
                          blank=False, null=False)
    bugzilla_tracker = models.ForeignKey(BugzillaTracker)
