# This file is part of OpenHatch.

#####################################################
########## THIS IS DEPRECATED #######################
########## WE INTEND TO MOVE THIS CODE ##############
########## INTO A SUBCLASS OF BUGPARSER OR ##########
########## BUGIMPORTER. IT WILL GO AWAY WITHIN ######
########## A MONTH OR SO. ###########################
########## INFO: http://lists.openhatch.org/pipermail/devel/2011-November/002466.html #

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

import cgi
import csv
import datetime
import feedparser
import logging
import urlparse
import urllib2

import dateutil.parser
from mysite.base.depends import lxml

from mysite.base.decorators import cached_property
import mysite.base.helpers
import mysite.base.unicode_sanity
from mysite.customs.models import TracTimeline, TracBugTimes
import mysite.search.models
import mysite.search.templatetags.search

############################################################
# Functions and classes for interacting with the tracker

def csv_of_bugs(url):
    b = mysite.customs.mechanize_helpers.mechanize_get(url)
    return b.response()

def csv_url2list_of_bug_ids(csv_fd):
    dictreader = csv.DictReader(mysite.base.unicode_sanity.wrap_file_object_in_utf8_check(csv_fd))
    return [int(line['id']) for line in dictreader]

class TracBug:
    @staticmethod
    def page2metadata_table(doc):
        ret = {}
        key_ths = doc.cssselect('table.properties th')
        for key_th in key_ths:
            key = key_th.text
            value = key_th.itersiblings().next().text
            if value is not None:
                ret[key.strip()] = value.strip()
        return ret
    
    @staticmethod
    def page2description_div(doc):
        div = doc.cssselect('.description .searchable')[0]
        cleaner = lxml.html.clean.Cleaner(javascript=True, scripts=True, meta=True, page_structure=True, embedded=True, frames=True, forms=True, remove_unknown_tags=True, safe_attrs_only=True, add_nofollow=True)
        return cleaner.clean_html(lxml.html.tostring(div))

    @staticmethod
    def page2date_opened(doc):
        span = doc.cssselect(
            '''.date p:contains("Opened") span,
            .date p:contains("Opened") a''')[0]
        return TracBug._span2date(span)

    @staticmethod
    def page2date_modified(doc):
        try:
            span = doc.cssselect(
                '''.date p:contains("Last modified") span,
                .date p:contains("Last modified") a''')[0]
        except IndexError:
            return TracBug.page2date_opened(doc)
        return TracBug._span2date(span)

    @staticmethod
    def _span2date(span):
        date_string = span.attrib['title']
        date_string = date_string.replace('in Timeline', '')
        date_string = date_string.replace('See timeline at ', '')
        return mysite.base.helpers.string2naive_datetime(date_string)

    @staticmethod
    def all_people_in_changes(doc):
        people = []
        for change_h3 in doc.cssselect('.change h3'):
            text = change_h3.text_content()
            for line in text.split('\n'):
                if 'changed by' in line:
                    person = line.split('changed by')[1].strip()
                    people.append(person)
        return people

    def __init__(self, bug_id, BASE_URL):
        self._bug_specific_csv_data = None
        self._bug_html_page = None
        self._parsed_bug_html_page = None
        self.bug_id = int(bug_id)
        if not BASE_URL.endswith('/'):
            BASE_URL += '/'
        self.BASE_URL = BASE_URL

    @staticmethod
    def from_url(url):
        base, ticket, num = url.rsplit('/', 2)
        bug_id = int(num)
        assert ticket == 'ticket'
        return TracBug(bug_id=bug_id,
                       BASE_URL=base + '/')

    def as_bug_specific_url(self):
        return urlparse.urljoin(self.BASE_URL,
                                "ticket/%d" % self.bug_id)

    def as_bug_specific_csv_url(self):
        return self.as_bug_specific_url() +"?format=csv"

    @cached_property
    def component(self):
        try:
            return self.as_bug_specific_csv_data()['component']
        except KeyError:
            return ''

    def as_bug_specific_csv_data(self):
        if self._bug_specific_csv_data is None:
            b = mysite.customs.mechanize_helpers.mechanize_get(
                self.as_bug_specific_csv_url())
            dr = csv.DictReader(b.response().readlines())
            self._bug_specific_csv_data = dr.next()
        return self._bug_specific_csv_data

    def get_bug_html_page(self):
        if self._bug_html_page is None:
            b = mysite.customs.mechanize_helpers.mechanize_get(
                self.as_bug_specific_url())
            self._bug_html_page = b.response().read()
        return self._bug_html_page

    def get_parsed_bug_html_page(self):
        if self._parsed_bug_html_page is None:
            self._parsed_bug_html_page = lxml.html.fromstring(
                self.get_bug_html_page())
        return self._parsed_bug_html_page

    @staticmethod
    @mysite.base.decorators.unicodify_strings_when_inputted
    def string_un_csv(s):
        """Trac serializes bug descriptions. Undo that serialization."""
        s = cgi.escape(s)
        return s

    def as_data_dict_for_bug_object(self, extract_tracker_specific_data, old_trac=False):
        trac_data = self.as_bug_specific_csv_data()
        html_data = self.get_parsed_bug_html_page()

        # Seems that some Trac bug trackers don't give all the information below.
        # For now, just put the offending item inside a try catch and give it a
        # null case.
        ret = {'title': trac_data['summary'],
               'description': TracBug.string_un_csv(trac_data['description']),
               'status': trac_data['status'],
               'submitter_username': trac_data['reporter'],
               'submitter_realname': '', # can't find this in Trac
               'canonical_bug_link': self.as_bug_specific_url(),
               'concerns_just_documentation': False,
               'as_appears_in_distribution': '',
               'last_polled': datetime.datetime.utcnow(),
               }
        ret['importance'] = trac_data.get('priority', '')

        ret['looks_closed'] = (trac_data['status'] == 'closed')

        page_metadata = TracBug.page2metadata_table(html_data)
        
        all_people = set(TracBug.all_people_in_changes(html_data))
        all_people.add(page_metadata['Reported by:'])
        all_people.update(
            map(lambda x: x.strip(),
                page_metadata.get('Cc', '').split(',')))
        all_people.update(
            map(lambda x: x.strip(),
                page_metadata.get('Cc:', '').split(',')))
        try:
            assignee = page_metadata['Assigned to:']
        except KeyError:
            try:
                assignee = page_metadata['Owned by:']
            except KeyError:
                assignee = ''
        if assignee:
            all_people.add(assignee)

        ret['people_involved'] = len(all_people)

        # FIXME: Need time zone
        if not old_trac:
            # All is fine, proceed as normal.
            ret['date_reported'] = TracBug.page2date_opened(html_data)
            ret['last_touched'] = TracBug.page2date_modified(html_data)

        ret = extract_tracker_specific_data(trac_data, ret)
        return ret

class TracBugTimeline(object):
    def __init__(self, base_url, tracker_name):
        self.tracker_name = tracker_name
        try:
            self.timeline = TracTimeline.all_timelines.get(base_url = base_url)
        except TracTimeline.DoesNotExist:
            self.timeline = TracTimeline(base_url = base_url)
        # Unsure if this is required here, but can't hurt.
        self.timeline.save()

    def generate_timeline_entries_from_rss(self, days_back):
        rss_url = urlparse.urljoin(self.timeline.base_url,
                            "timeline?ticket=on&daysback=%d&format=rss" % days_back)
        logging.info("[Trac] Fetching timeline RSS...")
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            yield entry

    def update(self):
        logging.info("[Trac] Started refreshing timeline for tracker named %s." % self.tracker_name)

        # Check when the timeline was last updated.
        timeline_age = datetime.datetime.utcnow() - self.timeline.last_polled

        # First step is to use the actual timeline to update the date_reported and
        # last_touched fields for each bug.
        # Add one to days count here to account for possible timezone differences.
        for entry in self.generate_timeline_entries_from_rss(timeline_age.days + 1):
            # Format the data.
            entry_url = entry.link.rsplit("#", 1)[0]
            entry_date = datetime.datetime(*entry.date_parsed[0:6])
            entry_status = entry.title.split("): ", 1)[0].rsplit(" ", 1)[1]

            logging.info("[Trac] Updating %s entry on %s for %s" % (entry_status, entry_date, entry_url))
            # Get or create a TracBugTimes object.
            try:
                tb_times = self.timeline.tracbugtimes_set.get(canonical_bug_link = entry_url)
            except TracBugTimes.DoesNotExist:
                tb_times = TracBugTimes(canonical_bug_link = entry_url,
                                        timeline = self.timeline)

            # Set the date values as appropriate.
            if 'created' in entry_status:
                tb_times.date_reported = entry_date
            if tb_times.last_touched < entry_date:
                tb_times.last_touched = entry_date
                # Store entry status as well for use in second step.
                tb_times.latest_timeline_status = entry_status

            # Save the TracBugTimes object.
            tb_times.save()

        # Second step is to use the RSS feed for each individual bug to update the
        # last_touched field. This would be unneccessary if the timeline showed
        # update events as well as creation and closing ones, and in fact later
        # versions of Trac have this option - but then the later versions of Trac
        # also hyperlink to the timeline from the bug, making this all moot.
        # Also, we cannot just use the RSS feed for everything, as it is missing
        # the date_reported time, as well as a lot of information about the bug
        # itself (e.g. Priority).
        for tb_times in self.timeline.tracbugtimes_set.all():
            # Check that the bug has not beeen seen as 'closed' in the timeline.
            # This will reduce network load by not grabbing the RSS feed of bugs
            # whose last_touched info is definitely correct.
            if 'closed' not in tb_times.latest_timeline_status:
                logging.info("[Trac] Grabbing RSS feed for %s" % tb_times.canonical_bug_link)
                feed = feedparser.parse(tb_times.canonical_bug_link + '?format=rss')
                comment_dates =  [datetime.datetime(*e.date_parsed[0:6]) for e in feed.entries]
                # Check if there are comments to grab from.
                if comment_dates:
                    tb_times.last_polled = max(comment_dates)
                    tb_times.save()

        # Finally, update the timeline's last_polled.
        self.timeline.last_polled = datetime.datetime.utcnow()
        self.timeline.save()

    def get_times(self, bug_url):
        bug_times = self.timeline.tracbugtimes_set.get(canonical_bug_link = bug_url)
        return (bug_times.date_reported, bug_times.last_touched)

############################################################
# General bug importing class

class TracBugTracker(object):
    def __init__(self, base_url, tracker_name, bug_project_name_format, old_trac=False):
        self.base_url = base_url
        self.tracker_name = tracker_name
        self.bug_project_name_format = bug_project_name_format
        self.old_trac = old_trac
        if self.old_trac:
            self.tbt = TracBugTimeline(self.base_url, self.tracker_name)

    def generate_bug_ids_from_queries(self, queries):
        for query_name in queries:
            query_url = queries[query_name]
            query_ids = mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
                mysite.customs.bugtrackers.trac.csv_of_bugs(query_url))
            for bug_id in query_ids:
                yield bug_id

    def generate_list_of_bug_ids_to_look_at(self):
        # Override this in a project-tracker-specific subclass.
        raise NotImplementedError

    def generate_bug_project_name(self, trac_bug):
        return self.bug_project_name_format.format(tracker_name=self.tracker_name,
                                                   component=trac_bug.component)

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Override this in a project-tracker-specific subclass.
        raise NotImplementedError

    def update(self):
        if self.old_trac:
            # It's an old version of Trac that doesn't have links from the
            # bugs to the timeline. So we need to update our local copy of
            # the timeline so it is accurate for use later.
            self.tbt.update()

        logging.info("[Trac] Started refreshing all bugs from tracker named %s." % self.tracker_name)

        # First, go through and refresh all the bugs specifically marked
        # as bugs to look at.

        for bug_id in self.generate_list_of_bug_ids_to_look_at():
            self.refresh_one_bug_id(bug_id)

        # Then, refresh them all
        self.refresh_all_bugs()

    def refresh_all_bugs(self):
        for bug in mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link__contains=self.base_url):
            tb = mysite.customs.bugtrackers.trac.TracBug.from_url(
                bug.canonical_bug_link)
            self.refresh_one_bug_id(tb.bug_id)

    def refresh_one_bug_id(self, bug_id):
        tb = mysite.customs.bugtrackers.trac.TracBug(
            bug_id=bug_id,
            BASE_URL=self.base_url)
        bug_url = tb.as_bug_specific_url()
    
        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                canonical_bug_link=bug_url)
        except mysite.search.models.Bug.DoesNotExist:
            bug = mysite.search.models.Bug(canonical_bug_link = bug_url)

        # Hopefully, the bug is so fresh it needs no refreshing.
        if bug.data_is_more_fresh_than_one_day():
            logging.info("[Trac] Bug %d from tracker named %s is fresh. Doing nothing!" % (bug_id, self.tracker_name))
            return # sweet

        # Okay, fine, we need to actually refresh it.
        logging.info("[Trac] Refreshing bug %d from tracker named %s." %
                     (bug_id, self.tracker_name))
        # For some unknown reason, some trackers choose to delete some bugs entirely instead
        # of just marking them as closed. That is fine for bugs we haven't yet pulled, but
        # if the bug is already being tracked then we get a 404 error. This catacher looks
        # for a 404 and deletes the bug if it occurs.
        try:
            data = tb.as_data_dict_for_bug_object(self.extract_tracker_specific_data, self.old_trac)
        except urllib2.HTTPError, e:
            if e.code == 404:
                logging.error("[Trac] ERROR: Bug %d returned 404, deleting..." % bug_id)
                bug.delete()
                return
            else:
                raise e
        if self.old_trac:
            # It's an old version of Trac that doesn't have links from the
            # bugs to the timeline. So we need to fetch these times from
            # the database built earlier.
            (data['date_reported'], data['last_touched']) = self.tbt.get_times(bug_url)

        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # And save the project onto it
        # Project name is taken from either overall project name or individual component name
        # based on the value of the boolean set in the __init__ method.
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=self.generate_bug_project_name(tb))
        if bug.project_id != project_from_name.id:
            bug.project = project_from_name
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()
        logging.info("[Trac] Finished with bug %d from tracker named %s." % (bug_id, self.tracker_name))

############################################################
# Specific sub-classes for individual bug trackers

class OLPCTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                tracker_name='OLPC',
                                base_url='http://dev.laptop.org/',
                                bug_project_name_format='{component}')

    def generate_list_of_bug_ids_to_look_at(self):
        queries = {
                'All bugs':
                    'http://dev.laptop.org/query?status=assigned&status=new&status=reopened&order=priority&format=csv',
                }
        return self.generate_bug_ids_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy'
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords']) or ('sugar-love' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Set as_appears_in_distribution.
        ret_dict['as_appears_in_distribution'] = 'OLPC'
        # Then pass ret_dict back
        return ret_dict

# Copy this generic class to add a new Trac bugtracker
# Remember to set 'enabled' to True
# Notes:
# Base URL: the URL of a bug for the bugtracker, without the 'ticket/1234'
# Tracking URL: go to BASE_URL/query and search for the bugs you want tracked
# bug_project_name_format: the format to be used for the bug's project name
# "{tracker_name}" will be replaced by tracker_name, and "{component}" by the
# component the bug is part of (as taken from the bug's ticket).
class GenTrac(TracBugTracker):
    enabled = False

    def __init__(self):
        TracBugTracker.__init__(self,
                                tracker_name='',
                                base_url='',
                                bug_project_name_format='')

    def generate_list_of_bug_ids_to_look_at(self):
        # Can replace both entries below with an 'All bugs' query.
        queries = {
                'Easy bugs':
                    '',
                'Documentation bugs':
                    ''
                }
        return self.generate_bug_ids_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = ''
        ret_dict['good_for_newcomers'] = ('' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

