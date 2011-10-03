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

import csv
import datetime
import lxml.html
import re
import urlparse

from mysite.base.decorators import cached_property
import mysite.base.helpers
from mysite.customs.bugimporters.base import BugImporter
import mysite.search.models

class RoundupBugImporter(BugImporter):
    def __init__(self, *args, **kwargs):
        # Create a list to store bug ids obtained from queries.
        self.bug_ids = []
        # Call the parent __init__.
        super(RoundupBugImporter, self).__init__(*args, **kwargs)

    def process_queries(self, queries):
        # Add all the queries to the waiting list
        for query in queries:
            query_url = query.get_query_url()
            self.add_url_to_waiting_list(
                    url=query_url,
                    callback=self.handle_query_csv)
            query.last_polled = datetime.datetime.utcnow()
            query.save()

        # URLs are now all prepped, so start pushing them onto the reactor.
        self.push_urls_onto_reactor()

    def handle_query_csv(self, query_csv):
        # Turn the string into a list so csv.DictReader can handle it.
        query_csv_list = query_csv.split('\n')
        dictreader = csv.DictReader(query_csv_list)
        self.bug_ids.extend([int(line['id']) for line in dictreader])

    def prepare_bug_urls(self):
        # Pull bug_ids out of the internal storage. This is done in case the
        # list is simultaneously being written to, in which case just copying
        # the entire thing followed by deleting the contents could lead to
        # lost IDs.
        bug_id_list = self.bug_ids[:] # this is called 'slice copy'

        # Convert the obtained bug ids to URLs.
        bug_url_list = [urlparse.urljoin(self.tm.get_base_url(),
                                "issue%d" % bug_id) for bug_id in bug_id_list]

        # Get the sub-list of URLs that are fresh.
        fresh_bug_urls = mysite.search.models.Bug.all_bugs.filter(
                canonical_bug_link__in=bug_url_list,
                last_polled__lt=datetime.datetime.now()-datetime.timedelta(days=1)
            ).values_list('canonical_bug_link', flat=True)

        # Remove the fresh URLs to be let with stale or new URLs.
        stale_bug_urls = [bug_url for bug_url in bug_url_list
                          if bug_url not in fresh_bug_urls]

        # Put the bug list in the form required for process_bugs.
        # The second entry of the tuple is None as Roundup never supplies data
        # via queries.
        bug_list = [(bug_url, None) for bug_url in stale_bug_urls]

        # And now go on to process the bug list
        self.process_bugs(bug_list)

    def process_bugs(self, bug_list):
        # If there are no bug URLs, finish now.
        if not bug_list:
            self.determine_if_finished()
            return

        for bug_url, _ in bug_list:
            # Create a RoundupBugParser instance to store the bug data
            rbp = RoundupBugParser(bug_url)

            self.add_url_to_waiting_list(
                    url=rbp.bug_html_url,
                    callback=self.handle_bug_html,
                    c_args={'rbp': rbp})

        # URLs are now all prepped, so start pushing them onto the reactor.
        self.push_urls_onto_reactor()

    def handle_bug_html(self, bug_html, rbp):
        # Pass the RoundupBugParser the HTML data.
        rbp.set_bug_html_data(bug_html)

        # Get the parsed data dict from the RoundupBugParser.
        data = rbp.get_parsed_data_dict(self.tm)

        # Get or create a Bug object to put the parsed data in.
        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                canonical_bug_link=rbp.bug_url)
        except mysite.search.models.Bug.DoesNotExist:
            bug = mysite.search.models.Bug(canonical_bug_link=rbp.bug_url)

        # Fill the Bug.
        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # Save the project onto it.
        # Project name is just the TrackerModel's tracker_name, as due to the
        # way Roundup is set up, there is almost always one project per tracker.
        # This could in theory not be the case, but until we find a Roundup
        # tracker handling bugs for multiple projects, we will just support one
        # project per tracker.
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=self.tm.tracker_name)
        # Manually save() the Project to ensure that if it was created then it has
        # a display_name.
        if not project_from_name.display_name:
            project_from_name.save()
        bug.project = project_from_name

        # Store the tracker that generated the Bug, update last_polled and save it!
        bug.tracker = self.tm
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()

    def determine_if_finished(self):
        # If we got here then there are no more URLs in the waiting list.
        # So if self.bug_ids is also empty then we are done.
        if self.bug_ids:
            self.prepare_bug_urls()
        else:
            self.finish_import()

class RoundupBugParser(object):
    def __init__(self, bug_url):
        self.bug_html = None
        self.bug_url = bug_url

    @cached_property
    def bug_html_url(self):
        return self.bug_url

    def set_bug_html_data(self, bug_html):
        self.bug_html = lxml.html.document_fromstring(bug_html)

    @staticmethod
    def roundup_tree2metadata_dict(tree):
        '''
        Input: tree is a parsed HTML document that lxml.html can understand.

        Output: For each <th>key</th><td>value</td> in the tree,
        append {'key': 'value'} to a dictionary.
        Return the dictionary when done.'''

        ret = {}
        for th in tree.cssselect('th'):
            # Get next sibling
            key_with_colon = th.text_content().strip()
            key = key_with_colon.rsplit(':', 1)[0]
            try:
                td = th.itersiblings().next()
            except StopIteration:
                # If there isn't an adjacent TD, don't use this TH.
                continue
            value = td.text_content().strip()
            ret[key] = value

        return ret

    def get_all_submitter_realname_pairs(self, tree):
        '''Input: the tree
        Output: A dictionary mapping username=>realname'''

        ret = {}
        for th in tree.cssselect('th'):
            match = re.match("Author: (([^(]*) \()?([^)]*)", th.text_content().strip())
            if match:
                _, realname, username = match.groups()
                ret[username] = realname
        return ret

    def get_submitter_realname(self, tree, submitter_username):
        try:
            return self.get_all_submitter_realname_pairs(tree)[submitter_username]
        except KeyError:
            return None

    def str2datetime_obj(self, date_string, possibility_index=0):
        # FIXME: I make guesses as to the timezone.
        possible_date_strings = [
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d.%H:%M",
                "%Y-%m-%d.%H:%M:%S"]
        try:
            return datetime.datetime.strptime(date_string, possible_date_strings[possibility_index])
        except ValueError:
            # A keyerror raised here means we ran out of a possibilities.
            return self.str2datetime_obj(date_string, possibility_index=possibility_index+1)

    def get_parsed_data_dict(self, tm):
        metadata_dict = RoundupBugParser.roundup_tree2metadata_dict(self.bug_html)

        date_reported, submitter_username, last_touched, last_toucher = [
                x.text_content() for x in self.bug_html.cssselect(
                    'form[name=itemSynopsis] + p > b, form[name=itemSynopsis] + hr + p > b, ' +
                    'form[name=itemSynopsis] + p > strong, form[name=itemSynopsis] + hr + p > strong')]

        # For description, just grab the first "message"
        try:
            description = self.bug_html.cssselect('table.messages td.content')[0].text_content().strip()
        except IndexError:
            # This Roundup issue has no messages.
            description = ""

        ret = {'title': metadata_dict['Title'],
               'description': description,
               'importance': metadata_dict['Priority'],
               'status': metadata_dict['Status'],
               'looks_closed': (metadata_dict['Status'] == tm.closed_status),
               'submitter_username': submitter_username,
               'submitter_realname': self.get_submitter_realname(
                   self.bug_html,
                   submitter_username),
               'people_involved': len(self.get_all_submitter_realname_pairs(self.bug_html)),
               'date_reported': self.str2datetime_obj(date_reported),
               'last_touched': self.str2datetime_obj(last_touched),
               'canonical_bug_link': self.bug_url,
               'last_polled': datetime.datetime.utcnow(),
               }

        # Check for the bitesized keyword
        if tm.bitesized_field:
            ret['bite_size_tag_name'] = tm.bitesized_text
            b_list = tm.bitesized_text.split(',')
            ret['good_for_newcomers'] = any(b in metadata_dict.get(tm.bitesized_field, '') for b in b_list)
        else:
            ret['good_for_newcomers'] = False
        # Check whether this is a documentation bug.
        if tm.documentation_field:
            d_list = tm.documentation_text.split(',')
            ret['concerns_just_documentation'] = any(d in metadata_dict.get(tm.documentation_field, '') for d in d_list)
        else:
            ret['concerns_just_documentation'] = False

        # Set as_appears_in_distribution.
        ret['as_appears_in_distribution'] = tm.as_appears_in_distribution

        # Then pass ret out
        return ret
