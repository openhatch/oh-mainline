# Bug tracker for the OS/Net (core) section of OpenSolaris

# Why just OS/Net? 
# Triskelios and Asheesh discussed this in #opensolaris
#
# <paulproteus> Hello OpenSolaris folks! I'm trying to find a list of good bugs for OpenSolaris newcomers to tackle. I see http://hub.opensolaris.org/bin/view/Main/oss_bite_size which refers to bugs.opensolaris.org. But there's a "Bugzilla" link on the side which goes to defect.opensolaris.org.
# <paulproteus> What is the difference, and is it sensible to look at bugs-dot like I am now?

# <Triskelios> b.o.o is a frontend to Sun's internal Bugster system and has a fairly poor interface for non-Sun users, while defect is relatively new and doesn't have this discrepancy
# <Triskelios> I'm pretty sure not all of the Bugster metadata is exposed by b.o.o
# <Triskelios> paulproteus: most ON (OS/Net, i.e. kernel and core userland) bugs are tracked in Bugster partially because many Sun engineers are not even aware of defect yet, and because some processes are still tied to Bugster IDs. issues for the OpenSolaris distro (packaging, installation, etc.) as well as desktop projects use defect at the moment
# <paulproteus> And it seems the Bugster stuff can't be commented-on by non-Sun-engineers.
# <Triskelios> right. ON commits normally require a Sun sponsor to sign off, so communication is usually over email, and the sponsoring engineer may update the bug

# <Triskelios> paulproteus: try emailing tools-discuss, or William.Rushmore@Sun, who seems to have been the bite-size list maintainer


import urllib2
import re
import lxml.html # scraper library
from itertools import chain
import csv
from mysite.search.models import Bug, Project
import datetime
from mysite.customs.models import flatten

def view_bug_table2dict(tree):
    # Find the big table that contains the bug data
    metadata_table = tree.cssselect('table.NoBorder [cellspacing="0"]')[0]

    ret = {}
    
    # Extract it out thrillingly
    for row in metadata_table.cssselect('tr'):
        key_elt, value_elt = row.cssselect('td')
        key = key_elt.text_content().strip()
        value = value_elt.text_content().strip()
        ret[key] = value

    return ret

def decode_datetime(s):
    return datetime.datetime.strptime(s, '%d-%B-%Y')

def create_bug_object_for_remote_bug_id(remote_bug_id):
    '''Create but don't save a bug.'''
    remote_bug_url = "http://bugs.opensolaris.org/bugdatabase/view_bug.do?bug_id=%d" % remote_bug_id
    try:
        tree = lxml.html.document_fromstring(urllib2.urlopen(remote_bug_url).read())
    except urllib2.HTTPError, e:
        if e.code == 404:
            return None
        # otherwise, bubble that crazy error up.
        raise e

    bug = Bug()

    metadata_dict = view_bug_table2dict(tree)

    bug.submitter_username = '' # FIXME: Find an example of this having a value
    bug.submitter_realname = '' # FIXME: Find an example of this having a value
    bug.date_reported = decode_datetime(metadata_dict['Submit Date'])
    bug.last_touched = decode_datetime(metadata_dict['Last Update Date'])
    bug.canonical_bug_link = remote_bug_url
    bug.good_for_newcomers = 'oss-bite-size' in metadata_dict['Keywords']
    bug.status = metadata_dict['State']
    status_number = int(bug.status.split('-')[0])
    bug.looks_closed = (status_number in (8, 10, 11))
    bug.title = metadata_dict['Synopsis']
    bug.importance = '' # No importance, as far as I can tell.

    # For description, just grab the first "message"
    bug.description = metadata_dict['Description']

    # We are always the project called Python.
    bug.project, _ = Project.objects.get_or_create(name='OpenSolaris OS/Net', language='C')

    # How many people participated?
    bug.people_involved = None # This tracker has no idea.

    bug.last_polled = datetime.datetime.utcnow()

    return bug

BUG_URL_PREFIX = 'http://bugs.opensolaris.org/bugdatabase/view_bug.do?bug_id='

def get_remote_bug_ids_to_read():
    remote_bug_list = 'http://hub.opensolaris.org/bin/view/Main/oss_bite_size'
    tree = lxml.html.document_fromstring(urllib2.urlopen(remote_bug_list).read())
    for a in tree.cssselect('a'):
        if BUG_URL_PREFIX in (
            a.attrib.get('href', '')):
            yield bug_url2bug_id(a.attrib['href'])

def bug_url2bug_id(url):
    return int(url.replace(BUG_URL_PREFIX, ''))

def get_remote_bug_ids_already_stored():
    for bug in Bug.all_bugs.filter(canonical_bug_link__contains=BUG_URL_PREFIX):
        yield bug_url2bug_id(bug.canonical_bug_link)

def grab():
    """Loops over the OpenSolaris bug tracker's oss-bite-sized bugs and stores/updates them in our DB.
    For now, just grab the easy bugs to be kind to their servers."""

    bug_ids = flatten([get_remote_bug_ids_to_read(), get_remote_bug_ids_already_stored()])

    for bug_id in bug_ids:
        # Sometimes create_bug_object_for_remote_bug_id will fail to create
        # a bug because it's somehow gone missing. For those cases:

        # create canonical_bug_link in this function to avoid assuming the
        # returned bug is not None.
        canonical_bug_link = BUG_URL_PREFIX + str(bug_id)

        # Try to create a bug. Now, it might return None...
        bug = create_bug_object_for_remote_bug_id(bug_id)

        # If there is already a bug with this canonical_bug_link in
        # the DB, just delete it. Same story if the bug doens't 404!
        bugs_this_one_replaces = Bug.all_bugs.filter(canonical_bug_link=
                                                     canonical_bug_link)
        for delete_me in bugs_this_one_replaces:
            delete_me.delete()

        # If the bug is None, we're done here.
        if bug is None:
            continue

        # Otherwise, print and save the sucker!
        print bug
        bug.save()
