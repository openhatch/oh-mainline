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

import logging

from django.contrib.auth.models import User
from mysite.search.models import Bug, Project
from mysite.profile.models import Person, Tag, TagType, Link_Person_Tag
from mysite.base.models import Timestamp
import sys
from django.utils import simplejson
from django.core.management.base import BaseCommand
import django.core.serializers
import django.core.serializers.json
import mysite.search.views


# You can run this, and it generates a JSON file that can be
# passed to loaddata.


class Command(BaseCommand):
    help = "Create a JSON file of all the public data in the Person and User models."

    def serialize_objects(self, query_set, whitelisted_columns):
        obj_serializer = django.core.serializers.get_serializer('python')()
        all = obj_serializer.serialize(query_set)
        for obj in all:
            fields_that_are_safe_to_export = {}
            for key in obj['fields']:
                value = obj['fields'][key]

                if key in whitelisted_columns:
                    # copy it into the safe dictionary
                    fields_that_are_safe_to_export[key] = value
                else:
                    # by failing to copy it in, we remove it from the
                    # perspective of the dump
                    pass

            # Now, in obj, replace the fields with a safe version
            obj['fields'] = fields_that_are_safe_to_export
        return all

    def serialize_objects_except(self, query_set, blacklisted_columns):
        obj_serializer = django.core.serializers.get_serializer('python')()
        all = obj_serializer.serialize(query_set)
        for obj in all:
            fields_that_are_safe_to_export = {}
            for key in obj['fields']:
                value = obj['fields'][key]

                if key in blacklisted_columns:
                    # by failing to copy it in, we remove it from the
                    # perspective of the dump
                    pass
                else:
                    # copy into the safe dictionary
                    fields_that_are_safe_to_export[key] = value

            # Now, in obj, replace the fields with a safe version
            obj['fields'] = fields_that_are_safe_to_export
        return all

    def serialize_all_objects(self, query_set):
        obj_serializer = django.core.serializers.get_serializer('python')()
        all = obj_serializer.serialize(query_set)
        for obj in all:
            fields_that_are_safe_to_export = {}
            for key in obj['fields']:
                value = obj['fields'][key]
                fields_that_are_safe_to_export[key] = value

            # Now, in obj, replace the fields with a safe version
            obj['fields'] = fields_that_are_safe_to_export
        return all

    def handle(self, output=None, *args, **options):
        if output == None:
            output = sys.stdout

        data = []

        # Save the User objects, anonymizing the email address if necessary
        all_user_objects = User.objects.all()
        for user in all_user_objects:
            try:
                if user.get_profile().show_email:
                    pass  # do not mutate the email address
                else:
                    # anonymize email address
                    user.email = 'user_id_%d_has_hidden_email_address@example.com' % user.id
            except Person.DoesNotExist:
                pass  # it is okay if the user has no prefs
        public_user_data = self.serialize_objects(query_set=all_user_objects,
                                                  whitelisted_columns=['id', 'username', 'first_name', 'last_name', 'email'])
        data.extend(public_user_data)

        # location_confirmed should be hidden -- that's private data
        # location_display_name should be set to the result of
        # Person.get_public_location_or_default()
        everyone = Person.objects.all()
        for dude in everyone:
            dude.location_display_name = dude.get_public_location_or_default()
            dude.longitude = dude.get_public_longitude_or_default()
            dude.latitude = dude.get_public_latitude_or_default()
        public_person_data = self.serialize_all_objects(query_set=everyone)
        data.extend(public_person_data)

        # exporting Project data
        public_project_data = self.serialize_objects_except(
            query_set=Project.objects.all(),
            blacklisted_columns=['icon_url', 'icon_raw'])
        data.extend(public_project_data)

        # Timestamp data needs export
        public_timestamp_data = self.serialize_all_objects(
            query_set=Timestamp.objects.all())
        data.extend(public_timestamp_data)

        # exporting Bug data
        public_bug_data = self.serialize_all_objects(
            query_set=Bug.all_bugs.all())
        data.extend(public_bug_data)

        # exporting tagtypes
        public_tagtypes_data = self.serialize_all_objects(
            query_set=TagType.objects.all())
        data.extend(public_tagtypes_data)

        # exporting tags
        public_tags_data = self.serialize_all_objects(
            query_set=Tag.objects.all())
        data.extend(public_tags_data)

        # exporting tags-persons links
        public_persons_tags_links = self.serialize_all_objects(
            query_set=Link_Person_Tag.objects.all())
        data.extend(public_persons_tags_links)

        # anyway, now we stream all this data out using simplejson
        simplejson.dump(data, output,
                        cls=django.core.serializers.json.DjangoJSONEncoder)
