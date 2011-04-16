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

import datetime
import lxml.etree
import twisted.web.error
import twisted.web.http
import urlparse

from mysite.base.decorators import cached_property
import mysite.base.helpers
from mysite.customs.bugimporters.base import BugImporter
import mysite.search.models

class BugzillaBugImporter(BugImporter):
    def __init__(self, *args, **kwargs):
        # Create a list to store bug ids obtained from queries.
        self.bug_ids = []
        # Call the parent __init__.
        super(BugzillaBugImporter, self).__init__(*args, **kwargs)

    def process_queries(self, queries):
        # Add all the queries to the waiting list.
        for query in queries:
            # Get the query URL.
            query_url = query.get_query_url()
            # Get the query type and set the callback.
            query_type = query.query_type
            if query_type == 'xml':
                callback = self.handle_query_html
            else:
                callback = self.handle_tracking_bug_xml
            # Add the query URL and callback.
            self.add_url_to_waiting_list(
                    url=query_url,
                    callback=callback)
            # Update query.last_polled and save it.
            query.last_polled = datetime.datetime.utcnow()
            query.save()

        # URLs are now all prepped, so start pushing them onto the reactor.
        self.push_urls_onto_reactor()

    def handle_query_html(self, query_html_string):
        # Turn the string into an HTML tree that can be parsed to find the list
        # of bugs hidden in the 'XML' form.
        query_html = lxml.etree.HTML(query_html_string)
        # Find all form inputs at the level we want.
        # This amounts to around three forms.
        query_form_inputs = query_html.xpath('/html/body/div/table/tr/td/form/input')
        # Extract from this the inputs corresponding to 'ctype' fields.
        ctype_inputs = [i for i in query_form_inputs if 'ctype' in i.values()]
        # Limit this to inputs with 'ctype=xml'.
        ctype_xml = [i for i in ctype_inputs if 'xml' in i.values()]
        if ctype_xml:
            # Get the 'XML' form.
            xml_form = ctype_xml[0].getparent()
            # Get all its children.
            xml_inputs = xml_form.getchildren()
            # Extract from this all bug id inputs.
            bug_id_inputs = [i for i in xml_inputs if 'id' in i.values()]
            # Convert this to a list of bug ids.
            bug_id_list = [int(i.get('value')) for i in bug_id_inputs]
            # Add them to self.bug_ids.
            self.bug_ids.extend(bug_id_list)

    def handle_tracking_bug_xml(self, tracking_bug_xml_string):
        # Turn the string into an XML tree.
        tracking_bug_xml = lxml.etree.XML(tracking_bug_xml_string)
        # Find all the bugs that this tracking bug depends on.
        depends = tracking_bug_xml.findall('bug/dependson')
        # Add them to self.bug_ids.
        self.bug_ids.extend([int(depend.text) for depend in depends])

    def prepare_bug_urls(self):
        # Pull bug_ids our of the internal storage. This is done in case the
        # list is simultaneously being written to, in which case just copying
        # the entire thing followed by deleting the contents could lead to
        # lost IDs.
        bug_id_list = []
        while self.bug_ids:
            bug_id_list.append(self.bug_ids.pop())

        # Convert the obtained bug ids to URLs.
        bug_url_list = [urlparse.urljoin(self.tm.get_base_url(),
                                "show_bug.cgi?id=%d" % bug_id) for bug_id in bug_id_list]

        # Get the sub-list of URLs that are fresh.
        fresh_bug_urls = mysite.search.models.Bug.all_bugs.filter(
                canonical_bug_link__in = bug_url_list,
                last_polled__lt = datetime.datetime.now() - datetime.timedelta(days = 1)
            ).values_list('canonical_bug_link', flat=True)

        # Remove the fresh URLs to be let with stale or new URLs.
        for bug_url in fresh_bug_urls:
            bug_url_list.remove(bug_url)

        # Put the bug list in the form required for process_bugs.
        # The second entry of the tuple is None as Bugzilla doesn't supply data
        # in the queries above (although it does support grabbing data for
        # multiple bugs at once, when all the bug ids are known.
        bug_list = [(bug_url, None) for bug_url in bug_url_list]

        # And now go on to process the bug list
        self.process_bugs(bug_list)

    def process_bugs(self, bug_list):
        # If there are no bug URLs, finish now.
        if not bug_list:
            self.determine_if_finished()
            return

        # Convert the bug URLs into bug ids.
        bug_id_list = []
        for bug_url, _ in bug_list:
            base, num = bug_url.rsplit('=', 1)
            bug_id = int(num)
            bug_id_list.append(bug_id)

        # Create a single URL to fetch all the bug data.
        big_url = urlparse.urljoin(
                self.tm.get_base_url(),
                'show_bug.cgi?ctype=xml&excludefield=attachmentdata')
        for bug_id in bug_id_list:
            big_url += '&id=%d' % bug_id

        # Fetch the bug data.
        self.add_url_to_waiting_list(
                url=big_url,
                callback=self.handle_bug_xml,
                c_args={},
                errback=self.errback_bug_xml,
                e_args={'bug_id_list': bug_id_list})

        # URLs are now all prepped, so start pushing them onto the reactor.
        self.push_urls_onto_reactor()

    def errback_bug_xml(self, failure, bug_id_list):
        # Check if the failure was related to the size of the request.
        size_related_errors = [
                twisted.web.http.REQUEST_ENTITY_TOO_LARGE,
                twisted.web.http.REQUEST_TIMEOUT,
                twisted.web.http.REQUEST_URI_TOO_LONG
                ]
        if failure.check(twisted.web.error.Error) and failure.value.status in size_related_errors:
            big_url_base = urlparse.urljoin(
                    self.tm.get_base_url(),
                    'show_bug.cgi?ctype=xml&excludefield=attachmentdata')
            # Split bug_id_list into pieces, and turn each piece into a URL.
            # Note that (floor division)+1 is used to ensure that for
            # odd-numbered lists we don't end up with one bug id left over.
            split_bug_id_list = []
            num_ids = len(bug_id_list)
            step = (num_ids//2)+1
            for i in xrange(0, num_ids, step):
                bug_id_list_fragment = bug_id_list[i:i+step]
                # Check the fragment actually has bug ids in it.
                if not bug_id_list_fragment:
                    # This is our recursive end-point.
                    continue

                # Create the URL for the fragment of bug ids.
                big_url = big_url_base
                for bug_id in bug_id_list_fragment:
                    big_url += '&id=%d' % bug_id

                # Fetch the reduced bug data.
                self.add_url_to_waiting_list(
                        url=big_url,
                        callback=self.handle_bug_xml,
                        c_args={},
                        errback=self.errback_bug_xml,
                        e_args={'bug_id_list': bug_id_list_fragment})

        else:
            # Pass the Failure on.
            return failure

    def handle_bug_xml(self, bug_list_xml_string):
        # Turn the string into an XML tree.
        bug_list_xml = lxml.etree.XML(bug_list_xml_string)
        for bug_xml in bug_list_xml.xpath('bug'):
            # Create a BugzillaBugParser with the XML data.
            bbp = BugzillaBugParser(bug_xml)

            # Get the parsed data dict from the BugzillaBugParser.
            data = bbp.get_parsed_data_dict(self.tm)

            # Get or create a Bug object to put the parsed data in.
            try:
                bug = mysite.search.models.Bug.all_bugs.get(
                    canonical_bug_link=bbp.bug_url)
            except mysite.search.models.Bug.DoesNotExist:
                bug = mysite.search.models.Bug(canonical_bug_link=bbp.bug_url)

            # Fill the Bug
            for key in data:
                value = data[key]
                setattr(bug, key, value)

            # Save the project onto it
            # Project name is generated from the bug_project_name_format property
            # of the TrackerModel.
            project_from_name, _ = mysite.search.models.Project.objects.get_or_create(
                    name=self.generate_bug_project_name(bbp))
            # Manually save() the Project to ensure that if it was created then it has
            # a display_name.
            project_from_name.save()
            bug.project = project_from_name

            # Store the tracker that generated the Bug, update last_polled and save it!
            bug.tracker = self.tm
            bug.last_polled = datetime.datetime.utcnow()
            bug.save()

    def generate_bug_project_name(self, bbp):
        return self.tm.bug_project_name_format.format(
                tracker_name=self.tm.tracker_name,
                product=bbp.product,
                component=bbp.component)

    def determine_if_finished(self):
        # If we got here then there are no more URLs in the waiting list.
        # So if self.bug_ids is also empty then we are done.
        if self.bug_ids:
            self.prepare_bug_urls()
        else:
            self.finish_import()

class BugzillaBugParser:
    @staticmethod
    def get_tag_text_from_xml(xml_doc, tag_name, index = 0):
        """Given an object representing <bug><tag>text</tag></bug>,
        and tag_name = 'tag', returns 'text'."""
        tags = xml_doc.xpath(tag_name)
        try:
            return tags[index].text
        except IndexError:
            return ''

    def __init__(self, bug_xml):
        self.bug_xml = bug_xml
        self.bug_id = self._bug_id_from_bug_data()
        self.bug_url = None # This gets filled in the data parser.

    def _bug_id_from_bug_data(self):
        return int(self.get_tag_text_from_xml(self.bug_xml, 'bug_id'))

    @cached_property
    def product(self):
        return self.get_tag_text_from_xml(self.bug_xml, 'product')

    @cached_property
    def component(self):
        return self.get_tag_text_from_xml(self.bug_xml, 'component')

    @staticmethod
    def _who_tag_to_username_and_realname(who_tag):
        username = who_tag.text
        realname = who_tag.attrib.get('name', '')
        return username, realname

    @staticmethod
    def bugzilla_count_people_involved(xml_doc):
        """Strategy: Create a set of all the listed text values
        inside a <who ...>(text)</who> tag
        Return the length of said set."""
        everyone = [tag.text for tag in xml_doc.xpath('.//who')]
        return len(set(everyone))

    @staticmethod
    def bugzilla_date_to_datetime(date_string):
        return mysite.base.helpers.string2naive_datetime(date_string)

    def get_parsed_data_dict(self, tm):
        # Generate the bug_url.
        self.bug_url = urlparse.urljoin(
                tm.get_base_url(),
                'show_bug.cgi?id=%d' % self.bug_id)

        xml_data = self.bug_xml

        date_reported_text = self.get_tag_text_from_xml(xml_data, 'creation_ts')
        last_touched_text = self.get_tag_text_from_xml(xml_data, 'delta_ts')
        u, r = self._who_tag_to_username_and_realname(xml_data.xpath('.//reporter')[0])
        status = self.get_tag_text_from_xml(xml_data, 'bug_status')
        looks_closed = status in ('RESOLVED', 'WONTFIX', 'CLOSED', 'ASSIGNED')

        ret_dict = {
            'title': self.get_tag_text_from_xml(xml_data, 'short_desc'),
            'description': (self.get_tag_text_from_xml(xml_data, 'long_desc/thetext') or
                           '(Empty description)'),
            'status': status,
            'importance': self.get_tag_text_from_xml(xml_data, 'bug_severity'),
            'people_involved': self.bugzilla_count_people_involved(xml_data),
            'date_reported': self.bugzilla_date_to_datetime(date_reported_text),
            'last_touched': self.bugzilla_date_to_datetime(last_touched_text),
            'submitter_username': u,
            'submitter_realname': r,
            'canonical_bug_link': self.bug_url,
            'looks_closed': looks_closed
            }
        keywords_text = self.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        # Check for the bitesized keyword
        if tm.bitesized_type:
            ret_dict['bite_size_tag_name'] = tm.bitesized_text
            b_list = tm.bitesized_text.split(',')
            if tm.bitesized_type == 'key':
                ret_dict['good_for_newcomers'] = any(b in keywords for b in b_list)
            elif tm.bitesized_type == 'wboard':
                whiteboard_text = self.get_tag_text_from_xml(xml_data, 'status_whiteboard')
                ret_dict['good_for_newcomers'] = any(b in whiteboard_text for b in b_list)
            else:
                ret_dict['good_for_newcomers'] = False
        else:
            ret_dict['good_for_newcomers'] = False
        # Check whether this is a documentation bug.
        if tm.documentation_type:
            d_list = tm.documentation_text.split(',')
            if tm.documentation_type == 'key':
                ret_dict['concerns_just_documentation'] = any(d in keywords for d in d_list)
            elif tm.documentation_type == 'comp':
                ret_dict['concerns_just_documentation'] = any(d == self.component for d in d_list)
            elif tm.documentation_type == 'prod':
                ret_dict['concerns_just_documentation'] = any(d == self.product for d in d_list)
            else:
                ret_dict['concerns_just_documentation'] = False
        else:
            ret_dict['concerns_just_documentation'] = False
        # And pass ret_dict on.
        return ret_dict
