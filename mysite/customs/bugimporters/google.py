# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
# Copyright (C) 2010 OpenHatch, Inc.
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

from atom.core import Parse
import datetime
from gdata.projecthosting.data import IssuesFeed, IssueEntry

from mysite.base.decorators import cached_property
import mysite.base.helpers
from mysite.customs.bugimporters.base import BugImporter
import mysite.search.models

class GoogleBugImporter(BugImporter):
    def __init__(self, *args, **kwargs):
        # Create a list to store bug ids obtained from queries.
        self.query_feeds = []
        # Call the parent __init__.
        super(GoogleBugImporter, self).__init__(*args, **kwargs)

    def process_queries(self, queries):
        # Add all the queries to the waiting list
        for query in queries:
            query_url = query.get_query_url()
            self.add_url_to_waiting_list(
                    url=query_url,
                    callback=self.handle_query_atom)
            query.last_polled = datetime.datetime.utcnow()
            query.save()

        # URLs are now all prepped, so start pushing them onto the reactor.
        self.push_urls_onto_reactor()

    def handle_query_atom(self, query_atom):
        # Turn the query_atom into an IssuesFeed.
        query_feed = Parse(query_atom, IssuesFeed)
        # And store it.
        self.query_feeds.append(query_feed)

    def prepare_bug_urls(self):
        # Pull query_feeds our of the internal storage. This is done in case the
        # list is simultaneously being written to, in which case just copying
        # the entire thing followed by deleting the contents could lead to
        # lost feeds.
        query_feed_list = []
        while self.query_feeds:
            query_feed_list.append(self.query_feeds.pop())

        # Convert query_feed_list into a list of issues.
        issue_list = []
        for feed in query_feed_list:
            issue_list.extend(feed.entry)

        # Convert the list of issues into a dict of bug URLs and issues.
        bug_dict = {}
        for issue in issue_list:
            # Get the bug URL.
            bug_url = issue.get_alternate_link().href
            # Add the issue to the bug_url_dict. This has the side-effect of
            # removing duplicate bug URLs, as later ones just overwrite earlier
            # ones.
            bug_dict[bug_url] = issue

        # And now go on to process the bug list.
        # We just use all the bugs, as they all have complete data so there is
        # no harm in updating fresh ones as there is no extra network hit.
        self.process_bugs(bug_dict.items())

    def process_bugs(self, bug_list):
        # If there are no bug URLs, finish now.
        if not bug_list:
            self.determine_if_finished()
            return

        for bug_url, bug_atom in bug_list:
            # Create a GoogleBugParser instance to store the bug data.
            gbp = GoogleBugParser(bug_url)

            if bug_atom:
                # We already have the data from a query.
                self.handle_bug_atom(bug_atom, gbp)
            else:
                # Fetch the bug data.
                self.add_url_to_waiting_list(
                        url=gbp.bug_atom_url,
                        callback=self.handle_bug_atom,
                        c_args={'gbp': gbp})

        # URLs are now all prepped, so start pushing them onto the reactor.
        self.push_urls_onto_reactor()

    def handle_bug_atom(self, bug_atom, gbp):
        # Pass the GoogleBugParser the Atom data
        gbp.set_bug_atom_data(bug_atom)

        # Get the parsed data dict from the GoogleBugParser
        data = gbp.get_parsed_data_dict(self.tm)

        # Get or create a Bug object to put the parsed data in.
        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                canonical_bug_link=gbp.bug_url)
        except mysite.search.models.Bug.DoesNotExist:
            bug = mysite.search.models.Bug(canonical_bug_link=gbp.bug_url)

        # Fill the Bug
        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # Save the project onto it
        # Project name is just the TrackerModel's tracker_name, as due to the
        # way Google Code is set up, there is always one project per tracker.
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=self.tm.tracker_name)
        # Manually save() the Project to ensure that if it was created then it has
        # a display_name.
        project_from_name.save()
        bug.project = project_from_name

        # Store the tracker that generated the Bug, update last_polled and save it!
        bug.tracker = self.tm
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()

    def determine_if_finished(self):
        # If we got here then there are no more URLs in the waiting list.
        # So if self.bug_ids is also empty then we are done.
        if self.query_feeds:
            self.prepare_bug_urls()
        else:
            self.finish_import()

class GoogleBugParser(object):
    @staticmethod
    def google_name_and_id_from_url(url):
        a, b, c, d, google_name, e, ending = url.split('/')
        show_bug, num = ending.split('=')
        bug_id = int(num)
        return (google_name, bug_id)

    def __init__(self, bug_url):
        self.bug_atom = None
        self.bug_url = bug_url
        self.google_name, self.bug_id = self.google_name_and_id_from_url(self.bug_url)

    @cached_property
    def bug_atom_url(self):
        return 'https://code.google.com/feeds/issues/p/%s/issues/full/%d' % (self.google_name, self.bug_id)

    def set_bug_atom_data(self, bug_atom):
        if type(bug_atom) == IssueEntry:
            # We have been passed the bug data directly.
            self.bug_atom = bug_atom
        else:
            # We have been passed an Atom feed string. So assume this is for a
            # single bug and parse it as an IssueEntry.
            self.bug_atom = Parse(bug_atom, IssueEntry)

    @staticmethod
    def google_count_people_involved(issue):
        # At present this only gets the author, owner if any and CCers if any.
        # FIXME: We could get absolutely everyone involved using comments,
        # but that would require an extra network call per bug.

        # Add everyone who is on CC: list
        everyone = [cc.username.text for cc in issue.cc]
        # Add author
        if type(issue.author) == type([]):
            for author in issue.author:
                everyone.append(author.name.text)
        else:
            everyone.append(issue.author.name.text)
        # Add owner if there
        if issue.owner:
            if type(issue.owner) == type([]):
                for owner in issue.owner:
                    everyone.append(owner.username.text)
            else:
                everyone.append(issue.owner.username.text)
        # Return length of the unique set of everyone.
        return len(set(everyone))

    @staticmethod
    def google_date_to_datetime(date_string):
        return mysite.base.helpers.string2naive_datetime(date_string)

    @staticmethod
    def google_find_label_type(labels, type_string):
        # This is for labels of format 'type-value'.
        # type is passed in, value is returned.
        for label in labels:
            if type_string in label.text:
                return label.text.split('-', 1)[1]
        return ''

    def get_parsed_data_dict(self, tm):
        issue = self.bug_atom
        if issue.status:
            status = issue.status.text
        else:
            status = ''
        if type(issue.author) == type([]):
            author = issue.author[0]
        else:
            author = issue.author

        ret_dict = {
                'title': issue.title.text,
                'description': issue.content.text,
                'status': status,
                'importance': self.google_find_label_type(issue.label, 'Priority'),
                'people_involved': self.google_count_people_involved(issue),
                'date_reported': self.google_date_to_datetime(issue.published.text),
                'last_touched': self.google_date_to_datetime(issue.updated.text),
                'submitter_username': author.name.text,
                'submitter_realname': '', # Can't get this from Google
                'canonical_bug_link': self.bug_url,
                'looks_closed': (issue.state.text == 'closed')
                }

        labels = [label.text for label in issue.label]
        # Check for the bitesized keyword(s)
        if tm.bitesized_type:
            ret_dict['bite_size_tag_name'] = tm.bitesized_text
            b_list = tm.bitesized_text.split(',')
            ret_dict['good_for_newcomers'] = any(b in labels for b in b_list)
        else:
            ret_dict['bite_size_tag_name'] = ''
            ret_dict['good_for_newcomers'] = False
        # Check whether this is a documentation bug.
        if tm.documentation_type:
            d_list = tm.documentation_text.split(',')
            ret_dict['concerns_just_documentation'] = any(d in labels for d in d_list)
        else:
            ret_dict['concerns_just_documentation'] = False

        # Then pass ret_dict out.
        return ret_dict
