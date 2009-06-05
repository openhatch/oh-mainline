from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^search/$', 'mysite.search.views.index'),
    (r'^search/query/(?P<query>\w+)/$', 'mysite.search.views.query'),
    (r'^search/query_json/(?P<query>\w+)/$', 'mysite.search.views.query_json'),
    (r'^admin/(.*)', admin.site.root),
)
