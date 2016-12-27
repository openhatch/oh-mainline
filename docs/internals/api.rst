=======
Web API
=======

The basics
==========

The OpenHatch Python code provides some basic APIs that can be used by
JavaScript on the web. Currently, these APIs are only used by
JavaScript within the OpenHatch site itself. In the future, people
might want to re-use our data in off-site JavaScript apps, and we hope
to enable that.

This page documents the data export APIs that exist.

API v1 Profile data
===================

The URL /+api/v1/profile/ is a RESTful API base URL. It has one endpoint,
portfolio_entry.

You can find out more about it interactively in your web browser, by
visiting a URL like
http://127.0.0.1:8000/+api/v1/profile/portfolio_entry/?format=json .

Additionally, if you have "cURL" (a common web page downloading tool),
you can run this command from your computer's command prompt::

 curl http://127.0.0.1:8000/+api/v1/profile/portfolio_entry/

Note that with curl (and with AJAX clients), you can (and should) omit
?format=json.

This exports data from the *PortfolioEntry* model in
mysite/profile/models.py. You can read the detailed code and
configuration behind it at mysite/profile/api.py. The API is powered by
the Tastypie Django app.

More information:

* Django Tastypie documentation: http://django-tastypie.readthedocs.org/en/latest/toc.html
