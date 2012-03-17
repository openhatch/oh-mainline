# -*- coding: utf-8 -*-
# vim: set ai et ts=4 sw=4:

# This file is part of OpenHatch.
# Copyright (C) 2012 Berry Phillips
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

import urlparse

from datetime import datetime, timedelta
from django.conf import settings
from mysite.customs.models import TracBugTimes, TracTimeline
from mysite.search.models import Bug, Project


def trac_bug_times(bug_url):
    tbt = TracBugTimes.objects.get(
        canonical_bug_link=bug_url)
    # It's an old version of Trac that doesn't have links from the
    # bugs to the timeline. So we need to fetch these times from
    # the database built earlier.
    return tbt.timeline.get_times(bug_url)


def trac_get_timeline_url(base_url):
    # Setup the TracTimeline instance
    try:
        timeline = TracTimeline.all_timelines.get(
                base_url=base_url)
    except TracTimeline.DoesNotExist:
        timeline = TracTimeline(base_url=base_url)

    # Check when the timeline was last updated.
    timeline_age = datetime.utcnow() - timeline.last_polled

    # Set up timeline URL.
    timeline_url = urlparse.urljoin(timeline.base_url,
            "timeline?ticket=on&daysback=%d&format=rss" % (
                    timeline_age.days + 1))

    return timeline_url


def trac_udate_timeline(base_url=None, entry_url=None, entry_status=None, entry_date=None):
    try:
        timeline = TracTimeline.all_timelines.get(
                base_url=base_url)
    except TracTimeline.DoesNotExist:
        timeline = TracTimeline(base_url=base_url)

    try:
        tb_times = timeline.tracbugtimes_set.get(
                canonical_bug_link=entry_url)
    except TracBugTimes.DoesNotExist:
        tb_times = TracBugTimes(canonical_bug_link=entry_url,
            timeline=timeline)

    # Set the date values as appropriate.
    if 'created' in entry_status:
        tb_times.date_reported = entry_date
    if tb_times.last_touched < entry_date:
        tb_times.last_touched = entry_date
        # Store entry status as well for use in second step.
        tb_times.latest_timeline_status = entry_status

    # Save the TracBugTimes object.
    tb_times.save()


def bug_get_fresh_urls(bug_url_list):
    # Get up-to-date versions of the urls.
    last_poll = datetime.now() - timedelta(days=settings.TRACKER_POLL_INTERVAL)
    fresh_bug_urls = Bug.all_bugs.filter(
            canonical_bug_link__in=bug_url_list,
            last_polled__lt=last_poll
        ).values_list('canonical_bug_link', flat=True)
    return fresh_bug_urls


def bug_update(bug_data):
    # Get or create a Bug object to put the parsed data in.
    try:
        bug = Bug.all_bugs.get(
            canonical_bug_link=bug_data['canonical_bug_link'])
    except Bug.DoesNotExist:
        bug = Bug(canonical_bug_link=bug_data['canonical_bug_link'])

    # Fill the Bug.
    for key in bug_data:
        value = bug_data[key]
        setattr(bug, key, value)

    # Save the project onto it.
    # Project name is just the TrackerModel's tracker_name, as due to the
    # way Roundup is set up, there is almost always one project per tracker.
    # This could in theory not be the case, but until we find a Roundup
    # tracker handling bugs for multiple projects, we will just support one
    # project per tracker.
    project_from_name, _ = Project.objects.get_or_create(
            name=bug_data['tracker'].tracker_name)
    # Manually save() the Project to ensure that if it was created then it has
    # a display_name.
    if not project_from_name.display_name:
        project_from_name.save()
    bug.project = project_from_name

    # Store the tracker that generated the Bug, update last_polled and save it!
    bug.last_polled = datetime.utcnow()
    bug.save()


def bug_delete_by_url(bug_url):
    try:
        bug = Bug.all_bugs.get(canonical_bug_link=bug_url)
        bug.delete()
    except Bug.DoesNotExist:
        pass

trac_data_transit = {
    'bug_times': trac_bug_times,
    'get_timeline_url': trac_get_timeline_url,
    'udate_timeline': trac_udate_timeline
}

bug_data_transit = {
    'get_fresh_urls': bug_get_fresh_urls,
    'update': bug_update,
    'delete_by_url': bug_delete_by_url,
}
