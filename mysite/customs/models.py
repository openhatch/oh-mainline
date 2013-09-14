# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2012 John Morrissey
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

import datetime
import urlparse
import urllib
import reversion

from django.db import models
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_str
from model_utils.managers import InheritanceManager

import django.forms.models
import mysite.base.unicode_sanity

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
    created_for_project = models.ForeignKey(
        'search.Project', null=True,
        help_text='The project (if any) whose edit page caused the creation of this bug tracker model')

    ### This optional attribute specifies a class name, which is intepreted as
    ### part of the mysite.customs.core_bugimporters module.
    ###
    ### If the class is specified, we will use custom code from that class
    ### when doing bug parsing.
    custom_parser = models.CharField(max_length=200, blank=True, default='',
                                     help_text='(For use by OpenHatch admins) Choose a custom bug parser class for the tracker')

    objects = InheritanceManager()

    def as_dict(self):
        # First, add our data
        out_dict = django.forms.models.model_to_dict(self)

        # Then, indicate to downstream what kind of bug importer we are
        CLASS_NAME2SIMPLE_NAME = {
            mysite.customs.models.BugzillaTrackerModel: 'bugzilla',
            mysite.customs.models.GitHubTrackerModel: 'github',
            mysite.customs.models.GoogleTrackerModel: 'google',
            mysite.customs.models.RoundupTrackerModel: 'roundup',
            mysite.customs.models.TracTrackerModel: 'trac',
            mysite.customs.models.LaunchpadTrackerModel: 'launchpad',
            }
        out_dict['bugimporter'] = CLASS_NAME2SIMPLE_NAME[self.__class__]

        # Then, remove fields that we don't care about
        BLACKLISTED_FIELDS = set([
                'id', # This is not needed by the importer
                'trackermodel_ptr', # This is not needed by the importer
                'created_for_project', # Not needed by importer either
                'old_trac', # This is useless
                'max_connections', # This is useless
                ])

        for field in BLACKLISTED_FIELDS:
            if field in out_dict:
                del out_dict[field]

        # Add a list of our queries.
        # This permits oh-bugimporters to go to the 'net and query the tracker
        # for new bugs that correspond to this bug tracker.
        query_urls = []
        for querymodel in TrackerQueryModel.__subclasses__():
            queries = querymodel.objects.filter(tracker=self)
            query_urls.extend([
                    q.get_query_url() for q in queries])
        out_dict['queries'] = query_urls

        # Add a list of bug URLs we're responsible for.
        # This permits oh-bugimporters to go to the 'net and refresh each bug.
        # It is essential because otherwise, when a bug falls out of a query
        # (if, for example, it becomes 'resolved' and the query only looks for
        # bugs that need fixing), we would not get up-to-date information about
        # the bug.
        out_dict['existing_bug_urls'] = list(mysite.search.models.Bug.all_bugs.filter(
            tracker_id=self.id).values_list('canonical_bug_link', flat=True))

        # Some subclasses will add a get_older_bug_data value. This generic
        # method supports that by adding that key, and setting it to None.
        out_dict['get_older_bug_data'] = None

        return out_dict

    def get_edit_url(self):
        '''This method returns the URL you can use to access this tracker's edit
        link.

        It is part of this superclass so that derived classes can use the
        functionality without implementing it themselves. It relies on
        the classes being manually added to
        mysite.customs.core_bugimporters.all_trackers.'''
        import mysite.customs.core_bugimporters
        my_short_name = None

        for short_name in mysite.customs.core_bugimporters.all_trackers:
            klass = mysite.customs.core_bugimporters.all_trackers[short_name]['model']
            if self.__class__ == klass:
                my_short_name = short_name
                break

        # Did we find a short name suitable for use in a URL? If not, let's
        # just crash.
        if my_short_name is None:
            raise ValueError, ("The tracker class seems to be misconfigured. "
                               "Read the comments around this message.")

        return reverse('mysite.customs.views.edit_tracker', kwargs={
                'tracker_id': self.id,
                'tracker_type': my_short_name,
                'tracker_name': self.tracker_name})


    def get_base_url(self):
        # Implement this in a subclass
        raise NotImplementedError

    @classmethod
    def get_by_name(cls, tracker_name):
        '''This returns the instance of a subclass of TrackerModel,
        if any, that has its tracker_name field set to the provided
        value.

        This is necessary because tracker_name is defined by each of
        the subclasses, rather than by this class in particular.'''
        query_parts = []
        for subclass in cls.__subclasses__():
            name = subclass.__name__.lower()
            query_as_dict = {name + '__tracker_name': tracker_name}
            query_parts.append(Q(**query_as_dict))

        def _pipe_things(a, b):
            return a | b
        joined = reduce(_pipe_things, query_parts)
        return cls.objects.select_subclasses().get(joined)

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
            ('tracker', 'Tracker bug URL'),
            )
    query_url_type = models.CharField(max_length=20, choices=QUERY_URL_TYPES, blank=False, default='xml',
            help_text="This field is deprecated, and will be removed once all Bugzilla trackers are in the asynchronous framework.")
    BITESIZED_TYPES = (
            ('key', 'Keyword'),
            ('wboard', 'Whiteboard tag'),
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES, blank=True)
    bitesized_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a bite-sized bug. Separate multiple values with single commas (,) only.")
    DOCUMENTATION_TYPES = (
            ('key', 'Keyword'),
            ('comp', 'Component'),
            ('prod', 'Product'),
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES, blank=True)
    documentation_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a documentation bug. Separate multiple values with single commas (,) only.")
    as_appears_in_distribution = models.CharField(max_length=200, blank=True, default='', help_text='If this applies to just one software distribution effort, like Fedora, Debian, Windows Portable Apps, etc., write the name of that here. If not, leave blank.')

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def get_base_url(self):
        return self.base_url

class BugzillaQueryModel(TrackerQueryModel):
    '''This model stores query or tracker URLs for BugzillaTracker objects.'''
    url = models.URLField(max_length=400,
                          blank=False, null=False)
    QUERY_TYPES = (
            ('xml', 'Bug XML query'),
            ('tracker', 'Tracker bug URL'),
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
            ('label', 'Label'),
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES, blank=True)
    bitesized_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that marks a bug as being ideal for newcomers.")
    DOCUMENTATION_TYPES = (
            ('label', 'Label'),
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES, blank=True)
    documentation_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the label that marks a documentation bug.")

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def as_dict(self):
        out = super(GoogleTrackerModel, self).as_dict()
        lowest_last_polled = mysite.search.models.Bug.all_bugs.filter(
            tracker_id=self.id).aggregate(django.db.models.Min('last_polled'))[
            'last_polled__min']
        if lowest_last_polled is None:
            lowest_last_polled = datetime.datetime(1970, 1, 1)
        query_data = {u'can': u'all',
                      u'updated-min': unicode(lowest_last_polled.isoformat())}
        query_url = google_query_url(self.google_name,
                                     **query_data)
        out['get_older_bug_data'] = query_url
        return out

    def get_base_url(self):
        return 'http://code.google.com/p/%s/' % self.google_name

def google_query_url(project_name, **kwargs):
    extra_data = {u'max-results': u'10000',
                  u'can': u'open',
                  }
    extra_data.update(kwargs)
    base = 'https://code.google.com/feeds/issues/p/%s/issues/full' % (project_name,)
    url = base + '?' + mysite.base.unicode_sanity.urlencode(extra_data)
    return url

class GoogleQueryModel(TrackerQueryModel):
    '''This model stores queries for GoogleTracker objects.
    At present we only allow labels to be queried.'''
    label = models.CharField(max_length=200, blank=True, default='')
    description = models.CharField(max_length=200, blank=True, default='')
    tracker = models.ForeignKey(GoogleTrackerModel)

    def get_query_url(self):
        if self.label:
            extra_data = {u'label': unicode(self.label)}
        else:
            extra_data = {}
        return google_query_url(self.tracker.google_name, **extra_data)

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
            ('keywords', 'Keyword'),
            ('priority', 'Priority'),
            ('difficulty', 'Difficulty'),
            )
    bitesized_type = models.CharField(max_length=10, choices=BITESIZED_TYPES, blank=True)
    bitesized_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a bite-sized bug. Separate multiple values with single commas (,) only.")
    DOCUMENTATION_TYPES = (
            ('keywords', 'Keyword'),
            ('component', 'Component'),
            )
    documentation_type = models.CharField(max_length=10, choices=DOCUMENTATION_TYPES, blank=True)
    documentation_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field type selected above will contain that indicates a documentation bug. Separate multiple values with single commas (,) only.")
    as_appears_in_distribution = models.CharField(max_length=200, blank=True, default='', help_text='If this applies to just one software distribution effort, like Fedora, Debian, Windows Portable Apps, etc., write the name of that here. If not, leave blank.')
    old_trac = models.BooleanField(default=False)

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def get_base_url(self):
        return self.base_url

class TracQueryModel(TrackerQueryModel):
    '''This model stores query URLs for TracTracker objects.'''
    url = models.URLField(max_length=400,
                          blank=False, null=False,
                          help_text="This is the URL of the Trac query containing the bugs that you want us to index. Make sure to include &format=csv in the URL.")
    description = models.CharField(max_length=200, blank=True, default='')
    tracker = models.ForeignKey(TracTrackerModel)

    def get_query_url(self):
        return self.url

reversion.register(TracTrackerModel, follow=["tracquerymodel_set"])
reversion.register(TracQueryModel)

class RoundupTrackerModel(TrackerModel):
    '''This model stores the data for individual Roundup trackers.'''
    tracker_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False,
            help_text="This is the name that OpenHatch will use to identify the project.")
    base_url = models.URLField(max_length=200, unique=True,
                               blank=False, null=False, verify_exists=False,
            help_text="This is the URL to the homepage of the Roundup tracker instance. Remove any subpaths like 'issue42' or 'user37' from this.")
    closed_status = models.CharField(max_length=200, blank=False,
            help_text="This is the text that the 'Status' field will contain that indicates a bug is closed. For multiple values to mean 'closed', separate with commas.")
    bitesized_field = models.CharField(max_length=50, blank=True, default='',
            help_text="This is the name of the field (as it appears on an issue page) that will contain the indicator of a bite-sized bug. Leave blank if none.")
    bitesized_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field above will contain that indicates a bite-sized bug. Separate multiple values with single commas (,) only.")
    documentation_field = models.CharField(max_length=50, blank=True, default='',
            help_text="This is the name of the field (as it appears on an issue page) that will contain the indicator of a documentation bug. Leave blank if none.")
    documentation_text = models.CharField(max_length=200, blank=True, default='',
            help_text="This is the text that the field above will contain that indicates a documentation bug. Separate multiple values with single commas (,) only.")
    as_appears_in_distribution = models.CharField(max_length=200, blank=True, default='', help_text='If this applies to just one software distribution effort, like Fedora, Debian, Windows Portable Apps, etc., write the name of that here. If not, leave blank.')

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def get_base_url(self):
        return self.base_url

class RoundupQueryModel(TrackerQueryModel):
    '''This model stores query URLs for RoundupTracker objects.'''
    url = models.URLField(max_length=400, blank=False, null=False,
            help_text="This is the URL of the Roundup query containing the bugs that you want us to index. Get it by navigating to the page, query, search etc. that shows the bugs you want indexed, and copy the URL of the 'Download as CSV' link at the bottom of the page.")
    description = models.CharField(max_length=200, blank=True, default='',
            help_text="This is just an identifier to help people work out what bugs this URL corresponds to, and isn't used anywhere else.")
    tracker = models.ForeignKey(RoundupTrackerModel)

    def get_query_url(self):
        return self.url

reversion.register(RoundupTrackerModel, follow=["roundupquerymodel_set"])
reversion.register(RoundupQueryModel)

class LaunchpadTrackerModel(TrackerModel):
    '''This model stores the data for individual launchpad tracker'''
    tracker_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False,
            help_text="This is the name that OpenHatch will use to identify the project.")
    launchpad_name = models.CharField(max_length=200, unique=True,
                                    blank=False, null=False,
            help_text="This is the name that Launchpad.net uses to identify the project.")
    bitesized_tag = models.CharField(max_length=50, blank=True,
            help_text="This is the value of the tag that indicates a bite-sized bug.")
    documentation_tag = models.CharField(max_length=50, blank=True,
            help_text="This is the value of the tag that indicates documentation bug.")

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def get_base_url(self):
        return '__impossible_to_use_with_launchpad'

class LaunchpadQueryModel(TrackerQueryModel):
    '''This model stores query URLs for LaunchpadTracker objects.

    For bugs in projects hosted on Launchpad, we always download all bugs
    from them. So this model is only really used to store timestamps.

    It does not need to be user-editable.'''
    tracker = models.ForeignKey(LaunchpadTrackerModel)

    def get_query_url(self):
        qs = [
            ('ws.op', 'searchTasks'),
            ('created_since', self.last_polled.isoformat())
        ]
        qs = urllib.urlencode(qs)
        parts = (
            'https',
            'api.launchpad.net',
            urlparse.urljoin('/1.0/', self.tracker.launchpad_name),
            '',
            qs,
            '')
        url = urlparse.urlunparse(parts)
        return url

reversion.register(LaunchpadTrackerModel, follow=["launchpadquerymodel_set"])
reversion.register(LaunchpadQueryModel)

class GitHubTrackerModel(TrackerModel):
    '''This model stores the data for individual GitHub repositories'''
    tracker_name = models.CharField(max_length=200, unique=True,
        blank=False, null=False,
        help_text="This is the name that OpenHatch will use to identify the project.")
    github_name = models.CharField(max_length=100, blank=False, null=False,
        help_text="This is the user or project name on GitHub that owns the project.")
    github_repo = models.CharField(max_length=100, blank=False, null=False,
        help_text="This is the repository name that GitHub uses to identify the project.")
    bitesized_tag = models.CharField(max_length=50, blank=True,
        help_text="This is the value of the GitHub label that indicates a bite-sized bug.")
    documentation_tag = models.CharField(max_length=50, blank=True,
        help_text="This is the value of the GitHub label that indicates a documentation bug.")

    class Meta:
        unique_together = (
            ('github_name', 'github_repo'),
        )

    all_trackers = models.Manager()

    def __str__(self):
        return smart_str('%s' % (self.tracker_name))

    def as_dict(self):
        out = super(GitHubTrackerModel, self).as_dict()
        # By default, set this to the empty string.
        out['get_older_bug_data'] = ''

        # If we have bugs, then instead set it to a reasonable query
        # for data that will include information about those bugs.
        lowest_last_polled = mysite.search.models.Bug.all_bugs.filter(
            tracker_id=self.id).aggregate(django.db.models.Min('last_polled'))[
            'last_polled__min']
        if lowest_last_polled is None:
            return out

        query_data = {u'since':
                          unicode(lowest_last_polled.isoformat())}
        query_url = github_query_url(self.github_name,
                                     self.github_repo,
                                     **query_data)
        out['get_older_bug_data'] = query_url
        return out

    def get_base_url(self):
        return '__impossible_to_use_with_github'

    def get_github_url(self):
        return 'https://github.com/%s/%s' % (self.github_name, self.github_repo)

def github_query_url(github_user_name, github_repo_name, **kwargs):
    base_url = ('https://api.github.com/repos/%s/%s/issues' % (
            mysite.base.unicode_sanity.quote(github_user_name),
            mysite.base.unicode_sanity.quote(github_repo_name)))
    return base_url + '?' + mysite.base.unicode_sanity.urlencode(
        kwargs)

class GitHubQueryModel(TrackerQueryModel):
    '''This model stores query URLs for GitHubTracker objects.'''
    tracker = models.ForeignKey(GitHubTrackerModel)
    state = models.CharField(max_length=20, default='open')

    def get_query_url(self):
        return github_query_url(self.tracker.github_name,
                                self.tracker.github_repo,
                                **{
                u'state': u'open'})

reversion.register(GitHubTrackerModel, follow=["githubquerymodel_set"])
reversion.register(GitHubQueryModel)
