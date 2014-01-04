import mysite.profile.models
import tastypie.http
import tastypie.fields
import tastypie.resources
import tastypie.authorization


class PerPersonModelResource(tastypie.resources.ModelResource):

    '''This ModelResource subclass overrides a few methods in
    ModelResource to filter database queries to only affect
    data from the user currently logged-in.'''

    def obj_create(self, bundle, request=None, **kwargs):
        if request.user.is_authenticated():
            return super(PerPersonModelResource, self).obj_create(
                bundle,
                request,
                person=request.user.get_profile(),
                **kwargs)
        return tastypie.http.HttpBadRequest(
            'You need to be logged in.')

    def apply_authorization_limits(self, request, object_list):
        if request.user.is_authenticated():
            return object_list.filter(person=request.user.get_profile())
        # Otherwise, just return an empty list. This is imperfect,
        # but it will do for now.
        return []


class PortfolioEntryResource(PerPersonModelResource):
    # First, we indicate what fields we're willing to copy
    # out of the profile.PortfolioEntry model:

    class Meta:
        excludes = ['person', 'project', 'date_created']
        queryset = mysite.profile.models.PortfolioEntry.objects.all()
        resource_name = 'portfolio_entry'

    # The following read-only fields are data calculated from
    # the project. They are read-only to indicate that this is
    # the wrong place to try to change them. (Use a project
    # API, whenever that exists.)
    #
    # We calculate them here so that consumers of the API can
    # deal with just one Resource, and not deal with nesting.
    project__name = tastypie.fields.CharField(readonly=True)
    project__icon = tastypie.fields.CharField(readonly=True)
    project__url = tastypie.fields.CharField(readonly=True)

    def dehydrate_project__icon(self, bundle):
        pfe = bundle.obj
        return pfe.project.get_url_of_icon_or_generic()

    def dehydrate_project__name(self, bundle):
        pfe = bundle.obj
        return pfe.project.name

    def dehydrate_project__url(self, bundle):
        pfe = bundle.obj
        return pfe.project.get_url()

    # The citation list is flattened here so that consumers of the API
    # can deal only with the PortfolioEntryResource, and not a separate
    # CitationResource.
    citation_list = tastypie.fields.ListField()

    def dehydrate_citation_list(self, bundle):
        '''This exposes the citation list as a flat list.'''
        pfe = bundle.obj
        return self._pfe2citation_list(pfe)

    @staticmethod
    def _pfe2citation_list(pfe):
        ret = []
        for citation in pfe.citation_set.all():
            data = {'description': citation.contributor_role,
                    'url': citation.url}
            ret.append(data)
        return ret

    def hydrate_citation_list(self, bundle):
        '''This takes a simple flat list of dictionaries
        and replaces all assocated Citations with them.'''
        raise NotImplemented
