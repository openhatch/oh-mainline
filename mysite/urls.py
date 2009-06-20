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
        (r'^people/add_contribution$', 'mysite.profile.views.add_contribution'),
        (r'^people/$', 'mysite.profile.views.display_person'),

        (r'^people/get_data_for_email$', 'mysite.profile.views.get_data_for_email'),
        (r'^people/change_what_like_working_on$', 'mysite.profile.views.change_what_like_working_on_web'),
        (r'^people/add_tag_to_project_exp$', 'mysite.profile.views.add_tag_to_project_exp_web'),

        # Get a list of suggestions for the search input, formatted the way that
        # the jQuery autocomplete plugin wants it.
        (r'^search/get_suggestions$', 'mysite.search.views.request_jquery_autocompletion_suggestions'),
        )

# vim: set ai ts=4 sts=4 et sw=4:
