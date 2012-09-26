import mysite.customs.models
import tastypie.resources
import tastypie.authorization


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

    def dehydrate(self, bundle):
        '''Actually do the work of creating the dict here.'''
        return bundle.obj.as_dict()
