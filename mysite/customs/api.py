import mysite.customs.models
import tastypie.resources
import tastypie.authorization
import mysite.search.models
import django.db.models
import datetime


class TrackerModelResource(tastypie.resources.ModelResource):
    # This is a trivial resource that just lets each BugImporter
    # subclass export its data out to the web.
    class Meta:
        fields = [] # Let this be handled by dehydrate()
        queryset = (mysite.customs.models.TrackerModel.objects.
                    select_subclasses().all())
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        resource_name = 'tracker_model'
        authorization = tastypie.authorization.DjangoAuthorization()

    def get_object_list(self, request):
        all_objects = super(TrackerModelResource, self).get_object_list(request)
        skip_these_ids = []
        if request.GET.get('just_stale', '').lower() == 'yes':
            # Note: This code is of low quality.
            for obj in all_objects:
                relevant_bugs = mysite.search.models.Bug.all_bugs.filter(
                    tracker_id=obj.id)
                # Find the minimum last_polled value
                oldest_last_polled_data = relevant_bugs.aggregate(
                    django.db.models.Min('last_polled'))
                oldest_last_polled = oldest_last_polled_data['last_polled__min']
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
