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

import logging

import json

from django.core.management.base import BaseCommand

import mysite.base.view_helpers
import mysite.profile.models

MAX_ERRORS = 5


class Command(BaseCommand):
    help = ("For all people whose latitude and longitude are the default, "
            "but whose location display name is not the default, "
            "geocode them.")

    def handle(self, *args, **kwargs):
        self.errors_so_far = 0
        self.successes_so_far = 0
        logging.info("Begun attempting to migrate people's locations...")
        self.migrate_people()
        logging.info("Succeeded at geocoding %d people", self.successes_so_far)

    def migrate_people(self):
        for person in mysite.profile.models.Person.objects.all():
            # If we have seen too many failures, then we bail out entirely.
            if self.errors_so_far > MAX_ERRORS:
                return

            address = person.location_display_name
            # If someone has their location set to the Inaccessible Island,
            # skip them.
            if address == mysite.profile.models.DEFAULT_LOCATION:
                continue

            # If someone has their latitude or longitude set to some real place,
            # skip them.
            if ((person.latitude != mysite.profile.models.DEFAULT_LATITUDE) or
                    (person.longitude != mysite.profile.models.DEFAULT_LONGITUDE)):
                continue

            # Okay, this is a person we should process! Try to geocode them...
            try:
                as_string = mysite.base.view_helpers.cached_geocoding_in_json(
                    address)
            except Exception:
                self.errors_so_far += 1
                continue

            as_dict = json.loads(as_string)
            try:
                person.latitude = as_dict['latitude']
                person.longitude = as_dict['longitude']
                person.save()
            except KeyError:
                logging.info("FYI, we hit a KeyError. Go figure.")
                logging.info(
                    "In case you're curious, the data was: %s", as_dict)
                self.errors_so_far += 1
                continue

            logging.info("Success with %s", address)
            self.successes_so_far += 1
