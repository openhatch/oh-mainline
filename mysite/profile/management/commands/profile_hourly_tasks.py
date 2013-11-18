# This file is part of OpenHatch.
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

import datetime
import logging

from django.core.management.base import BaseCommand

import mysite.profile.tasks
import mysite.base.models
import mysite.search.tasks

# FIXME: Move to a search management command?


def periodically_check_if_bug_timestamp_eclipsed_the_cached_search_timestamp():
    logging.info(
        "Checking if bug timestamp eclipsed the cached search timestamp")
    cache_time = mysite.base.models.Timestamp.get_timestamp_for_string(
        'search_cache')
    bug_time = mysite.base.models.Timestamp.get_timestamp_for_string(
        'search_cache')
    if cache_time < bug_time:
        mysite.search.tasks.clear_search_cache()
        mysite.base.models.Timestamp.update_timestamp_for_string(
            'search_cache')
    logging.info(
        "Finished dealing with bug timestamp vs. cached search timestamp.")


class Command(BaseCommand):
    help = "Run this once hourly for the OpenHatch profile app."

    def handle(self, *args, **options):
        rootLogger = logging.getLogger('')
        rootLogger.setLevel(logging.WARN)
        mysite.profile.tasks.sync_bug_timestamp_from_model_then_fill_recommended_bugs_cache(
        )
        mysite.profile.tasks.fill_recommended_bugs_cache()

        # Every 4 hours, clear search cache
        if (datetime.datetime.utcnow().hour % 4) == 0:
            periodically_check_if_bug_timestamp_eclipsed_the_cached_search_timestamp(
            )
