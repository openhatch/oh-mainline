from django.conf.urls.defaults import *
import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

parameter_grabbers = {
		'language': 'language[=:](?P<language>[^/,]+)',
		'format': 'format[=:](?P<format>.+)',
		'slice': 'slice[=:](?P<start>\d+):(?P<end>\d+)',
		}
urlpatterns = patterns('',
    (r'^search/$', 'mysite.search.views.index'),
    (r'^search/%(language)s/%(format)s/%(slice)s/$' % \
			parameter_grabbers, 'mysite.search.views.fetch_bugs'),
    (r'^search/%(language)s/%(format)s/$' % \
			parameter_grabbers, 'mysite.search.views.fetch_bugs'),
    (r'^search/%(format)s/%(language)s/$' % \
			parameter_grabbers, 'mysite.search.views.fetch_bugs'),
    (r'^search/%(language)s/$' % \
			parameter_grabbers, 'mysite.search.views.fetch_bugs'),
    (r'^admin/(.*)', admin.site.root),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_DOC_ROOT}),
)
