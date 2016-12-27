Installation & configuration
============================

Requirements
------------

Django HTTP Proxy should be compatible with any Python 2.x version from 2.5 and 
up and a relatively recent version of Django. It is compatible with Django 1.7.


Installation
------------

The easiest way to install the latest version of Django HTTP Proxy is using 
`pip <http://pypi.python.org/pypi/pip>`_::

    $ pip install django-http-proxy

Alternatively, you can manually download the package from the `Python Package Index <http://pypi.python.org/pypi/django-http-proxy>`_ or from the `Github repository <github_>`_.

.. _github: https://github.com/yvandermeer/django-http-proxy


Next, you need to add "httpproxy" to the ``INSTALLED_APPS`` list 
in your Django settings module (typically ``settings.py``)::

    INSTALLED_APPS = (
        ...
        'httpproxy',
    )

Finally, install the database tables::

    $ python manage.py syncdb

.. note::

    If you are only interested in using Django HTTP Proxy as a live proxy and 
    don't care about recording/playing back requests and responses, simply 
    do not add it to your ``INSTALLED_APPS`` and no database tables will be created.


Configuration
-------------

The core of Django HTTP Proxy is a class-based Django view, 
:class:`httpproxy.views.HttpProxy`.

To use Django HTTP Proxy, you create an entry in your ``urls.py`` that forwards
requests to the :class:`~httpproxy.views.HttpProxy` view class, e.g.::

    from httpproxy.views import HttpProxy

    urlpatterns += patterns('',
        (r'^proxy/(?P<url>.*)$', 
            HttpProxy.as_view(base_url='http://www.python.org/')),
    )
    
Given the above url config, request matching ``/proxy/<any-url>`` will be 
handled by the configured :class:`~httpproxy.views.HttpProxy` view instance and 
forwarded to ``http://www.python.org/<any-url>``.

.. note::

    Older versions of Django HTTP Proxy only supported a single proxy per Django 
    project, which had to be configured using a Django setting::

        PROXY_BASE_URL = 'http://www.python.org/'

    Naturally, you can easily replicate this behavior using the new class-based 
    view syntax::

        from django.conf import settings
        from httpproxy.views import HttpProxy

        urlpatterns += patterns('',
            (r'^proxy/(?P<url>.*)$', 
                HttpProxy.as_view(base_url=settings.PROXY_BASE_URL)),
        )
