"""
TODO (thekorn20080709):
    * auto fetching of edge cookie is not working
       - no idea why an edge cookies is not created when accessing edge.launchpad.net
    * cookie lifetime (auto extend?)
    * adjust almost all testcases and connector
"""

import urllib2
import multipartpost_handler
import cookielib
import cStringIO as StringIO
import time
import urlparse
import cPickle
import base64
from tempfile import mkstemp
try:
    import sqlite3 as sqlite
except ImportError:
    try:
        from pysqlite2 import dbapi2 as sqlite
    except ImportError:
        raise ImportError, "no module named sqlite3 or pysqlite2.dbapi2"
import os

import exceptions
import utils
from lpconstants import BASEURL, HTTPCONNECTION
from config import Config

class _result(object):
    """ represents an object returned by HTTPConnection. """
    def __init__(self, contenttype=None, text=None, url=None):
        assert contenttype or text or url, "at least one argument needed"
        self.contenttype = contenttype
        self.text = text
        self.url = url
        
class LPCookieProcessor(urllib2.HTTPCookieProcessor):
    """ CookieProcessor with special functionality regarding launchpad.net
        cookies.
    """
    
    @staticmethod
    def sqlite_to_txt(cookiefile ,domain):
        match = '%%%s%%' % domain
        con = sqlite.connect(cookiefile)
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies where host like ?", [match])
        ftstr = ["FALSE","TRUE"]
        (tmp, tmpname) = mkstemp()
        os.write(tmp, "# HTTP Cookie File\n")
        for item in cur.fetchall():
            str = "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( item[0], \
                   ftstr[item[0].startswith('.')], item[1], \
                   ftstr[item[2]], item[3], item[4], item[5])
            os.write(tmp, str)
        os.close(tmp)
        return tmpname
        
    def __nonzero__(self):
        return ".launchpad.net" in [i.domain for i in self.cookiejar]
        
    def load_file(self, cookiefile):
        if cookiefile:
            cj = cookielib.MozillaCookieJar()
            if cookiefile[-6:] == "sqlite":
                cookies = self.sqlite_to_txt(cookiefile, "launchpad.net")
                try:
                    cj.load(cookies)
                except:
                    os.unlink(cookies)
                    raise IOError, "Invalid cookie file"
                os.unlink(cookies)
            else:
                cj.load(cookiefile)
            for cookie in cj:
                self.cookiejar.set_cookie(cookie)
            return True
        else:
            raise IOError, "No cookie file given"
        
    def get_cookie(self, name, domain=None):
        domain = domain or ".launchpad.net"
        for i in self.cookiejar:
            if i.name == name and i.domain == domain:
                return i
        return False
        
    def change_inhibit_beta_redirect(self, mode):
        """
        cj.clear(".launchpad.net", "/", "inhibit_beta_redirect")

        name inhibit_beta_redirect
        domain .launchpad.net
        path /
        Cookie(version=0, name='inhibit_beta_redirect', value='1', port=None, port_specified=False, domain='.launchpad.net', domain_specified=True, domain_initial_dot=True, path='/', path_specified=False, secure=True, expires=1202139678, discard=False, comment=None, comment_url=None, rest={}, rfc2109=False)
        """
        if mode in (HTTPCONNECTION.MODE.DEFAULT, HTTPCONNECTION.MODE.EDGE):
            #delete redirecting cookie
            try:
                self.cookiejar.clear(".launchpad.net", "/", "inhibit_beta_redirect")
            except KeyError:
                pass
        elif mode == HTTPCONNECTION.MODE.STABLE:
            #enable redirection cookie
            #redirection for 2 hours
            c_expires = int(time.time()) + 2 * 60 * 60
            c = self.get_cookie("inhibit_beta_redirect")
            if not c:
                # create one
                try:
                    c = cookielib.Cookie(version=0,
                        name='inhibit_beta_redirect', value='1', port=None,
                        port_specified=False, domain='.launchpad.net',
                        domain_specified=True, domain_initial_dot=True,
                        path='/', path_specified=False, secure=True,
                        expires=c_expires, discard=False, comment=None,
                        comment_url=None, rest={}, rfc2109=False)
                except TypeError:
                    #missing 'rfc2109' argument in python 2.4
                    c = cookielib.Cookie(version=0,
                        name='inhibit_beta_redirect', value='1', port=None,
                        port_specified=False, domain='.launchpad.net',
                        domain_specified=True, domain_initial_dot=True,
                        path='/', path_specified=False, secure=True,
                        expires=c_expires, discard=False, comment=None,
                        comment_url=None, rest={})                    
                self.cookiejar.set_cookie(c)
            else:
                # check if expired
                # more time
                pass
        return self.get_cookie("inhibit_beta_redirect")
        
    def save_cookie(self, filename):
        cj = cookielib.MozillaCookieJar()
        for cookie in self.cookiejar:
            cj.set_cookie(cookie)
        cj.save(filename)
    
def pickle_cookie_load(cookie_string):
    """ load a cookie instance from the value of the config file """
    try:
        cookie_string = base64.decodestring(cookie_string)
    except Exception:
        pass
    try:
        c = cPickle.loads(cookie_string)
        if isinstance(c, cookielib.Cookie):
            return c
        else:
            return None
    except Exception:
        return None
    
def pickle_cookie_dump(cookie_obj):
    """ dump a cookie object and encode the resulting string """
    if not isinstance(cookie_obj, cookielib.Cookie):
        if cookie_obj is None:
            return ""
        raise TypeError
    return base64.encodestring(cPickle.dumps(cookie_obj))
        
class HTTPConnectionConfig(Config):
    """ read the configuration of the HTTPConnection from a config file. """
    
    # define load and save handler for the cookie objects    
    Config.MAPPING["cookies"] = {"lp": (pickle_cookie_load, pickle_cookie_dump),
                                 "edge": (pickle_cookie_load, pickle_cookie_dump),
                                 "staging": (pickle_cookie_load, pickle_cookie_dump),
                                 "inhibit_beta_redirect": (pickle_cookie_load, pickle_cookie_dump)}

class HTTPConnection(object):
    """ class to manage a https connection to launchpad.net. """
    def __init__(self, cookiefile=None, attempts=5, content_types=None,
                    config_file=None, config_ignore=None):
        self.__config = HTTPConnectionConfig(config_file, config_ignore)
        self.__username = None
        version = "python-launchpad-bugs/%s (Python-urllib2/%s) (user: %s)" %(utils.find_version_number(show_nick=True),urllib2.__version__, self.user)
        self.__cookiefile = cookiefile
        self.__cookie_handler = LPCookieProcessor()
        self.__opener = urllib2.build_opener(self.__cookie_handler)
        self.__opener.addheaders = [('User-agent', version)]
        self.__poster = urllib2.build_opener(self.__cookie_handler, multipartpost_handler.MultipartPostHandler)
        self.__poster.addheaders = [('User-agent', version)]
        self.__attempts = attempts
        self.content_types = content_types or ["text/html","text/plain"]
        self.__progress_hook = None
        self.__mode = HTTPCONNECTION.MODE.DEFAULT
        self.__cookies_to_dump = []
        for key, value in self.__config["cookies"].iteritems():
            if value is None:
                self.__cookies_to_dump.append(key)
            else:
                self.__cookie_handler.cookiejar.set_cookie(value)
        
    def get_auth(self):
        return self.__cookie_handler
        
    def set_auth(self, auth):
        if isinstance(auth, str):
            self.__cookiefile = auth
            try:
                return self.__cookie_handler.load_file(self.__cookiefile)
            except IOError, e:
                raise exceptions.PythonLaunchpadBugsIOError(str(e))
        elif isinstance(auth, dict):
            try:
                email = auth["email"]
                password = auth["password"]
            except KeyError:
                raise ValueError, "The argument of .set_auth() needs to be either a path to a valid \
mozilla cookie-file or a dict like {'email':<lp-email-address>,'password':<password>}, but it is %s" %auth
            self._do_login(email, password)
        else:
            raise ValueError, "The argument of .set_auth() needs to be either a path to a valid \
mozilla cookie-file or a dict like {'email':<lp-email-address>,'password':<password>}, but it is %s" %auth

    def _do_login(self, email, password, server=None):
        if server is None:
            server = (  "https://bugs.launchpad.net/+login",
                        "https://bugs.edge.launchpad.net/+login",
                        "https://bugs.staging.launchpad.net/+login",)
        for url in server:
            try:
                r = self.post(url, {"loginpage_email": email,
                                    "loginpage_password": password,
                                    "loginpage_submit_login":"Log In"})
            except exceptions.LaunchpadLoginError:
                raise exceptions.LaunchpadLoginFailed(url)
            except exceptions.LaunchpadError, e:
                raise exceptions.LaunchpadLoginError(url,
                            "Connection failed with %s" %e)
        
    @property
    def user(self):
        return self.__username or self.__config["user"]["lplogin"] or "unknown"
        
    def set_username(self, user):
        self.__username = user
            
    def needs_login(self, url=None):
        """ checks if authentication is needed.
        this considers connection-mode and cookies
        """
        url = self._change_url(url or "https://launchpad.net/people/+me")
        url = self.__opener.open(url).geturl()
        return url.endswith("+login")
        
    def get(self, url):
        return self._safe_urlopen(url, None, False)
        
    def post(self, url, data):
        return self._safe_urlopen(url, data, True)
            
    def set_mode(self, mode):
        assert mode in (HTTPCONNECTION.MODE.DEFAULT,
                        HTTPCONNECTION.MODE.EDGE,
                        HTTPCONNECTION.MODE.STABLE,
                        HTTPCONNECTION.MODE.STAGING), "Unknown mode"
        self.__mode = mode
        c = self.__cookie_handler.change_inhibit_beta_redirect(self.__mode)
        self.__config["cookies"]["inhibit_beta_redirect"] = c or None
        if "inhibit_beta_redirect" in self.__cookies_to_dump:
            self.__cookies_to_dump.remove("inhibit_beta_redirect")
        self.__config.save()
            
    def _change_url(self, url):
        u = list(urlparse.urlsplit(url))
        if self.__mode == HTTPCONNECTION.MODE.EDGE:
            # return *.edge.launchpad.net/...
            u[1] = u[1].replace("staging.","") #remove staging from netloc
            u[1] = u[1].replace("edge.","") # remove edge from netloc
            u[1] = u[1].replace("launchpad.net", "edge.launchpad.net")
        elif self.__mode == HTTPCONNECTION.MODE.STAGING:
            # return *.staging.launchpad.net/...
            u[1] = u[1].replace("staging.","") #remove staging from netloc
            u[1] = u[1].replace("edge.","") # remove edge from netloc
            u[1] = u[1].replace("launchpad.net", "staging.launchpad.net")
            u[1] = u[1].replace("launchpadlibrarian.net", "staging.launchpadlibrarian.net")

        elif self.__mode == HTTPCONNECTION.MODE.STABLE:
            # return *.launchpad.net/...
            u[1] = u[1].replace("staging.","") #remove staging from netloc
            u[1] = u[1].replace("edge.","") # remove edge from netloc
        return urlparse.urlunsplit(u)
        
        
    def _safe_urlopen(self, url, data, post):
        url = self._change_url(url)
        count = 0
        text = None
        contenttype = None
        geturl = None
        sock = None
        if post:
            opener = self.__poster
        else:
            opener = self.__opener
        while count < self.__attempts:
            #print "count: %s, url: %s" %(count,url) #DEBUG
            try:
                if url[:4] != 'http':
                    url_old = url
                    url = 'https://' + url
                    print "wrong url <%s>, try <%s>" %(url_old, url)
                if data:
                    sock = opener.open(url,data)
                else:
                    sock = opener.open(url)
                contenttype = sock.info()["Content-type"]
                #~ print sock.geturl()
                if sock.geturl().endswith("+login"):
                    raise exceptions.LaunchpadLoginError(url)
                for ct in self.content_types:
                    if contenttype.startswith(ct):
                        if self.__progress_hook is None:
                            text = sock.read()
                            geturl = sock.geturl()
                            sock.close()
                        else:
                            tmp_text = StringIO.StringIO()
                            i = 0
                            counter = 0
                            size = int(sock.info()['Content-Length'])
                            while i < size:
                                tmp_text.write(sock.read(self.__block_size))
                                i += self.__block_size
                                counter += 1
                                self.__progress_hook(counter, self.__block_size, size)
                            text = tmp_text.getvalue()
                            geturl = sock.geturl()
                            sock.close()
                            tmp_text.close()
                        x = self.__cookies_to_dump[:]
                        for i in x:
                            c = self.__cookie_handler.get_cookie(i)
                            if c:
                                self.__config["cookies"][i] = c
                                self.__cookies_to_dump.remove(i)
                        if not self.__cookies_to_dump == x:
                            self.__config.save()
                        return _result(contenttype=contenttype,text=text, url=geturl)
                sock.close()
                raise IOError, "unsupported contenttype (contenttype=%s, url=%s)" %(contenttype, url)
            except urllib2.URLError, e:
                try:
                    error = e.code
                except AttributeError:
                    error = e.reason
                count += 1
        raise exceptions.choose_LaunchpadError(error, url)
        
    def set_progress_hook(self, hook_func, blocksize=4096):
        assert blocksize, "blocksize needs to be an integer greater than 0"
        self.__block_size = blocksize
        assert callable(hook_func), "hook_func needs to be callable with three arguments"
        self.__progress_hook = hook_func
        
    def save_cookie(self, filename):
        self.__cookie_handler.save_cookie(filename)
        
        
if __name__ == '__main__':
    c = HTTPConnection()
    print repr(c.user), c.user
    
    def example_hook(counter, block_size, size):
        print (counter, block_size, size)
        
    c.set_progress_hook(example_hook)
    x = c.get("https://bugs.edge.launchpad.net/ubuntu/+source/linux/+bug/200500/")
    print len(x.text)
