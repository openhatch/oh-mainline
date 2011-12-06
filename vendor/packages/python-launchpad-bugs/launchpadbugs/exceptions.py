import urllib2
import libxml2

from lphelper import unicode_for_libxml2
        
# deactivate error messages from the validation [libxml2.htmlParseDoc]
def noerr(ctx, str):
    pass

libxml2.registerErrorHandler(noerr, None)

#########################
# Launchpad errors
#########################

class LaunchpadError(Exception):
    def __str__(self):
        return "Something went wrong"
        
    def __repr__(self):
        t = self.__class__.__name__
        if t == "LaunchpadError":
            t = ""
        else:
            t = " %s" %t
        return "<LaunchpadError%s>" %t
        
    @property
    def value(self):
        try:
            return self.msg
        except:
            return None
    
class LaunchpadURLError(LaunchpadError, urllib2.URLError):
    def __init__(self, msg, url=None):
        self.msg = msg
        self.url = url
        
    def __str__(self):
        return """
    * message: %s
    * url: %s""" %(self.msg, self.url or "unknown")
        
class LaunchpadInternalServerError(LaunchpadError):
    def __init__(self, url):
        self.url = url
        
    def __str__(self):
        return """
    * message: An internal server error occurred. Please try again later.
    * url: %s""" %self.url
        
class LaunchpadLoginError(LaunchpadError):
    def __init__(self, url, msg=""):
        self.url = url
        self.msg = msg
        
    def __str__(self):
        if self.msg:
            m = " %s" %self.msg.strip()
        else:
            m = ""
        return """
    * message: To continue, you must log in to Launchpad.%s
    * url: %s""" %(m, self.url)
    
class LaunchpadLoginFailed(LaunchpadLoginError):
    def __init__(self, url):
        self.url = url
        
    def __str__(self):
        return """Login failed: The email address and password do not match.
    * url: %s""" %self.url
        
class LaunchpadNotAllowedError(LaunchpadLoginError):
    pass
        
        
################################
## python-launchpad-bugs Errors
################################
class PythonLaunchpadBugsError(Exception):
    def __str__(self):
        return "Something went wrong"
        
    def __repr__(self):
        t = self.__class__.__name__
        if t == "PythonLaunchpadBugsError":
            t = ""
        else:
            t = " %s" %t
        return "<PythonLaunchpadBugsError%s>" %t
        
class PythonLaunchpadBugsValueError(PythonLaunchpadBugsError, ValueError):
    def __init__(self, values={}, url="", msg=""):
        self.values = values
        self.url = url or "unknown"
        self.msg = msg
        
    def __str__(self):
        errors = ""
        msg = ""
        if self.values:
            l = len(self.values)
            if l == 1:
                errors = "\nThere is %s error\n" %l
            else:
                errors = "\nThere are %s errors\n" %len(self.values)
            for i, k in self.values.iteritems():
                errors += "    * %s: %s\n" %(i,k)
            errors.rstrip("\n")
        if self.msg:
            msg = "\n%s" %self.msg
        r = """There is a problem with the information you entered. \
 Please fix it and try again.%s%s""" %(errors, msg)
        return r.rstrip("\n")
        
class PythonLaunchpadBugsIOError(PythonLaunchpadBugsError, IOError):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg
        
class PythonLaunchpadBugsRuntimeError(PythonLaunchpadBugsError, RuntimeError):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        msg = "    * %s" %self.msg.lstrip(" *")
        return """The following error occured while using python-launchpad-bugs. Please report this error with as much information as possible.\n\t%s""" %msg
        
class PythonLaunchpadBugsParsingError(PythonLaunchpadBugsError, AssertionError):
    def __init__(self, path, url=None):
        self.path = path
        self.url = url or "unknown url"
        
    def __str__(self):
        return """Error while parsing %s (%s)""" %(self.path, self.url)
        
class PythonLaunchpadBugsXMLParsingError(PythonLaunchpadBugsParsingError):
    def __init__(self, path, xml, url=None):
        PythonLaunchpadBugsParsingError.__init__(self, path, url)
        self.xml = xml
        
    def __str__(self):
        return """Wrong XPath-Expr while parsing %s (%s)""" %(self.path, self.url)
        
        
         
            
    


##################################################################
## functions
##################################################################

def choose_LaunchpadError(value, url):
    if value == "login failed":
        return LaunchpadLoginError(url)
    elif value == 500:
        return LaunchpadInternalServerError(url)
    elif value == 404:
        return LaunchpadURLError("Page not found", url)
    elif value == 403:
        return LaunchpadNotAllowedError(url)
    else:
        return LaunchpadURLError(value, url)
        
        
UNKNOWNERROR, VALUEERROR, RUNTIMEERROR = range(3)
        
        
def _parse_page(text):
    guess_type = UNKNOWNERROR
    errors = {}
    t = libxml2.htmlParseDoc(unicode_for_libxml2(text), "UTF-8")
    e = t.xpathEval('//tr[@class="error"]')
    for i in e:
        msg = ""
        m = i.xpathEval('td/div[@class="message"]')
        if m:
            msg = m[0].content
        m = i.xpathEval("td/div/input | td/div/textarea")
        assert m
        val = m[0].prop("name")
        errors[val] = msg
    return guess_type, errors
    
        
def choose_pylpbugsError(error_type=UNKNOWNERROR, values={}, text="", url=""):
    errors = {}
    if text:
        guess_type, errors = _parse_page(text)
        if not error_type:
            error_type = guess_type
    values.update(errors)
    if error_type == VALUEERROR:
        return PythonLaunchpadBugsValueError(values, url)
    elif error_type == RUNTIMEERROR and msg:
        return PythonLaunchpadBugsRuntimeError(msg)
    else:
        return PythonLaunchpadBugsError
        
def parse_error(cond, path, xml=None, url="", msg="", error_type=UNKNOWNERROR):
    if not cond:
        if error_type:
            if error_type == VALUEERROR:
                raise PythonLaunchpadBugsValueError(url=url, msg=msg)
            elif error_type == RUNTIMEERROR and msg:
                raise PythonLaunchpadBugsRuntimeError(msg)
            else:
                raise PythonLaunchpadBugsError
        else:
            if xml is None:
                raise PythonLaunchpadBugsParsingError(path, url)
            else:
                raise PythonLaunchpadBugsXMLParsingError(path, xml, url)
        
