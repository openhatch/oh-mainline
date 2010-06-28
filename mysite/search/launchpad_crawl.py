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

#FIXME: Add only those of the following that actually use Launchpad for development.
#u'apache-mod-digest' : u'apache-mod-digest' , u'bws-upload' : u'BWS-Upload' , u'pyjunitxml' : u'pyjunitxml' , u'bzr-search' : u'bzr search plugin' , u'bzr-email' : u'bzr email commit hook' , u'check' : u'check' , u'libsyncml' : u'libsyncml' , u'config-manager' : u'config-manager' , u'testscenarios' : u'testscenarios' , u'liburl' : u'liburl' , u'liblockdir' : u'lockdir' , u'bzr-guess' : u'bzr-guess' , u'etap' : u'etap' , u'gforth' : u'Gforth' , u'bitten' : u'Bitten' , u'sqlobject' : u'SQLObject' , u'bzr-ping' : u'Ping plugin for Bazaar' , u'unittest-ext' : u'unittest-ext' , u'pytz' : u'pytz' , u'funkload' : u'FunkLoad' , u'slony-i' : u'Slony-I' , u'zoneinfo' : u'The tz Database' , u'py-radius' : u'py-radius' , u'pypi' : u'Python Package Index' , u'pybabel' : u'Python Babel' , u'feedvalidator' : u'Feed Validator' , u'sphinx' : u'Sphinx' , u'mammoth-replicator' : u'Mammoth Replicator' , u'dbapi-compliance' : u'Python DBAPI Compliance Tests' , u'wget' : u'wget' , u'redhatcluster' : u'Red Hat Cluster' , u'bugzilla' : u'Bugzilla' , u'grepmap' : u'grepmap' , u'live-f1' : u'Live F1' , u'libnih' : u'libnih' , u'hct' : u'HCT' , u'upstart' : u'upstart ' , u'module-init-tools' : u'module-init-tools' , u'ubuntu-seeds' : u'Ubuntu Seeds' , u'usplash' : u'usplash' , u'merge-o-matic' : u'Merge-o-Matic' , u'uds-intrepid' : u'UDS Intrepid' , u'watershed' : u'watershed' , u'udev-extras' : u'Udev extras' , u'sreadahead' : u'sreadahead' , u'pybootchartgui' : u'pybootchartgui' , u'bootchart-collector' : u'bootchart-collector' , u'bootchart' : u'bootchart' , u'ubiquity' : u'ubiquity' , u'man-db' : u'man-db'}


TextBugList = ConnectBugList("text")
TextBug = ConnectBug("text")

def dump_data_from_project(project):

        yield serialized

# Callback to handle an update to a single Launchpad bug update
def handle_launchpad_bug_update(project_name, canonical_bug_link, new_data):
    """
    We're going to store a bug in our database. First we want to
    check to see if we've stored in the DB a stale copy of the same bug.

    Side-effect: We create or update a bug in the database.  
    In particular, if we already have a bug for this (project,
    canonical_bug_link) pair, we modify that instead of creating a
    duplicate entry.

    Right now we do not store last_modified time stamps; no one has
    yet figured out what good it would do us."""
    project, _ = Project.objects.get_or_create(name=project_name)
    new_data['project'] = project
    bug, created = Bug.all_bugs.get_or_create(
            canonical_bug_link=canonical_bug_link, defaults=new_data)
    # 'defaults' means data used for creating but not getting
    if created:
        return bug # nothing to do!
    else:
        # else, update the local copy of the bug
        for key in new_data:
            setattr(bug, key, new_data[key])
        bug.save()
        return bug
    
def clean_lp_data_dict(lp_data_dict):
    """Input: A single datum as returned by launchpadbugs.

    Output: query_data, new_data - two dicts that represent
    processed data from Launchpad.
    We've divided the data from launchpad into bug-identifying data (query_data)
    and the rest of the data we want to store (new_data).
    """
    # These are the invariants for every bug: together (well, maybe the
    # bug link is enough, hush) they uniquely identify the bug.
    query_data = {}
    query_data['canonical_bug_link'] = lp_data_dict['url']

    # If the above is the "key" that we use to find or create the record,
    # these are the "value",
    new_data = {}
    new_data['title'] = lp_data_dict['title']
    new_data['description'] = lp_data_dict['text']

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

    # Look for bitesize tag
    # If no 'tags', pass
    try:
        if 'bitesize' in lp_data_dict['tags']:
            new_data['good_for_newcomers'] = True
    except KeyError:
        pass

    status =  lp_data_dict.get('status', 'Unknown')
    if not status:
        status = 'Unknown'
    new_data['status'] = status
    if new_data['status'].lower() in ('fix released', 'fix committed'):
        new_data['looks_closed'] = True
    # else looks_closed will be False due to the Bug default
    new_data['date_reported'] = datetime.datetime(
        *lp_data_dict['date_reported'][:6])
    return query_data, new_data
    
def dict2hashable(d):
    return tuple(d.items())

def grab_lp_bugs(lp_project, openhatch_project_name):
    '''Input: The name of a Launchpad project and its corresponding
    OpenHatch project name.

    Side effect: Loops over the available issues in that project and
    updates the database with them.'''
    for data_dict in dump_data_from_project(lp_project):
        data_dict['project'] = openhatch_project_name
        query_data, new_data = clean_lp_data_dict(data_dict)
        handle_launchpad_bug_update(
                project_name=openhatch_project_name,
                canonical_bug_link=query_data['canonical_bug_link'],
                new_data=new_data)
