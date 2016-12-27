import mysite.customs.models
import tastypie.resources
import tastypie.authorization
import mysite.search.models
import django.db.models
import django.core.exceptions
import datetime
import re


class TrackerModelResource(tastypie.resources.ModelResource):
    # This is a trivial resource that just lets each BugImporter
    # subclass export its data out to the web.

    class Meta:
        fields = []  # Let this be handled by dehydrate()
        queryset = (mysite.customs.models.TrackerModel.objects.
                    select_subclasses().all())
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        resource_name = 'tracker_model'
        authorization = tastypie.authorization.DjangoAuthorization()

    def get_object_list(self, request):
        all_objects = super(TrackerModelResource,
                            self).get_object_list(request)
        skip_these_ids = []
        tracker_type = request.GET.get('tracker_type', '')
        # Sanitize tracker_type.
        tracker_type = re.sub('[^a-z]', '', tracker_type)
        if tracker_type:
            # Note. This is an ugly hack.
            query_for_corresponding_foreign_key = ~django.db.models.Q(**{
                tracker_type + 'trackermodel' + '__id': None,
            })
            try:
                all_objects = all_objects.filter(
                    query_for_corresponding_foreign_key)
            except django.core.exceptions.FieldError:
                # In the case the user gave us some nonsense, just declare
                # the query will get no results.
                all_objects = all_objects.none()

        if request.GET.get('tracker_id', '').lower():
            try:
                as_int = int(request.GET['tracker_id'])
            except ValueError:
                # Well, if you really want to know what ints are equal to
                # your string that not an int all, it's no ints. So you get
                # no results.
                all_objects = all_objects.none()
            else:
                all_objects = all_objects.filter(id=as_int)

        if request.GET.get('just_stale', '').lower() == 'yes':
            # Note: This code is of low quality.
            for obj in all_objects:
                relevant_bugs = mysite.search.models.Bug.all_bugs.filter(
                    tracker_id=obj.id)
                # Find the minimum last_polled value
                # HACK. Because we currently leave old bugs sitting around,
                # if no query would refresh them, we know that the oldest bugs
                # will have very old last_polled values. What we're trying to get
                # at is if the bug importer has run for this tracker. So for now,
                # we use django.db.models.Max() instead.
                #
                # This should be changed back to Min() when https://openhatch.org/bugs/issue772
                # is resolved.
                oldest_last_polled_data = relevant_bugs.aggregate(
                    django.db.models.Min('last_polled'))
                oldest_last_polled = oldest_last_polled_data[
                    'last_polled__min']
                if (oldest_last_polled and (
                        oldest_last_polled >= (
                            datetime.datetime.utcnow() -
                            datetime.timedelta(days=1)))):
                    skip_these_ids.append(obj.id)
        filtered = all_objects.exclude(id__in=skip_these_ids)
        return filtered

    def dehydrate(self, bundle):
        '''Actually do the work of creating the dict here.'''
        return bundle.obj.as_dict()
