import urllib2
import re
import lxml.html # scraper library
from itertools import chain
import csv
from mysite.search.models import Bug, Project
import datetime

# From http://docs.python.org/library/itertools.html
def flatten(listOfLists):
    return list(chain.from_iterable(listOfLists))

class RoundupBugTracker:

    roundup_root_url = ""
    project = None
    csv_url = ""

    def __init__(self, project=None, roundup_root_url=None, append_to_csv_url=""):

        self.project = project
        self.roundup_root_url = roundup_root_url
        self.csv_url = roundup_root_url + ("/issue?@action=export_csv&@columns=id"
                + "&@sort=activity&@group=priority&@filter=keywords,status&@pagesize=50"
                + "&@startwith=0&status=1") + append_to_csv_url

    @staticmethod
    def roundup_date_to_datetime(date_string):
        # FIXME: I make guesses as to the timezone.
        try:
            ret = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M')
        except ValueError:
            ret = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return ret


    @staticmethod
    def roundup_tree2metadata_dict(tree):
        '''For each <a class="classhelp">, get the nearly-sibling <td> with the value
        of that property.'''

        # find the "process" table

        # It lives after the <legend>process</legend>
        legends = tree.cssselect('legend')

        my_table = None
        for legend in legends:
            if legend.text_content().strip() == 'process':
                my_table = legend.getnext()
                assert my_table.tag.lower() == 'table'
        if my_table is None:
            raise ValueError, "Could not find process table."

        ret = {}
        for tr in my_table.cssselect('tr'):
            children_remaining = tr.getchildren()

            while children_remaining:
                th, td = children_remaining.pop(0), children_remaining.pop(0)
                assert th.tag == 'th'
                assert td.tag == 'td'
                key_with_colon = th.text_content().strip()
                key = key_with_colon.rsplit(':', 1)[0]
                value = td.text_content().strip()
                ret[key] = value

        return ret
            

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
        return self.get_all_submitter_realname_pairs(tree)[submitter_username]

    def create_bug_object_for_remote_bug_id(self, remote_bug_id):
        '''Create but don't save a bug.'''
        remote_bug_url = self.roundup_root_url + "/issue%d" % remote_bug_id
        tree = lxml.html.document_fromstring(urllib2.urlopen(remote_bug_url).read())

        bug = Bug()

        metadata_dict = RoundupBugTracker.roundup_tree2metadata_dict(tree)

        date_reported, bug.submitter_username, last_touched, last_toucher = [
                x.text_content() for x in tree.cssselect('form + p > b')]
        bug.submitter_realname = self.get_submitter_realname(tree, bug.submitter_username)
        bug.date_reported = RoundupBugTracker.roundup_date_to_datetime(date_reported)
        bug.last_touched = RoundupBugTracker.roundup_date_to_datetime(last_touched)
        bug.canonical_bug_link = remote_bug_url
        bug.good_for_newcomers = True # No need to check the page - we only grab "easy" bugs!
        bug.status = 'open' # True based on its being in the CSV!
        bug.looks_closed = False # False, same reason as above.
        bug.title = tree.cssselect('input[name="title"]')[0].value
        bug.importance = metadata_dict['Priority']

        # For description, just grab the first "message"
        bug.description = tree.cssselect('table.messages td.content')[0].text_content().strip()

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

# Just testing
python_tracker = RoundupBugTracker(roundup_root_url="http://bugs.python.org",
        project=Project.objects.get_or_create(name='Python', language='Python')[0], append_to_csv_url="&keywords=6")

xemacs_tracker = RoundupBugTracker(roundup_root_url="http://tracker.xemacs.org/XEmacs/its",
        project=Project.objects.get_or_create(name='XEmacs', language='Emacs Lisp')[0])
