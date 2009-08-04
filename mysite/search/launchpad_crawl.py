# vim: set columns=80:
import os
import datetime

# Initialize Launchpad scraper thing
from launchpadbugs.connector import ConnectBug, ConnectBugList
from launchpadbugs.basebuglistfilter import URLBugListFilter

# Initialize data dumpers
import lpb2json
import simplejson

import simplejson
import datetime
import glob
from .models import Project, Bug
import codecs

# Look, ma, a hard-coded table that maps to
# OpenHatch project names from Launchpad.net project names.
# TimBL would be proud.
lpproj2ohproj = { 'do': 'GNOME-do' }

TextBugList = ConnectBugList("text")
TextBug = ConnectBug("text")

def dump_data_from_project(project):
    url = "https://bugs.launchpad.net/%s/+bugs" % project
    bug_filter = URLBugListFilter()
    # no filtering; dump everything
    l = TextBugList(bug_filter(url))
    # convert elements into Bug objects
    for _bug in l:
        bug = TextBug(_bug)
        serialized = lpb2json.obj2serializable(bug)
        yield serialized

# Callback to handle an update to a single Launchpad bug update
def handle_launchpad_bug_update(query_data, new_data):
    '''
    We're going to store a bug in our database. First we want to
    check to see if we've stored in the DB a stale copy of the same bug.
    We've divided the data from launchpad into bug-identifying data (query_data)
    and the rest of the data we want to store (new_data).

    Side-effect: We create or update a bug in the database.  
    In particular, if we already have a bug for this (project,
    canonical_bug_link) pair, we modify that instead of creating a
    duplicate entry.

    Right now we do not store last_modified time stamps; no one has
    yet figured out what good it would do us.'''
    real_query_data = {}
    real_query_data.update(query_data)
    real_query_data['project'], _ = Project.objects.get_or_create(
        name=query_data['project'])
    bug, created = Bug.objects.get_or_create(defaults=new_data,
                                             **real_query_data)
    if created:
        return bug # nothing to do!
    # else, update the local copy of the bug
    for key in new_data:
        setattr(bug, key, new_data[key])
    bug.save()
    return bug
    
def clean_lp_data_dict(lp_data_dict):
    '''Input: A single datum as returned by launchpadbugs.

    Output: query_data, new_data - two dicts that represent
    processed data from Launchpad.
    We've divided the data from launchpad into bug-identifying data (query_data)
    and the rest of the data we want to store (new_data).
    '''
    # These are the invariants for every bug: together (well, maybe the
    # bug link is enough, hush) they uniquely identify the bug.
    query_data = {}
    query_data['project'] = lp_data_dict['project']
    query_data['canonical_bug_link'] = lp_data_dict['url']

    # If the above is the "key" that we use to find or create the record,
    # these are the "value",
    new_data = {}
    new_data['title'] = lp_data_dict['title']
    new_data['description'] = lp_data_dict['text'][:180]
    new_data['status'] = lp_data_dict['status']
    new_data['importance'] = lp_data_dict['importance']
    if new_data['importance'] is None:
        new_data['importance'] =  'Unknown'

    # create set of people who have commented or created the ticket
    people_involved = set()
    if lp_data_dict['reporter']:
        people_involved.add(dict2hashable(lp_data_dict['reporter']))
    for comment in lp_data_dict['comments']:
        people_involved.add(dict2hashable(comment['user']))

    new_data['people_involved'] = len(people_involved)

    new_data['submitter_username'] = lp_data_dict['reporter']['lplogin']
    new_data['submitter_realname'] = unicode(lp_data_dict['reporter']['realname'])

    # Handle dates
    new_data['last_touched'] = datetime.datetime(*lp_data_dict['date_updated'][:6])
    new_data['last_polled'] = datetime.datetime.now()

    status =  lp_data_dict.get('status', 'Unknown')
    if not status:
        status = 'Unknown'
    new_data['status'] = status
    new_data['date_reported'] = datetime.datetime(
        *lp_data_dict['date_reported'][:6])
    return query_data, new_data
    
def dict2hashable(d):
    return tuple(d.items())

def grab_lp_bugs(lp_project, openhatch_project):
    '''Input: The name of a Launchpad project and its corresponding
    OpenHatch project.

    Side effect: Loops over the available issues in that project and
    updates the database with them.'''
    for data_dict in dump_data_from_project(lp_project):
        data_dict['project'] = openhatch_project
        query_data, new_data = clean_lp_data_dict(data_dict)
        handle_launchpad_bug_update(query_data, new_data)
