from django.conf.urls.defaults import *

urlpatterns = patterns('mysite.project.views',

        (r'(?P<project__name>.+)$', 'project'),

        (r'^$', 'projects'),


        )

# vim: set ai ts=4 sts=4 et sw=4:
