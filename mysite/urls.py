from django.conf.urls.defaults import *

import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
        (r'^$', 'mysite.search.views.fetch_bugs'),
        (r'^search/$', 'mysite.search.views.fetch_bugs'),
        (r'^admin/(.*)', admin.site.root),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_DOC_ROOT}),
        (r'^profile/$', 'mysite.profile.views.index'),
        (r'^profile/add_contribution$', 'mysite.profile.views.add_contribution'),
        (r'^profile/get_data_for_username$', 'mysite.profile.views.get_data_for_username'),

        # Get a list of suggestions for the search input, formatted the way that
        # the jQuery autocomplete plugin wants it.
        (r'^search/get_suggestions$', 'mysite.search.views.request_jquery_autocompletion_suggestions'),
        )

# vim: set ai ts=4 sts=4 et sw=4:
