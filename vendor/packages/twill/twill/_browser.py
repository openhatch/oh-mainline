"""
A subclass of the mechanize browser patched to fix various bits.
"""

# wwwsearch imports
from _mechanize_dist import Browser as MechanizeBrowser

import wsgi_intercept
from utils import FixedHTTPBasicAuthHandler, FunctioningHTTPRefreshProcessor

def build_http_handler():
    from _mechanize_dist._urllib2 import HTTPHandler

    class MyHTTPHandler(HTTPHandler):
        def http_open(self, req):
            return self.do_open(wsgi_intercept.WSGI_HTTPConnection, req)

    return MyHTTPHandler

class PatchedMechanizeBrowser(MechanizeBrowser):
    """
    A patched version of the mechanize browser class.  Currently
    installs the WSGI intercept handler & fixes a problem with
    mechanize/urllib2 Basic Authentication.
    """
    def __init__(self, *args, **kwargs):
        # install WSGI intercept handler.
        self.handler_classes['http'] = build_http_handler()

        # fix basic auth.
        self.handler_classes['_basicauth'] = FixedHTTPBasicAuthHandler

        # make refresh work even for somewhat mangled refresh directives.
        self.handler_classes['_refresh'] = FunctioningHTTPRefreshProcessor

        MechanizeBrowser.__init__(self, *args, **kwargs)
