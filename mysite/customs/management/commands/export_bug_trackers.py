# This file is part of OpenHatch.
# Copyright (C) 2012 OpenHatch, Inc.
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

import yaml
from django.core.management.base import BaseCommand
import mysite.customs.models

USEFUL_KEYS = set(['base_url',
                  'tracker_name',
                  'documentation_text',
                  'documentation_type',
                  'bitesized_text',
                  'bitesized_type',
                   ])

class Command(BaseCommand):
    help = "Print a YAML file with configuration all Trac-based trackers"

    def handle(self, *args, **options):
        as_dicts = []
        for tracker in mysite.customs.models.TracTrackerModel.objects.select_subclasses():
            # Just Trac for now
            if tracker.__class__ != mysite.customs.models.TracTrackerModel:
                continue
            this_tracker_as_dict = {}
            for key in USEFUL_KEYS:
                value = getattr(tracker, key, None)
                if value:
                    this_tracker_as_dict[key] = value
            as_dicts.append(this_tracker_as_dict)
        print yaml.safe_dump(as_dicts)
