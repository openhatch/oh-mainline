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

# From http://docs.python.org/library/itertools.html
def flatten(listOfLists):
    return list(chain(*listOfLists))

class RoundupBugTracker(models.Model):

    name = models.CharField(max_length=255)
    roundup_root_url = models.CharField(max_length=255)
    project = models.ForeignKey(mysite.search.models.Project)
    include_these_roundup_bug_statuses = models.CharField(max_length=255, default="-1,1,2,3,4,5,6")
    my_bugs_are_always_good_for_newcomers = models.BooleanField(default=False)
    my_bugs_concern_just_documentation = models.BooleanField(default=False)
    csv_keyword = models.CharField(max_length=50, null=True, default=None)
    components = models.CharField(max_length=50, null=True, default=None)

    @staticmethod
    def csv_url2bugs(csv_url):
        csv_fd = mysite.customs.ohloh.mechanize_get(
            csv_url).response()

        doc = csv.reader(csv_fd)
        try:
            doc.next()
        except StopIteration:
            raise ValueError, "The CSV was empty."

        for row in doc:
            if row:
                yield int(row[0])

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
        return [] # A separate task fills this in for us.

    def get_remote_bug_ids_already_stored(self):
        bugs = mysite.search.models.Bug.all_bugs.filter(
                canonical_bug_link__contains=self.roundup_root_url)
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

    def get_remote_bug_id(self, bug):
        return int(bug.canonical_bug_link.split(self.roundup_root_url + "/issue")[1])

    def create_bug_object_for_remote_bug_id(self, remote_bug_id):
        '''Create but don't save a bug.'''
        remote_bug_url = self.roundup_root_url + "/issue%d" % remote_bug_id
        tree = lxml.html.document_fromstring(urllib2.urlopen(remote_bug_url).read())

        bug = mysite.search.models.Bug()

        metadata_dict = RoundupBugTracker.roundup_tree2metadata_dict(tree)
        import pdb
        pdb.set_trace()

        date_reported, bug.submitter_username, last_touched, last_toucher = [
                x.text_content() for x in tree.cssselect(
                    'form[name=itemSynopsis] + p > b, form[name=itemSynopsis] + hr + p > b')]
        bug.submitter_realname = self.get_submitter_realname(tree, bug.submitter_username)
        bug.date_reported = self.str2datetime_obj(date_reported)
        bug.last_touched = self.str2datetime_obj(last_touched)
        bug.canonical_bug_link = remote_bug_url

        # FIXME: here is special-case data for python.org
        bug.good_for_newcomers = ('easy' in metadata_dict['Keywords'])
        bug.concerns_just_documentation = ('Documentation' 
                                           in metadata_dict['Components'])
        bug.status = metadata_dict['Status'] 
        bug.looks_closed = (metadata_dict['Status'] == 'closed')
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

    def __unicode__(self):
        return "<Roundup bug tracker for %s>" % self.roundup_root_url

