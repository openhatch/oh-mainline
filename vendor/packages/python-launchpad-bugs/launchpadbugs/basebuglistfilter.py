import urllib
import urlparse
from datetime import datetime
from operator import eq as OP_EQ, gt as OP_GT, lt as OP_LT

from lpconstants import BUGLIST
from bugbase import Bug as LPBug
from exceptions import PythonLaunchpadBugsValueError
    
def minbug(bug, minbug):
    return int(bug) >= minbug and bug
        
def filterbug(bug, buglist):
    return int(bug) not in buglist and bug
    
def hasbranch(bug, cls=None):
    try:
        br = bug.branches
        if not br:
            return False
        else:
            return True and bug
    except AttributeError:
        if cls:
            try:
                bug = cls(bug)
                br = bug.branches
                if not br:
                    return False
                else:
                    return True and bug
            except:
                raise RuntimeError, "Something went wrong"

def reporter(bug, reporter, cls=None):
    try:
        return bug.reporter == reporter and bug
    except AttributeError:
        if cls:
            try:
                bug = cls(bug)
                return x.reporter == reporter and bug
            except:
                raise RuntimeError, "Something went wrong"
        else:
            raise NotImplementedError, "Please define your own reporter-filterfunction"
            
            
#this is a HACK-filter to get current task-row
def get_current_task(bug, listurl, cls=None):
    try:
        t = bug.infotable
    except AttributeError:
        if cls:
            bug = cls(bug)
            t = bug.infotable
        else:
            raise NotImplementedError, "Please define your own get_current_task-filterfunction"
    
    if t._current is None:
        idx_fallback = None
        y = t.current_from_listurl(listurl)
        for idx, a in enumerate(t):
            if a.is_current(y):
                t._current = idx
                break
            if a.target == y[2]:
                idx_fallback = idx
        else:
            # there is no way to find the currrent task if we are searching
            # an package-unspecific list like https://bugs.edge.launchpad.net/ubuntu/+bugs
            # as a fallback take the last one with the right target, in this case,
            # take the last one where .target == 'ubuntu'
            
            # if idx_fallback is still None, this is worse an error message, because in this case
            # parsing went wrong
            assert not idx_fallback is None, "parsing of '%s' went wrong" %bug.url
            t._current = idx_fallback
    return bug
            
def lastcomment(bug, cls=None, **comment_def):
    """
    comment_def["user"], type: str or lphelper.user or "reporter"
    comment_def["before"], type: datetime
    comment_def["after"], type: datetime
    comment_def["operation"], in ["|","&"]
    """
    if not comment_def:
        raise TypeError, "lastcomment-function needs at least one definitional argument"
    if not set(comment_def.keys()) <= set(["user","before","after","operation", "at"]):
        raise TypeError, "unknown definitional argument for lastcomment"
    if "at" in comment_def.keys():
        if "before" in comment_def.keys() or "after" in comment_def.keys():
            raise TypeError, "'at' and 'after' or 'before' is not allowed"
    conditions = []
    operation = comment_def.get("operation","|")
    if operation not in ("|","&"):
        raise ValueError, "unknown operation"
    try:
        c = bug.comments
        if not c:
            return False
        lastcomment = c[-1]
    except AttributeError:
        if cls:
            try:
                bug = cls(bug)
                c = bug.comments
                if not c:
                    return False
                lastcomment = c[-1]
            except:
                raise RuntimeError, "Something went wrong"
        else:
            raise NotImplementedError, "Please define your own reporter-filterfunction"
    if "user" in comment_def:
        if comment_def["user"] == "reporter":
            comment_def["user"] = bug.reporter
        conditions.append(lastcomment.user == comment_def["user"])
    if "at" in comment_def:
        conditions.append(lastcomment.date.timetuple()[:3] == comment_def["at"].timetuple()[:3])
    if "before" in comment_def:
        conditions.append(lastcomment.date <= comment_def["before"])
    if "after" in comment_def:
        conditions.append(lastcomment.date >= comment_def["after"])
    #print conditions
    if operation == "&":
        return not (False in conditions) and bug
    else:
        return True in conditions and bug
        
class date_filter(object):
    DATEREPORTED = "date"
    DATEUPDATED = "date_updated"

    def __init__(self, date_def, date_kind, cls=None):
        """
        date_def = ("=" or ">" or "<" , date (type of datetime))
        """
        abort = False
        try:
            if not issubclass(cls, LPBug):
                abort = True
        except TypeError:
            if not issubclass(cls.cls, LPBug):
                abort = True
        if abort:
            raise TypeError
            
        self.cls = cls
        op, value = date_def
        self.op = {"=": OP_EQ, "<": OP_LT, ">": OP_GT}[op]
        self.value = value.date()
        today = datetime.today().date()
        if self.value > today:
            raise PythonLaunchpadBugsValueError({"date_filter(%s)" %date_kind: "The given date (%s) is in the future" %self.value})
        elif self.value == today and op == ">":
            raise PythonLaunchpadBugsValueError({"date_filter(%s)" %date_kind: "You can not search for bugs reported in the future (op='%s', date='%s')" %(op, self.value)})
        self.date_state = False
        self.kind = date_kind
        
    def __call__(self, bug):
        if not isinstance(bug, LPBug):
            bug = self.cls(bug)
        try:
            date = getattr(bug, self.kind)
        except AttributeError:
            raise ValueError, "Unable to filter the list of bugs by '%s'" %self.kind
        date = date.date()
        result = self.op(date, self.value)
        if result:
            self.date_state = True
        elif self.date_state:
            if self.kind == date_filter.DATEREPORTED:
                #Task<->Bug issue: double check all tasks
                x = map(lambda i: self.op(i.date_created.date(), self.value), bug.infotable)
                if True in x:
                    self.date_state = True
                    return bug
            self.date_state = False
            raise StopFiltering
        return result and bug

        
class datereported(date_filter):
    """ class to ensure backward compatibility """
    def __init__(self, date_def, cls=None):
        date_filter.__init__(self, date_def, date_filter.DATEREPORTED, cls)

class dateupdated(date_filter):
    """ class to ensure backward compatibility """
    def __init__(self, date_def, cls=None):
        date_filter.__init__(self, date_def, date_filter.DATEUPDATED, cls)    

class StopFiltering(StopIteration):
    pass
    
class LPBugListFilter(object):
    
    def __init__(self, func=None):
        self._functions = func or []
        self._func_cache = self._functions[:]
        
    @property
    def functions(self):
        return self._functions
        
    def reset(self):
        self._functions = self._func_cache

def parse_options(url_opt):
    result = {}
    if url_opt:
        for i in urllib.unquote_plus(url_opt).split("&"):
            k = i.split("=")
            try:
                result[k[0]].add(k[1])
            except:
                result[k[0]] = set([k[1]])
    return result
    

class URLBugListFilter(LPBugListFilter):
    
    ADD = 1
    OVERWRITE = 2
    CONFLICTS_ERROR = 3
    
    OPTION_DICT = { "status": "field.status:list",
                    "importance": "field.importance:list",
                    "tag": "field.tag",
                    "assignee": "field.assignee",
                    "reporter": "field.bug_reporter",
# the UI now refers to the bug contact as a bug supervisor and bughelper never used contact from what I saw
# could we drop contact from the dictionary? - bdmurray 20080613
                    "contact": "field.bug_supervisor",
                    "supervisor": "field.bug_supervisor",
                    "commenter": "field.bug_commenter",
                    "subscriber": "field.subscriber",
                    "duplicates": "field.omit_dupes",
                    "component": "field.component",
                    "cve": "field.has_cve",
                    "has-patch": "field.has_patch",
                    "upstream-status": "field.status_upstream",
                    "milestone": "field.milestone:list",
                    "orderby": "orderby",
                    "batch": "batch"}
                    
        
    def __init__(self, url_opt="", func=[], opt_type=CONFLICTS_ERROR):
        
        self._conflicts_error = opt_type
        self.__url_opt = parse_options(url_opt)
        self.__baseurl = ()
        self.__url_cache = self.__url_opt.copy()
        LPBugListFilter.__init__(self, func)
        
    def __call__(self, baseurl):
        self.baseurl = baseurl
        return self
        
    def reset(self):
        self._functions = self._func_cache
        self.__url_opt = self.__url_cache
        
    def get_baseurl(self):
        assert self.__baseurl, "needs baseurl"
        x = list(self.__baseurl[:3])
        x.append(self.urlopt)
        x.append("")
        return urlparse.urlunsplit(x)
        
    def set_baseurl(self, baseurl):
        self.__baseurl = urlparse.urlsplit(baseurl)
        self._add_default_urlopt(baseurl)
    baseurl = property(get_baseurl, set_baseurl)
        
    @property
    def urlopt(self):
        return urllib.urlencode(self.__url_opt,True)
        
    def add_option(self, option, value):
        if not option in URLBugListFilter.OPTION_DICT:
            raise ValueError
        if option == "component":
            value = set([BUGLIST.COMPONENT_DICT[i] for i in value])
        self._add_option({URLBugListFilter.OPTION_DICT[option]: value})
        
        
    def _add_default_urlopt(self, url):
        u = urlparse.urlsplit(url)
        r = parse_options(u[3])
        self._add_option(r)
        
    def _add_option(self, r):
        if self._conflicts_error == URLBugListFilter.ADD:
            for i,k in r.iteritems():
                try:
                    self.__url_opt[i] = self.__url_opt[i].union(k)
                except KeyError:
                    self.__url_opt[i] = k
        elif self._conflicts_error == URLBugListFilter.OVERWRITE:
            self.__url_opt = r
        elif self._conflicts_error == URLBugListFilter.CONFLICTS_ERROR:
            for i,k in r.iteritems():
                if isinstance(k, set) and len(k) == 1:
                    k = k.pop()
                if i in self.__url_opt:
                    if not self.__url_opt[i] == k:
                        try:
                            if k in self.__url_opt[i]:
                                pass
                        except:
                            raise ValueError, "ValueError: conflict filter options (%s)" %i
                else:
                    self.__url_opt[i] = k
        else:
            raise ValueError, "unknown type=%s" %type
        
        


        
#some test-cases
if __name__ == '__main__':
    import connector as Connector
    tBug = Connector.ConnectBug(method="text")
    tBuglist = Connector.ConnectBugList(method="text")
    from datetime import datetime
    
    f = LPBugListFilter([lambda x: minbug(x, 175000)])#, lambda x: lastcomment(x, tBug, user="thekorn", before=datetime(2007,10,16))])
    bugs = [172802,
 137574,
 177608,
 146377,
 175946,
 162814,
 173005,
 177202,
 116243,
 138837,
 174103,
 172882,
 172637,
 172670]
    print f.filter(bugs)
     
    f = URLBugListFilter(func=(lambda x: lastcomment(x, tBug, user="reporter"),))
    bugs = tBuglist(f("https://bugs.edge.launchpad.net/python-launchpad-bugs/+bugs?field.searchtext=&orderby=-importance&search=Search&field.status%3Alist=NEW&field.status%3Alist=INCOMPLETE_WITH_RESPONSE&field.status%3Alist=CONFIRMED&field.status%3Alist=TRIAGED&field.status%3Alist=INPROGRESS&field.status%3Alist=FIXCOMMITTED&field.assignee=&field.bug_reporter=&field.omit_dupes=on&field.has_patch=&field.has_no_package="))
    print bugs, len(bugs)
        
