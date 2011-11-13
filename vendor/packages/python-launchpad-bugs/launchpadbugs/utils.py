# Written by Henrik Nilsen Omma
# (C) Canonical, Ltd. Licensed under the GPL

import os
import re
import subprocess
import libxml2
import urlparse

from exceptions import LaunchpadURLError, PythonLaunchpadBugsValueError
from lpconstants import BASEURL

try:
    from bzrlib.branch import Branch
    from bzrlib import trace
    HAVE_BZR = True    
except:
    HAVE_BZR = False

def get_version_from_changelog(path):
    # look/set what version we have
    changelog = os.path.join(path, "debian/changelog")
    if os.path.exists(changelog):
        head=open(changelog).readline()
        match = re.compile(".*\((.*)\).*").match(head)
        if match:
            return match.group(1)
    return "unknown"
    

# deactivate error messages from the validation [libxml2.htmlParseDoc]
def noerr(ctx, str):
    pass

libxml2.registerErrorHandler(noerr, None)

def find_version_number(show_nick=False):
    path = os.path.join(os.path.dirname(__file__), "..")

    # We're using a package
    if path.startswith('/usr'):
        output = subprocess.Popen(["dpkg-query", "-W", "python-launchpad-bugs"], 
                                   stdout=subprocess.PIPE).communicate()[0]
        try:
            return output.split()[1]
        except:
            # not installed as a package
            return "unknown"
    if HAVE_BZR:
        try:
            trace.be_quiet()
            trace.enable_default_logging()
            version = get_version_from_changelog(path)
            if os.path.islink(os.path.dirname(__file__)):
                path = os.path.realpath(os.path.dirname(__file__))
            branch = Branch.open_containing(path)[0]
            bzr_revno = branch.revno()
            if show_nick:
                nick = branch.nick
                return "%sr%s, branch nick: %s" % (version, bzr_revno, nick)
            else:
                return "%sr%s" % (version, bzr_revno)
        except:
            pass
    return "unknown"

def package_exists(package_name):
    import apt_pkg
    try:
        apt_pkg.init()
        sources = apt_pkg.GetPkgSrcRecords()
        sources.Restart()
        if not sources.Lookup(str(package_name)):
            return False
        else:
            return True
    except:
        print "You must put some 'source' URIs in your sources.list"
        return False

def lazy_makedir(directory):
    try:
        os.makedirs(directory)
    except:
        pass
    
def remove_obsolete_attachments(path, open_bugs):
    open_bug_nrs = set(map(lambda a: str(a.nr), open_bugs))
    if os.path.exists(path):
        bugs = set(filter(lambda a: os.path.isdir(os.path.join(path, a)), 
                          os.listdir(path)))
        for bug in bugs.difference(bugs.intersection(open_bug_nrs)):
            bug_path = os.path.join(path, bug)
            if os.path.isdir(bug_path):
                os.system("rm -r %s" % bug_path)
                
      
def bugnumber_to_url(nr):
    return "%s/bugs/%s" %(BASEURL.BUG, nr)

def valid_lp_url(url, type):
    """ validates given 'url' against 'type'
    raises PythonLaunchpadBugsValueError for invalid url and modifies
    if necessary. Currently only validation for 'scheme' and 'netloc'
    part of the url is implemented, path needs to be done but is more
    complicated.    
    """
    if not url:
        raise PythonLaunchpadBugsValueError(msg="url is empty")
    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    
    # adjust type
    # we only need netloc part as type
    _, type, x, _, _ = urlparse.urlsplit(type)
    if not type:
        type = x
    assert type, "unable to validate against given type"
    
    if not scheme and not netloc:
        if not path.startswith("/"):
            scheme = "http"
            x = path.split("/", 1)
            if len(x) == 1:
                netloc = x[0]
                path = ""
            else:
                netloc = x[0]
                path = x[1]
    # check scheme
    # change http:// to https:// as they will be redirected anyway
    if not scheme or scheme == "http":
        scheme = "https"
    if not scheme in ("http", "https"):
        raise PythonLaunchpadBugsValueError(values={"url": url, "type": type}, msg="Wrong schema")
    # check netloc based on type
    if not netloc:
        netloc = type
    else:
        n = netloc
        prefix = None
        if "edge." in netloc:
            n = netloc.replace("edge.", "")
            prefix = "edge"
        elif "staging." in netloc:
            n = netloc.replace("staging.", "")
            prefix = "staging"
        if n != type:
            if n == "launchpad.net":
                # 'https://launchpad.net/*' is automatically redirected to the best url
                netloc = type
                if prefix:
                    netloc = netloc.replace(".launchpad", ".%s.launchpad" %prefix)
            else:
                raise PythonLaunchpadBugsValueError(values={"url": url, "type": type}, msg="Wrong type")
    
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))
        
        
def debug(*arg,**args):
    for i in arg:
        if type(i) == type(dict()):
            for k in i:
                print "%s : %s" %(k, i[k])
        else:
            print i
    for k in args:
        print k, args[k]
        
        
def get_open_milestones(dist=None, package=None, project=None):
    url = BASEURL.BUG
    if dist:
        url += "/%s" %dist
        if package:
            url += "/+source/%s" %package
    elif project:
        url += "/%s" %project
    else:
        raise TypeError, "Wrong number of arguments"
    url += "/+bugs?advanced=1"
    try:
        from http_connection import HTTPConnection
        text = HTTPConnection().get(url).text
    except LaunchpadURLError:
        raise PythonLaunchpadBugsValueError({"get_open_milestones":"Can't find milestones for (dist=%s, package=%s, project=%s)" %(dist, package, project)},
                                             url)
    ctx = libxml2.htmlParseDoc(text, "UTF-8")
    milestones = ctx.xpathEval('//input[@name="field.milestone:list"]')
    for m in milestones:
        identifier = m.prop("id").split(".", 1).pop()
        yield (identifier, int(m.prop("value")))
        x = identifier.split(" ")[1:]
        if x:
            yield (" ".join(x), int(m.prop("value")))
    
    
    
