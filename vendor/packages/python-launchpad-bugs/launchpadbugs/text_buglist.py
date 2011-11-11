"""
TODO:
  * implement BugList.sort()
"""
import urlparse

from bugbase import LPBugInfo, Bug as LPBug
from buglistbase import LPBugList, LPBugPage
from utils import valid_lp_url
from lpconstants import BASEURL
from lphelper import sort

class BugInfo(LPBugInfo):
    # TODO: use same attribute names like Bug.Bug
    def __init__(self, nr, all_tasks):
        LPBugInfo.__init__(self, nr, None, None, None, None, None, all_tasks)
        
        
class BugPage(LPBugPage):
    """
    grab content of a single bug-table    
    """
    @staticmethod
    def find_parse_function(connection, url, all_tasks):
        """ this can extended to parse other listtypes (like
            https://edge.launchpad.net/ubuntu/+milestone/gutsy-updates"""
        url = valid_lp_url(url, BASEURL.BUGPAGE)
        u = urlparse.urlsplit(url)
        if u[2].endswith("+bugs-text"):
            pass
        elif u[2].endswith("+bugs"):
            url = urlparse.urlunsplit((u[0],u[1],"%s-text"%u[2],u[3],u[4]))
        else:
            url = urlparse.urlunsplit((u[0],u[1],"%s/+bugs-text"%u[2],u[3],u[4]))
        lp_content = connection.get(url)
        result = BugPage.parse_text_bugpage(lp_content.text, all_tasks, url)
        return result
        
    @staticmethod
    def parse_text_bugpage(text, all_tasks, url):
        bugs = text.split("\n")
        def _parse():
            for i in bugs:
                if i:
                    yield BugInfo(i, all_tasks)
        return _parse(), False, len(bugs), len(bugs)


class BugList(LPBugList):
    """
    returns a SET of BugInfo objects
    searches baseurl and its following pages
    """
    def __init__(self, baseurl, connection=None, all_tasks=False, progress_hook=None):
        if hasattr(baseurl, "baseurl"):
            baseurl.baseurl = valid_lp_url(baseurl.baseurl, BASEURL.BUGLIST)
        else:
            baseurl = valid_lp_url(baseurl, BASEURL.BUGLIST)
        LPBugList.__init__(self, baseurl, connection, all_tasks,
                    BugPage, progress_hook)
        
    def add(self, item):
        assert isinstance(item, (LPBugInfo, LPBug))
        LPBugList.add(self, item)
    
    def sort(self, optsort):
        """ returns a list of bug objects sorted by optsort
        if one of the element in the list is an instance of LPBugInfo
        the list can only be sorted by the bugnumber """
        attribute = optsort.strip("-")
        m = filter(lambda x: isinstance(x, LPBugInfo), self)
        if m and not attribute == "nr":
            raise TypeError, "text buglists containing LPBugInfo objects can only be sorted by nr"
        cmp_func = lambda x, y: sort(x, y, attribute)
        isreverse = optsort.startswith("-")
        return sorted(self, cmp=cmp_func, reverse=isreverse)
