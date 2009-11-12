import urllib2
import urllib
import re
import lxml.html # scraper library
from itertools import chain
import csv
from mysite.search.models import Bug, Project
import datetime
from django.db import models

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


# From http://docs.python.org/library/itertools.html
def flatten(listOfLists):
    return list(chain.from_iterable(listOfLists))

class RoundupBugTracker(models.Model):

    roundup_root_url = models.CharField(max_length=255)
    project = models.ForeignKey(Project)
    csv_url = models.CharField(max_length=255)
    include_these_roundup_bug_statuses = models.CharField(max_length=255, default="-1,1,2,3,4,5,6")
    my_bugs_are_always_good_for_newcomers = models.BooleanField(default=False)

    @property
    def csv_url(self):
        return "%s/issue?%s" % (
                self.roundup_root_url,
                urllib.urlencode({
                    "@action": "export_csv",
                    "@columns": "id", 
                    "@sort": "activity",
                    "@group": "priority",
                    "@filter" : "status",
                    "@startwith": 0,
                    "status": self.include_these_roundup_bug_statuses
                    }))

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

    def get_remote_bug_ids_to_read(self):
        csv_fd = urllib2.urlopen(self.csv_url)

        doc = csv.reader(csv_fd)
        try:
            doc.next()
        except StopIteration:
            raise ValueError, "The CSV was empty."

        for row in doc:
            if row:
                yield int(row[0])

    def get_remote_bug_ids_already_stored(self):
        return [] #FIX. ME.

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

    def create_bug_object_for_remote_bug_id(self, remote_bug_id):
        '''Create but don't save a bug.'''
        remote_bug_url = self.roundup_root_url + "/issue%d" % remote_bug_id
        tree = lxml.html.document_fromstring(urllib2.urlopen(remote_bug_url).read())

        bug = Bug()

        metadata_dict = RoundupBugTracker.roundup_tree2metadata_dict(tree)

        date_reported, bug.submitter_username, last_touched, last_toucher = [
                x.text_content() for x in tree.cssselect(
                    'form[name=itemSynopsis] + p > b, form[name=itemSynopsis] + hr + p > b')]
        bug.submitter_realname = self.get_submitter_realname(tree, bug.submitter_username)
        bug.date_reported = self.str2datetime_obj(date_reported)
        bug.last_touched = self.str2datetime_obj(last_touched)
        bug.canonical_bug_link = remote_bug_url
        bug.good_for_newcomers = self.my_bugs_are_always_good_for_newcomers 
        bug.status = 'open' # True based on its being in the CSV!
        bug.looks_closed = False # False, same reason as above.
        bug.title = metadata_dict['Title'] 
        bug.importance = metadata_dict['Priority']

        # For description, just grab the first "message"
        try:
            bug.description = tree.cssselect('table.messages td.content')[0].text_content().strip()
        except IndexError:
            # This Roundup issue has no messages.
            bug.description = ""

        bug.project = self.project

        # How many people participated?
        bug.people_involved = len(self.get_all_submitter_realname_pairs(tree))

        bug.last_polled = datetime.datetime.utcnow()

        return bug


    def grab(self):
        """Loops over the Python bug tracker's easy bugs and stores/updates them in our DB.
        For now, just grab the easy bugs to be kind to their servers."""

        bug_ids = flatten([self.get_remote_bug_ids_to_read(), self.get_remote_bug_ids_already_stored()])

        for bug_id in bug_ids:
            print bug_id
            bug = self.create_bug_object_for_remote_bug_id(bug_id)

            # If there is already a bug with this canonical_bug_link in the DB, just delete it.
            bugs_this_one_replaces = Bug.all_bugs.filter(canonical_bug_link=
                                                        bug.canonical_bug_link)
            for delete_me in bugs_this_one_replaces:
                delete_me.delete()

            print bug
            # With the coast clear, we save the bug we just extracted from the Miro tracker.
            bug.save()
