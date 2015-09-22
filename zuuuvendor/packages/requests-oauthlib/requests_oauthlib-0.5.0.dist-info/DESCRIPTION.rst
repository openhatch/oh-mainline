Requests-OAuthlib |build-status| |coverage-status| |docs|
=========================================================

This project provides first-class OAuth library support for `Requests <http://python-requests.org>`_.

The OAuth 1 workflow
--------------------

OAuth 1 can seem overly complicated and it sure has its quirks. Luckily,
requests_oauthlib hides most of these and let you focus at the task at hand.

Accessing protected resources using requests_oauthlib is as simple as:

.. code-block:: pycon

    >>> from requests_oauthlib import OAuth1Session
    >>> twitter = OAuth1Session('client_key',
                                client_secret='client_secret',
                                resource_owner_key='resource_owner_key',
                                resource_owner_secret='resource_owner_secret')
    >>> url = 'https://api.twitter.com/1/account/settings.json'
    >>> r = twitter.get(url)

Before accessing resources you will need to obtain a few credentials from your
provider (i.e. Twitter) and authorization from the user for whom you wish to
retrieve resources for. You can read all about this in the full
`OAuth 1 workflow guide on RTD <http://requests-oauthlib.readthedocs.org/en/latest/oauth1_workflow.html>`_.

The OAuth 2 workflow
--------------------

OAuth 2 is generally simpler than OAuth 1 but comes in more flavours. The most
common being the Authorization Code Grant, also known as the WebApplication
flow.

Fetching a protected resource after obtaining an access token can be as simple as:

.. code-block:: pycon

    >>> from requests_oauthlib import OAuth2Session
    >>> google = OAuth2Session(r'client_id', token=r'token')
    >>> url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    >>> r = google.get(url)

Before accessing resources you will need to obtain a few credentials from your
provider (i.e. Google) and authorization from the user for whom you wish to
retrieve resources for. You can read all about this in the full
`OAuth 2 workflow guide on RTD <http://requests-oauthlib.readthedocs.org/en/latest/oauth2_workflow.html>`_.

Installation
-------------

To install requests and requests_oauthlib you can use pip:

.. code-block:: bash

    $ pip install requests requests_oauthlib

.. |build-status| image:: https://travis-ci.org/requests/requests-oauthlib.svg?branch=master
   :target: https://travis-ci.org/requests/requests-oauthlib
.. |coverage-status| image:: https://img.shields.io/coveralls/requests/requests-oauthlib.svg
   :target: https://coveralls.io/r/requests/requests-oauthlib
.. |docs| image:: https://readthedocs.org/projects/requests-oauthlib/badge/?version=latest
   :alt: Documentation Status
   :scale: 100%
   :target: https://readthedocs.org/projects/requests-oauthlib/


History
-------

v0.5.0 (4 May 2015)
+++++++++++++++++++
- Fix ``TypeError`` being raised instead of ``TokenMissing`` error.
- Raise requests exceptions on 4XX and 5XX responses in the OAuth2 flow.
- Avoid ``AttributeError`` when initializing the ``OAuth2Session`` class
  without complete client information.

v0.4.2
++++++
- New ``authorized`` property on OAuth1Session and OAuth2Session, which allows
  you to easily determine if the session is already authorized with OAuth tokens
  or not.
- New ``TokenMissing`` and ``VerifierMissing`` exception classes for OAuth1Session:
  this will make it easier to catch and identify these exceptions.

v0.4.1 (6 June 2014)
++++++++++++++++++++
- New install target ``[rsa]`` for people using OAuth1 RSA-SHA1 signature
  method.
- Fixed bug in OAuth2 where supplied state param was not used in auth url.
- OAuth2 HTTPS checking can be disabled by setting environment variable
  ``OAUTHLIB_INSECURE_TRANSPORT``.
- OAuth1 now re-authorize upon redirects.
- OAuth1 token fetching now raise a detailed error message when the
  response body is incorrectly encoded or the request was denied.
- Added support for custom OAuth1 clients.
- OAuth2 compliance fix for Sina Weibo.
- Multiple fixes to facebook compliance fix.
- Compliance fixes now re-encode body properly as bytes in Python 3.
- Logging now properly done under ``requests_oauthlib`` namespace instead
  of piggybacking on oauthlib namespace.
- Logging introduced for OAuth1 auth and session.

v0.4.0 (29 September 2013)
++++++++++++++++++++++++++
- OAuth1Session methods only return unicode strings. #55.
- Renamed requests_oauthlib.core to requests_oauthlib.oauth1_auth for consistency. #79.
- Added Facebook compliance fix and access_token_response hook to OAuth2Session. #63.
- Added LinkedIn compliance fix.
- Added refresh_token_response compliance hook, invoked before parsing the refresh token.
- Correctly limit compliance hooks to running only once!
- Content type guessing should only be done when no content type is given
- OAuth1 now updates r.headers instead of replacing it with non case insensitive dict
- Remove last use of Response.content (in OAuth1Session). #44.
- State param can now be supplied in OAuth2Session.authorize_url


