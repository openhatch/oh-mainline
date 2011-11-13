"""
TODO:
    * maybe move initialisation of libxml2 parser to utils
"""

import libxml2
import urlparse
import re
from bugbase import LPBugInfo, Bug as LPBug
from buglistbase import LPBugList, LPBugPage
from lphelper import user, unicode_for_libxml2, sort
from lpconstants import BASEURL
from exceptions import parse_error
from lptime import LPTime
from utils import valid_lp_url, bugnumber_to_url

#deactivate error messages from the validation [libxml2.htmlParseDoc]
def noerr(ctx, str):
    pass
libxml2.registerErrorHandler(noerr, None)


class BugInfo(LPBugInfo):
    # TODO: use same attribute names like Bug.Bug
    def __init__(self, nr, url, status, importance, summary, package=None, all_tasks=False):
        url = valid_lp_url(url, BASEURL.BUG)
        LPBugInfo.__init__(self, nr, url, status, importance, summary, package, all_tasks)
        
class BugInfoWatches(LPBugInfo):
    def __init__(self, lp_url, lp_bugnr, lp_title, watch_url, watch_bugnr, watch_status, private, all_tasks):
        url = valid_lp_url(lp_url, BASEURL.BUG)
        LPBugInfo.__init__(self, lp_bugnr, url, None, None, lp_title, None, all_tasks)
        
        # add additional attributes
        self.watch_url = watch_url or "unknown"
        self.watch_bugnr = watch_bugnr
        self.watch_status = watch_status or "unknown"
        self.private = private
        
re_url_to_project = re.compile(r'/(\w+)/\+bug/\d+')
class ExpBugInfo(LPBugInfo):
    def __init__(self, bugnumber, url, importance, summary, private, package, date_last_update, all_tasks=False):
        url = valid_lp_url(url, BASEURL.BUG)
        if package is None:
            u = urlparse.urlsplit(url)
            m = re_url_to_project.match(u[2])
            if m:
                package = m.group(1)
        LPBugInfo.__init__(self, bugnumber, url, None, importance, summary, package, all_tasks)
        
        # add additional attributes
        self.private = private
        self.date_last_update = date_last_update
        

class BugPage(LPBugPage):
    """
    grab content of a single bug-table    
    """
    @staticmethod
    def find_parse_function(connection, url, all_tasks):
        url = valid_lp_url(url, BASEURL.BUGPAGE)
        lp_content = connection.get(url)
        xmldoc = libxml2.htmlParseDoc(unicode_for_libxml2(lp_content.text), "UTF-8")
        u = urlparse.urlsplit(url)
        if "+milestone" in u[2]:
            result = BugPage.parse_html_milestone_bugpage(xmldoc, all_tasks, url)
        elif "+expirable-bugs" in u[2]:
            result = BugPage.parse_html_expirable_bugpage(xmldoc, all_tasks, url)
        elif "bugs/bugtrackers" in u[2]:
            result = BugPage.parse_html_bugtracker_bugpage(xmldoc, all_tasks, url)
        else:
            result = BugPage.parse_html_bugpage(xmldoc, all_tasks, url)
        return result
        
    @staticmethod
    def parse_html_bugpage(xmldoc, all_tasks, debug_url):
        def _parse():
            if xmldoc.xpathEval('//div/p[contains(.,"There are currently no open bugs.")]') or xmldoc.xpathEval('//div/p[contains(.,"No results for search")]'):
                raise StopIteration
                
            # count number of columns
            # Bug-Pages have seven columns: icon|nr|summary(url)|icon(milestone|branch|blueprint)|package|importance|status
            # personal Bug-Pages have six columns: icon|nr|summary(url)|package|importance|status
            # TODO: look for more simple XPath-statements
            col = int(xmldoc.xpathEval('count(//table[@id="buglisting"]//thead//tr//th[not(@*)])'))
            for span in xmldoc.xpathEval('//table[@id="buglisting"]//thead//tr//@colspan'):
                col += int(span.content)

            assert col == 6 or col == 7, "Parsing of this page (%s) is not \
    supported by python-launchpad-bugs" %debug_url
            bug_table_rows = xmldoc.xpathEval('//table[@id="buglisting"]//tbody//tr')
            for row in bug_table_rows:
                out = []
                for i in xrange(2,col+1):
                    if i == 3:
                        expr = 'td[' + str(i) + ']//a'
                    else:
                        expr = 'td[' + str(i) + ']/text()'
                    res = row.xpathEval(expr)
                    parse_error(res, "BugPage.parse_html_bugpage._parse.row[%s]" %i, xml=row, url=debug_url)
                    if i == 3:
                        out.append(res[0].prop("href"))
                    out.append(res[0].content)
                #drop icon td
                out.pop(3)
                # package is optional, move package to the end of the list
                if len(out) == 6:
                    out.append(out.pop(3))
                else:
                    out.append(None)
                yield BugInfo(out[0], out[1], out[4],out[3], out[2], out[5], all_tasks)

        next = xmldoc.xpathEval('//div[@class="lesser"]//a[@rel="next"]//@href')
        m = xmldoc.xpathEval('//td[@class="batch-navigation-index"]')
        if m:
            m = m.pop()
            n = re.search(r'(\d+)\s+results?', m.content)
            parse_error(n, "BugPage.parse_html_bugpage.length", url=debug_url)
            length = n.group(1)
            n = m.xpathEval("strong")
            batchsize = int(n[1].content) - int(n[0].content) + 1
        else:
            length = batchsize = 0
        if next:
            return _parse(), next[0].content, batchsize, int(length)
        return _parse(), False, batchsize, int(length)
        
    @staticmethod
    def parse_html_milestone_bugpage(xmldoc, all_tasks, debug_url):
        def _parse():
            bug_table_rows = xmldoc.xpathEval('//table[@id="milestone_bugtasks"]//tbody//tr')
            for row in bug_table_rows:
                x = row.xpathEval('td[1]//span/img')
                parse_error(x, "BugPage.parse_html_milestone_bugpage.importance", xml=row, url=debug_url)
                importance = x[0].prop("alt").strip("()").title()
                x = row.xpathEval('td[2]')
                parse_error(x, "BugPage.parse_html_milestone_bugpage.nr", xml=row, url=debug_url)
                nr = x[0].content
                x = row.xpathEval('td[3]/a')
                parse_error(x, "BugPage.parse_html_milestone_bugpage.url", xml=row, url=debug_url)
                url = x[0].prop("href")
                summary = x[0].content
                x = row.xpathEval('td[5]//a')
                if x:
                    usr = user.parse_html_user(x[0])
                else:
                    usr = user(None)
                x = row.xpathEval('td[6]/span[2]')
                parse_error(x, "BugPage.parse_html_milestone_bugpage.status", xml=row, url=debug_url)
                status = x[0].content
                x = BugInfo(nr, url, status, importance, summary, None, all_tasks)
                x.assignee = usr
                yield x
        m = xmldoc.xpathEval('//h2[@id="bug-count"]')
        length = batchsize = int(m[0].content.split(" ")[0])
        return _parse(), False, batchsize, length
        
    @staticmethod
    def parse_html_bugtracker_bugpage(xmldoc, all_tasks, debug_url):
        def _parse():
            rows = xmldoc.xpathEval('//table[@class="sortable listing" and @id="latestwatches"]/tbody//tr')
            for row in rows:
                lp_url, lp_bugnr, lp_title, watch_url, watch_bugnr, watch_status, private = [None] * 7
                data = row.xpathEval("td")
                parse_error(len(data) == 3, "BugPage.parse_html_bugtracker_bugpage.len_td=%s" %len(data), xml=row, url=debug_url)
                x = data[0].xpathEval("a")
                if x:
                    lp_url = x[0].prop("href")
                    lp_bugnr = int(lp_url.split("/").pop())
                    lp_title = x[0].content.split(":", 1)[-1].strip("\n ")
                    
                    x = data[1].xpathEval("a")
                    parse_error(x, "BugPage.parse_html_bugtracker_bugpage.watch_url", xml=row, url=debug_url)
                    watch_url = x[0].prop("href")
                    watch_bugnr = x[0].content
                    
                    watch_status = data[2].content
                else:
                    x = data[0].content
                    parse_error("(Private)" in x, "BugPage.parse_html_bugtracker_bugpage.private", xml=row, url=debug_url)
                    private = True
                    x = x.split("#").pop()
                    lp_bugnr = int(x.split(":").pop(0))
                    lp_url = bugnumber_to_url(lp_bugnr)
                b = BugInfoWatches( lp_url, lp_bugnr, lp_title, watch_url,
                                    watch_bugnr, watch_status, bool(private), all_tasks)
                yield b

        next = xmldoc.xpathEval('//td[@class="batch-navigation-links"]//a[@rel="next"]//@href')
        m = xmldoc.xpathEval('//td[@class="batch-navigation-index"]')
        if m:
            m = m.pop()
            n = re.search(r'(\d+)\s+results?', m.content)
            parse_error(n, "BugPage.parse_html_bugpage.length", url=debug_url)
            length = n.group(1)
            n = m.xpathEval("strong")
            batchsize = int(n[1].content) - int(n[0].content) + 1
        else:
            length = batchsize = 0
        if next:
            return _parse(), next[0].content, batchsize, int(length)
        return _parse(), False, batchsize, int(length)
        
    @staticmethod
    def parse_html_expirable_bugpage(xmldoc, all_tasks, debug_url):
        def _parse():
            rows = xmldoc.xpathEval('//table[@class="listing" and @id="buglisting"]//tbody//tr')
            for row in rows:
                col_count = len(row.xpathEval("td"))
                parse_error( 4 < col_count < 7, "BugPage.parse_html_expirable_bugpage.col_count", xml=row, url=debug_url)
                m = row.xpathEval("td[1]/img")
                parse_error( m, "BugPage.parse_html_expirable_bugpage.importance", xml=row, url=debug_url)
                importance = m[0].prop("title").split()[0]
                m = row.xpathEval("td[2]")
                parse_error( m, "BugPage.parse_html_expirable_bugpage.bugnumber", xml=row, url=debug_url)
                bugnumber = int(m[0].content)
                m = row.xpathEval("td[3]/a")
                parse_error( m, "BugPage.parse_html_expirable_bugpage.url", xml=row, url=debug_url)
                url = m[0].prop("href")
                summary = m[0].content
                m = row.xpathEval("td[4]/img")
                private = False
                if m:
                    private = m[0].prop("alt").lower() == "private"
                if col_count == 6:
                    m = row.xpathEval("td[5]")
                    parse_error( m, "BugPage.parse_html_expirable_bugpage.package", xml=row, url=debug_url)
                    package = m[0].content
                    if package == '\xe2\x80\x94':
                        package = None
                    m = row.xpathEval("td[6]")
                    parse_error( m, "BugPage.parse_html_expirable_bugpage.date_last_update.1", xml=row, url=debug_url)
                    date_last_update = LPTime(m[0].content)
                elif col_count == 5:
                    package = None #this should be the package related to given url
                    m = row.xpathEval("td[5]")
                    parse_error( m, "BugPage.parse_html_expirable_bugpage.date_last_update.2", xml=row, url=debug_url)
                    date_last_update = LPTime(m[0].content)
                yield ExpBugInfo(bugnumber, url, importance, summary, private, package, date_last_update, all_tasks)
                    
        next = xmldoc.xpathEval('//td[@class="batch-navigation-links"]//a[@rel="next"]//@href')
        m = xmldoc.xpathEval('//td[@class="batch-navigation-index"]')
        if m:
            m = m.pop()
            n = re.search(r'(\d+)\s+results?', m.content)
            parse_error(n, "BugPage.parse_html_bugpage.length", url=debug_url)
            length = n.group(1)
            n = m.xpathEval("strong")
            batchsize = int(n[1].content) - int(n[0].content) + 1
        else:
            length = batchsize = 0
        if next:
            return _parse(), next[0].content, batchsize, int(length)
        return _parse(), False, batchsize, int(length)
        

class BugList(LPBugList):
    """
    returns a SET of LPBugInfo objects
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
        cmp_func = lambda x, y: sort(x, y, optsort.strip("-"))
        isreverse = optsort.startswith("-")
        return sorted(self, cmp=cmp_func, reverse=isreverse)
