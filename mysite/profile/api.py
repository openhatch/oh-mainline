import tastypie.authorization
from tastypie.authorization import Authorization
from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized
import tastypie.fields
import tastypie.http
import tastypie.resources

import mysite.profile.models


class PerPersonModelResource(tastypie.resources.ModelResource):
    """
    The PerPersonModelResource subclass of tastypie's
    ModelResource overrides a few methods in
    ModelResource to allow OpenHatch to filter database queries
    to only affect data from the currently logged-in user.
    """

    def obj_create(self, bundle, request=None, **kwargs):
        """
        For an authenticated user, obj_create creates a
        PerPersonModelResource object for the user's profile
        """
        if request.user.is_authenticated():
            return super(PerPersonModelResource, self).obj_create(bundle, request, person=request.user.get_profile(), **kwargs)
        return tastypie.http.HttpBadRequest('You need to be logged in.')


class CustomAuthorization(Authorization):
    """
    Custom authorization for an individual user and the
    objects related to the user.
    """

    def read_list(self, object_list, bundle):
        """
        This assumes a ``QuerySet`` from ``ModelResource``.
        Returns an object_list for an authenticated user that
        has been filter for the user.
        If not an authenticated user, currently return an
        empty list.
        """
        if bundle.request.user.is_authenticated():
            return object_list.filter(person=bundle.request.user)
        return []


class PortfolioEntryResource(PerPersonModelResource):
    """
    The PortolioEntryResource

    First, we indicate what fields we're willing to copy
    out of the profile.PortfolioEntry model:
    """

    class Meta:
        excludes = ['person', 'project', 'date_created']
        queryset = mysite.profile.models.PortfolioEntry.objects.all()
        resource_name = 'portfolio_entry'
        authorization = CustomAuthorization()

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
        portfolio_entry = bundle.obj
        return portfolio_entry.project.get_url_of_icon_or_generic()

    def dehydrate_project__name(self, bundle):
        portfolio_entry = bundle.obj
        return portfolio_entry.project.name

    def dehydrate_project__url(self, bundle):
        pfe = bundle.obj
        return pfe.project.get_url()

    # The citation list is flattened here so that consumers of the API
    # can deal only with the PortfolioEntryResource, and not a separate
    # CitationResource.
    citation_list = tastypie.fields.ListField()

    def dehydrate_citation_list(self, bundle):
        """This exposes the citation list as a flat list."""
        portfolio_entry = bundle.obj
        return self._pfe2citation_list(portfolio_entry)

    @staticmethod
    def _pfe2citation_list(pfe):
        """
        Takes a portfolio entry resource and creates a citation list
        :param pfe: portfolio entry resource
        :return: citation_list
        """
        citation_list = []
        for citation in pfe.citation_set.all():
            data = {'description': citation.contributor_role,
                    'url': citation.url}
            citation_list.append(data)
        return citation_list

    def hydrate_citation_list(self, bundle):
        """ This takes a simple flat list of dictionaries
        and replaces all associated Citations with them. """
        raise NotImplemented
