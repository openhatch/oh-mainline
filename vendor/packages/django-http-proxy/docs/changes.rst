Changes
-------

0.4
~~~

* Migration from Bitbucket (Mercurial) to Github
* Refactored main view using Django class-based views (see :class:`~httpproxy.views.HttpProxy`)
* Removed basic authentication support (`PROXY_USER` and `PROXY_PASSWORD`); may be added back later on.
* Finally merged back Django 1.6 fixes by `Petr Dlouhý <https://bitbucket.org/pdlouhy>`_ (thanks!)
* Merged pull request from `Garrett Seward <https://github.com/spectralsun>`_ (thanks!)
* Added Django 1.7 compatibility
* Added database migrations (Django 1.7 and higher only)
* Updated and improvement the documentation (including :doc:`API documentation <api/index>`)
* Added an ``example`` project for reference
* Using urllib2 instead of httplib2
* Using setuptools instead of distutils
* Using versioneer2 for package versioning
* Removed some unused imports and did some further code cleanup

0.3.2
~~~~~

* Limited display of request querystring in admin screen to 50 characters

0.3.1
~~~~~

* Fixed 250 character limitation for querystring in Recorded Request 
  (`issue #2 <http://bitbucket.org/yvandermeer/django-http-proxy/issue/2/>`_)
* Added new Request Parameter model; requires ``./manage.py reset httpproxy && ./manage.py syncdb``

0.3
~~~

* Fixed Python 2.5 support by removing use of ``__package__``
* Implemented request path "normalization", fixing record and playback if the
  proxy is URL-configured anywhere other than directly in the root.
* Added experimental ``PROXY_REWRITE_RESPONSES`` settings to fix paths to
  resources (images, javascript, etc) on the same domain if ``httproxy`` is
  not configured at the root.

0.2.2
~~~~~

* Removed print statement I accidentally left behind.

0.2.1
~~~~~

* Fixed `issue #1 <http://bitbucket.org/yvandermeer/django-http-proxy/issue/1/>`_;
  Unsupported content types are now silently ignored.
* Added ``PROXY_IGNORE_UNSUPPORTED`` setting to control the behavior for
  handling unsupported responses.

0.2
~~~

* Added recording and playback functionality
* Improved handling of ``httpproxy``-specific settings
* Started using Sphinx for documentation

0.1
~~~

* Initial release
* Basic HTTP proxy functionality based on `a blog post by Will Larson <http://lethain.com/entry/2008/sep/30/suffer-less-by-using-django-dev-server-as-a-proxy/>`_
