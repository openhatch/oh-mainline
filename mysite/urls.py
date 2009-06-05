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
                       
    # Example:
    # (r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
