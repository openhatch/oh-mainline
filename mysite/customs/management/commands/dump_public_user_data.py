import logging

from django.contrib.auth.models import User
from mysite.search.models import Bug
import sys
import simplejson
from django.core.management.base import BaseCommand
import django.core.serializers
import django.core.serializers.json
import mysite.search.views


## You can run this, and it generates a JSON file that can be
## passed to loaddata.


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
                    pass # by failing to copy it in, we remove it from the perspective of the dump

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

        # Now, go through that data and remove all columns except these:
        public_user_data = self.serialize_objects(
                query_set=User.objects.all(),
                whitelisted_columns = ['id', 'username', 'first_name', 'last_name'])
        data.extend(public_user_data)

        # It would be nice if we exported the Person data, too.
        # Note: The location column is not safe to export. There's the privacy issue that
        # not all people want to share their location data.

        # location_confirmed should be hidden -- that's private data
        # location_display_name should be set to the result of Person.get_public_location_or_default()
        # For now, since I can't write it right now, I pretend we got the empty list as the result.
        public_data_from_person_model = []
        data.extend(public_data_from_person_model)
        
        # exporting Bug data (?)
        public_bug_data = self.serialize_all_objects(query_set=Bug.all_bugs.all())
        data.extend(public_bug_data)

        ### anyway, now we stream all this data out using simplejson
        simplejson.dump(data, output,cls=django.core.serializers.json.DjangoJSONEncoder)
