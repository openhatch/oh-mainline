# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
# Copyright (C) 2012 Berry Phillips
# Copyright (C) 2012 John Morrissey
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
import dateutil
import mysite.customs.models
import mysite.customs.forms
import logging

from mysite.customs.models import TrackerModel
from mysite.search.models import Bug

import django.db.models

all_trackers = {
        'bugzilla': {
            'namestr': 'Bugzilla',
            'model': mysite.customs.models.BugzillaTrackerModel,
            'form': mysite.customs.forms.BugzillaTrackerForm,
            'urlmodel': mysite.customs.models.BugzillaQueryModel,
            'urlform': mysite.customs.forms.BugzillaQueryForm,
            },
        'google': {
            'namestr': 'Google Code',
            'model': mysite.customs.models.GoogleTrackerModel,
            'form': mysite.customs.forms.GoogleTrackerForm,
            'urlmodel': mysite.customs.models.GoogleQueryModel,
            'urlform': mysite.customs.forms.GoogleQueryForm,
            },
        'roundup': {
            'namestr': 'Roundup',
            'model': mysite.customs.models.RoundupTrackerModel,
            'form': mysite.customs.forms.RoundupTrackerForm,
            'urlmodel': mysite.customs.models.RoundupQueryModel,
            'urlform': mysite.customs.forms.RoundupQueryForm,
            },
        'trac': {
            'namestr': 'Trac',
            'model': mysite.customs.models.TracTrackerModel,
            'form': mysite.customs.forms.TracTrackerForm,
            'urlmodel': mysite.customs.models.TracQueryModel,
            'urlform': mysite.customs.forms.TracQueryForm,
            },
        'launchpad': {
            'namestr': 'Launchpad',
            'model': mysite.customs.models.LaunchpadTrackerModel,
            'form':  mysite.customs.forms.LaunchpadTrackerForm,
            'urlmodel': mysite.customs.models.LaunchpadQueryModel,
            'urlform': None,
            },
        'github': {
            'namestr': 'GitHub',
            'model': mysite.customs.models.GitHubTrackerModel,
            'form':  mysite.customs.forms.GitHubTrackerForm,
            'urlmodel': mysite.customs.models.GitHubQueryModel,
            'urlform': None,
            },
        }

def import_one_bug_item(d):
    '''Accepts one ParsedBug object, as a Python dict.

    Usually causes the side effect of creating a Bug project.'''
    # Store d as a copy of the input dict, to avoid making a mess.
    d = dict(d)
    # Look for a matching Bug
    matches = mysite.search.models.Bug.all_bugs.filter(
        canonical_bug_link=d['canonical_bug_link'])

    # Provide a quick escape if the bug importer told us it has
    # no updates for us.
    if matches and d.get('_no_update'):
        b = matches[0]
        b.last_polled = datetime.datetime.utcnow()
        b.save()
        return

    if not (('_tracker_name' in d) and
            ('_project_name' in d)):
        logging.error("Your data needs a _tracker_name and _project_name.")
        logging.error(repr(d))
        return

    project, created = mysite.search.models.Project.objects.get_or_create(name=d['_project_name'])
    if created:
        logging.error("FYI we created: %s", d['_project_name'])

    tracker = mysite.customs.models.TrackerModel.get_by_name(
        tracker_name=d['_tracker_name'])
    del d['_project_name']
    del d['_tracker_name']
    deleted = d.get('_deleted', False)
    if '_deleted' in d:
        del d['_deleted']
    if matches:
        bug = matches[0]
    else:
        bug = mysite.search.models.Bug()

    if deleted:
        if bug.pk: # meaning, is the bug already in the DB?
            # If so, delete it.
            bug.delete()
        # Either way, stop further processing.
        return

    datetime_field_names = set([
            field.name
            for field in bug._meta.fields
            if isinstance(field,
                          django.db.models.fields.DateTimeField)])

    for key in d:
        value = d[key]
        if key in datetime_field_names and (
            not isinstance(value, datetime.datetime)):
            value = dateutil.parser.parse(value)
        if getattr(bug, key) != value:
            setattr(bug, key, value)

    if (bug.project_id is None) or (bug.project != project):
        bug.project = project
    if (bug.tracker_id is None) or (bug.tracker != tracker):
        bug.tracker = tracker

    bug.save()
    return bug

class AddTrackerForeignKeysToBugs(object):

    def __init__(self, tracker_model, reactor_manager, bug_parser=None, data_sinks_by_type=None, data_transits=None):
        # Store the tracker model
        self.tm = tracker_model
        # Store the reactor manager
        self.rm = reactor_manager

    def process_bugs(self, list_of_url_data_pairs):
        # Unzip the list of bugs and discard the data field.
        bug_urls = [bug_url for (bug_url, bug_data) in list_of_url_data_pairs]
        # Fetch a list of all Bugs that are stale.
        bugs = Bug.all_bugs.filter(canonical_bug_link__in=bug_urls)
        tms = TrackerModel.objects.all().select_subclasses()
        # For each TrackerModel, process its stale Bugs.
        bugs_to_retry = []
        for bug in bugs:
            tms_shortlist = [tm for tm in tms if tm.get_base_url() in bug.canonical_bug_link]
            # Check that we actually got something back, otherwise bug.tracker would get
            # set to None, and self.rm.update_bugs would send it right back here, causing
            # infinite recursion.
            if len(tms_shortlist) > 0:
                # Ideally this should now just be one object, so just take the first.
                bug.tracker = tms_shortlist[0]
                bug.save()
                bugs_to_retry.append(bug)
        # For the Bugs that now have TrackerModels, update them.
        if bugs_to_retry:
            self.rm.update_bugs(bugs_to_retry)
