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

You can find out more about it interactively, by visiting a URL like
http://127.0.0.1:8000/+api/v1/profile/portfolio_entry/?format=json .

This exports data from the *PortfolioEntry* model in
mysite/profile/models.py. You can read the detailed code and
configuration behind it at mysite/profile/api.py. The API is powered by
the Tastypie Django app.

More information:

* Django Tastypie documentation: http://django-tastypie.readthedocs.org/en/latest/toc.html

Profile API (for location data)
===============================

The URL /+profile_api/location_data/ accepts IDs as input through the
*person_ids* parameter, and it returns a JSON dictionary with user IDs
and values of a dictionary of data about the user.

(This "API" is implemented in mysite/profile/views.py, and it doesn't
use any sort of API system like Tastypie. We should probably convert
it to use Tastypie.)

