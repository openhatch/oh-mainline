from django.conf.urls.defaults import *

import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^search/$', 'mysite.search.views.fetch_bugs'),
    (r'^admin/(.*)', admin.site.root),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_DOC_ROOT}),
    (r'^$', 'mysite.search.views.fetch_bugs'),
    (r'^profile/$', 'mysite.profile.views.index'),
    (r'^profile/add_contribution$', 'mysite.profile.views.add_contribution'),
)


