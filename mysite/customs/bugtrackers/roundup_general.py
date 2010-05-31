import urllib2
import urllib
import re
import lxml.html # scraper library
from itertools import chain
import csv
import datetime
import logging
import urlparse

from django.db import models

import mysite.search.models
import mysite.customs.ohloh

def csv_url2bugs(csv_url):
    csv_fd = mysite.customs.ohloh.mechanize_get(
        csv_url).response()
    dict_reader = csv.DictReader(csv_fd)
    for thing in dict_reader:
        yield int(thing['id'])

class RoundupTracker(object):
    def __init__(self, root_url, project_name):
        assert root_url[-1] == '/'
        assert root_url[-2] != '/'
        self.root_url = unicode(root_url)
        self.project = mysite.search.models.Project.objects.get(name=project_name)

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

    def get_remote_bug_ids_already_stored(self):
        bugs = mysite.search.models.Bug.all_bugs.filter(
                canonical_bug_link__contains=self.root_url)
        bug_ids = [self.get_remote_bug_id(bug) for bug in bugs]
        return bug_ids

    def get_all_submitter_realname_pairs(self, tree):
        '''Input: the tree
        Output: A dictionary mapping username=>realname'''

        ret = {}
        for th in tree.cssselect('th'):
            match = re.match("Author: ([^(]*) \(([^)]*)", th.text_content().strip())
            if match:
                realname, username = match.groups()
                ret[username] = realname
        return ret

    def get_submitter_realname(self, tree, submitter_username):
        try:
            return self.get_all_submitter_realname_pairs(tree)[submitter_username]
        except KeyError:
            return None

    def remote_bug_id2url(self, remote_bug_id):
        return urlparse.urljoin(self.root_url, "issue%d" % remote_bug_id)

    def get_remote_bug_id(self, bug):
        plus_slash_issue = urlparse.urljoin(self.root_url, 'issue')
        return int(bug.canonical_bug_link.split(plus_slash_issue)[1])

    def create_bug_object_for_remote_bug_id_if_necessary(self, remote_bug_id):
        """See if we have either no bug or only a stale one. If so,
        refresh."""
        logging.info(
            "Was asked to look at bug %d in %s" % (remote_bug_id, self.project.name))
        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                canonical_bug_link=self.remote_bug_id2url(remote_bug_id))
            if bug.data_is_more_fresh_than_one_day():
                return False
        except mysite.search.models.Bug.DoesNotExist:
            bug = mysite.search.models.Bug()
            bug.canonical_bug_link = self.remote_bug_id2url(remote_bug_id)

        # otherwise, fill the bug object with fresh data
        bug = self._update_bug_object_for_remote_bug_id(
            bug_object=bug,
            remote_bug_id=remote_bug_id)
        bug.save()
        logging.info(
            "Actually loaded %d in from %s" % (
                remote_bug_id, self.project.name))
        return True

    def _update_bug_object_for_remote_bug_id(self, bug_object, remote_bug_id):
        """Create but don't save a bug."""
        remote_bug_url = self.remote_bug_id2url(remote_bug_id)
        tree = lxml.html.document_fromstring(urllib2.urlopen(remote_bug_url).read())

        metadata_dict = RoundupTracker.roundup_tree2metadata_dict(tree)

        date_reported, bug_object.submitter_username, last_touched, last_toucher = [
                x.text_content() for x in tree.cssselect(
                    'form[name=itemSynopsis] + p > b, form[name=itemSynopsis] + hr + p > b')]
        bug_object.submitter_realname = self.get_submitter_realname(tree, bug_object.submitter_username)
        bug_object.date_reported = self.str2datetime_obj(date_reported)
        bug_object.last_touched = self.str2datetime_obj(last_touched)
        bug_object.canonical_bug_link = remote_bug_url

        bug_object.status = metadata_dict['Status'] 
        bug_object.looks_closed = (metadata_dict['Status'] == 'closed')
        bug_object.title = metadata_dict['Title'] 
        bug_object.importance = metadata_dict['Priority']

        # For description, just grab the first "message"
        try:
            bug_object.description = tree.cssselect('table.messages td.content')[0].text_content().strip()
        except IndexError:
            # This Roundup issue has no messages.
            bug_object.description = ""

        bug_object.project = self.project

        # How many people participated?
        bug_object.people_involved = len(self.get_all_submitter_realname_pairs(tree))

        bug_object.last_polled = datetime.datetime.utcnow()

        self.extract_bug_tracker_specific_data(metadata_dict=metadata_dict,
                                               bug_object=bug_object)

        return bug_object

    def extract_bug_tracker_specific_data(self, metadata_dict, bug_object):
        raise RuntimeError(NotImplemented)

    def grab(self):
        """Loops over the Python bug tracker's easy bugs and stores/updates them in our DB.
        For now, just grab the easy bugs to be kind to their servers."""

        bug_ids = flatten([self.get_remote_bug_ids_to_read(),
                self.get_remote_bug_ids_already_stored()])

        for bug_id in bug_ids:
            print bug_id
            bug = self.create_bug_object_for_remote_bug_id(bug_id)

            # If there is already a bug with this canonical_bug_link in the DB, just delete it.
            bugs_this_one_replaces = mysite.search.models.Bug.all_bugs.filter(canonical_bug_link=
                                                        bug.canonical_bug_link)
            for delete_me in bugs_this_one_replaces:
                delete_me.delete()

            print bug
            # With the coast clear, we save the bug we just extracted from the Miro tracker.
            bug.save()

    def update(self):
        '''Call this nightly.'''
        logging.info("Learning about new bugs in %s" % self.project.name)

        # First, find an examine any new bugs.
        for bug_id in self.generate_list_of_bug_ids_to_look_at():
            self.create_bug_object_for_remote_bug_id_if_necessary(bug_id)
        # Second, make sure old bugs in the database aren't too stale.
        logging.info("Starting refreshing all bugs from %s." % self.project.name)
        count = 0
        for bug_id in self.get_remote_bug_ids_already_stored():
            self.create_bug_object_for_remote_bug_id_if_necessary(bug_id=bug_id)
            count += 1
        logging.info("Okay, looked at %d bugs from %s." % (
                count, self.project.name))

    def __unicode__(self):
        return "<Roundup bug tracker for %s>" % self.root_url

class MercurialTracker(RoundupTracker):
    enabled = True

    def __init__(self):
        RoundupTracker.__init__(self,
                                root_url='http://mercurial.selenic.com/bts/',
                                project_name='Mercurial')

    def extract_bug_tracker_specific_data(self, metadata_dict, bug_object):
        if 'bitesized' in metadata_dict['Topics']:
            bug_object.good_for_newcomers = True
        if 'documentation' in metadata_dict['Topics']:
            bug_object.concerns_just_documentation = True

    def generate_list_of_bug_ids_to_look_at(self):
        # Bitesized bugs
        for bug_id in csv_url2bugs(
            'http://mercurial.selenic.com/bts/issue?@action=export_csv&@columns=title,id,activity,status,assignedto&@sort=activity&@group=priority&@filter=topic&@pagesize=500&@startwith=0&topic=61'):
            yield bug_id
            
        # Documentation bugs
        for bug_id in csv_url2bugs(
                'http://mercurial.selenic.com/bts/issue?@action=export_csv&@columns=title,id,activity,status,assignedto&@sort=activity&@group=priority&@filter=topic&@pagesize=500&@startwith=0&topic=10'):
            yield bug_id
        
class PythonTracker(RoundupTracker):
    enabled = True

    def __init__(self):
        RoundupTracker.__init__(self,
                                root_url='http://bugs.python.org/',
                                project_name='Python')

    def extract_bug_tracker_specific_data(self, metadata_dict, bug_object):
        bug_object.good_for_newcomers = (
            'easy' in metadata_dict['Keywords'])
        bug_object.concerns_just_documentation = (
            'Documentation' in metadata_dict['Components'])
        bug_object.status = metadata_dict['Status']
        bug_object.looks_closed = (
            metadata_dict['Status'] == 'closed' or
            'patch' in metadata_dict['Keywords'])
        bug_object.importance = metadata_dict['Priority']

    def generate_list_of_bug_ids_to_look_at(self):
        ### bug queries to look at
        queries = {
            'Documentation bugs':
                'http://bugs.python.org/issue?status=1%2C3&%40sort=activity&%40columns=id&%40startwith=0&%40group=priority&%40filter=status%2Ccomponents&components=4&%40action=export_csv',
            'Easy bugs':
                'http://bugs.python.org/issue?status=1%2C3&%40sort=activity&%40columns=id&%40startwith=0&%40group=priority&%40filter=status%2Ckeywords&keywords=6&%40action=export_csv',
            }

        for query_name in queries:
            query_url = queries[query_name]
            for bug_id in csv_url2bugs(query_url):
                yield bug_id
