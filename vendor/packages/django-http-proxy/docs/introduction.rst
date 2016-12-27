Introduction
============

Django HTTP Proxy provides simple HTTP proxy functionality for the Django web
development framework. It allows you make requests to an external server by 
requesting them from the main server running your Django application. In 
addition, it allows you to record the responses to those requests and play them 
back at any time.

One possible use for this application (actually, the reason it was developed)
is to allow for easy development of Ajax applications against a live server
environment:

* Avoid typical cross-domain issues while developing an Ajax application based
  on live data from another server.
* Record responses and play them back at a later time:
    * Use "live" data, even when you are developing offline
    * Speedy responses instead of having to wait for a remote server
* Manually edit recorded responses via the Django admin interface

Combined with the standard `Django development server <http://docs.djangoproject.com/en/dev/ref/django-admin/#runserver>`_, 
you have a useful toolkit for developing HTML5/Ajax applications.

Django HTTP Proxy is licensed under an `MIT-style permissive license <license>`_ and
`maintained on Github <http://github.com/yvandermeer/django-http-proxy/>`_.
