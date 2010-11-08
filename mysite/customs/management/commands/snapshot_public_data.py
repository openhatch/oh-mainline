import logging

from django.contrib.auth.models import User
from mysite.search.models import Bug, Project
from mysite.profile.models import Person
from mysite.base.models import Timestamp
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
        
    def serialize_objects_except(self, query_set, blacklisted_columns):
        obj_serializer = django.core.serializers.get_serializer('python')()
        all = obj_serializer.serialize(query_set)
        for obj in all:
            fields_that_are_safe_to_export = {}
            for key in obj['fields']:
                value = obj['fields'][key]

                if key in blacklisted_columns:
                    pass # by failing to copy it in, we remove it from the perspective of the dump
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

        # location_confirmed should be hidden -- that's private data
        # location_display_name should be set to the result of Person.get_public_location_or_default()
        everyone = Person.objects.all()
        for dude in everyone:
            dude.location_display_name = dude.get_public_location_or_default()
        public_person_data = self.serialize_all_objects(query_set=everyone)
        data.extend(public_person_data)

        # Save the User objects, anonymizing the email address if necessary
        all_user_objects = User.objects.all()
        for user in all_user_objects:
            try:
                if user.get_profile().show_email:
                    pass # do not mutate the email address
                else:
                    # anonymize email address
                    user.email = 'user_id_%d_has_hidden_email_address@example.com' % user.id
            except Person.DoesNotExist:
                pass # it is okay if the user has no prefs
        public_user_data = self.serialize_objects(query_set=all_user_objects,
                                whitelisted_columns = ['id', 'username', 'first_name', 'last_name', 'email'])
        data.extend(public_user_data)

        # exporting Project data
        public_project_data = self.serialize_objects_except(
            query_set=Project.objects.all(),
            blacklisted_columns = ['icon_url','icon_raw'])
        data.extend(public_project_data)
        
        # Timestamp data needs export
        public_timestamp_data = self.serialize_all_objects(query_set=Timestamp.objects.all())
        data.extend(public_timestamp_data)
        
        # exporting Bug data
        public_bug_data = self.serialize_all_objects(query_set=Bug.all_bugs.all())
        data.extend(public_bug_data)
        

        ### anyway, now we stream all this data out using simplejson
        simplejson.dump(data, output,cls=django.core.serializers.json.DjangoJSONEncoder)
