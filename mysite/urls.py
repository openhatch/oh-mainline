from django.conf.urls.defaults import *
import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^search/$', 'mysite.search.views.index'),
   (r'^search/query/(?P<query>.+)/$', 'mysite.search.views.query'),
    (r'^search/query_json/(?P<query>.+)/$', 'mysite.search.views.query_json'),
    (r'^admin/(.*)', admin.site.root),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_DOC_ROOT}),
)
