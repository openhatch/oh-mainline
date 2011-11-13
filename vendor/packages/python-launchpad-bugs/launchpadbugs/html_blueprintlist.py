import re
import libxml2
import urlparse
from exceptions import parse_error
from blueprintbase import BlueprintInfo, LPBluePrint
from buglistbase import LPBugList, LPBugPage
from lphelper import blueprint_sort, user, unicode_for_libxml2
from lpconstants import BASEURL
from utils import valid_lp_url

#deactivate error messages from the validation [libxml2.htmlParseDoc]
def noerr(ctx, str):
    pass

libxml2.registerErrorHandler(noerr, None)

class BPInfo(BlueprintInfo):
    def __init__(self, priority, spec, title, url, design, delivery, assignee, project, mentorship):
        url = valid_lp_url(url, BASEURL.BLUEPRINT)
        BlueprintInfo.__init__(self, priority, spec, title, url, design, delivery, assignee, project, mentorship)
        

class Project(object):
    def __init__(self, url, project):
        self.url = valid_lp_url(url, BASEURL.BLUEPRINT)
        self.project = project
    def __str__(self):
        return str(self.project)
        

class BlueprintPage(LPBugPage):
    """
    grab content of a single BluePrint-table    
    """
    @staticmethod
    def find_parse_function(connection, url, all_tasks):
        url = valid_lp_url(url, BASEURL.BLUEPRINTLIST)
        lp_content = connection.get(url)
        xmldoc = libxml2.htmlParseDoc(unicode_for_libxml2(lp_content.text), "UTF-8")
        u = urlparse.urlsplit(url)
        if "+milestone" in u[2]:
            result = BlueprintPage.parse_html_milestone_specs(xmldoc, all_tasks, url)
        else:
            result = BlueprintPage.parse_html_blueprintpage(xmldoc, all_tasks, url)
        return result
        
    @staticmethod
    def parse_html_blueprintpage(xmldoc, all_tasks, url):
        def _parse():
            if not xmldoc.xpathEval('//table[@id="speclisting"]'):
                xmldoc.freeDoc()
                return
                
            blueprinttable = xmldoc.xpathEval('//table[@id="speclisting"]//tbody//tr')
            for row in blueprinttable:
                m = row.xpathEval('td[1]//span[not(@class="sortkey")]')
                assert m
                priority = m[0].prop("class")
                
                m = row.xpathEval('td[2]//a')
                assert m
                url = m[0].prop("href")
                title = m[0].prop("title")
                spec = m[0].content
                
                mentorship = bool(row.xpathEval('td[2]//img[@alt="mentoring"]'))
                #add INFORMATIONAL
                
                m = row.xpathEval('td[3]//span[not(@class="sortkey")]')
                assert m
                status = m[0].prop("class")
                
                m = row.xpathEval('td[4]//span[not(@class="sortkey")]')
                assert m
                delivery = m[0].prop("class")
                
                m = row.xpathEval('td[5]//a')
                if m:
                    assignee = user.parse_html_user(m[0])
                else:
                    assignee = user(None)
                
                m = row.xpathEval('td[6]//a')
                # on personal blueprint pages this column does not exist
                if m:
                    project = Project(m[0].prop("href"), m[0].content)
                else:
                    project = None
                
                yield BPInfo(priority, spec, title, url, status, delivery, assignee, project, mentorship)

        next = xmldoc.xpathEval('//div[@class="lesser"]//a[@rel="next"]//@href')
        m = xmldoc.xpathEval('//td[@class="batch-navigation-index"]')
        if m:
            m = m.pop()
            n = re.search(r'(\d+)\s+results?', m.content)
            parse_error(n, "BugPage.parse_html_bugpage.length", url=url)
            length = n.group(1)
            n = m.xpathEval("strong")
            batchsize = int(n[1].content) - int(n[0].content) + 1
        else:
            length = batchsize = 0
        if next:
            return _parse(), next[0].content, batchsize, int(length)
        return _parse(), False, batchsize, int(length)
        
    
    @staticmethod
    def parse_html_milestone_specs(xmldoc, all_tasks, url):
        def _parse():
            if not xmldoc.xpathEval('//table[@id="milestone_specs"]'):
                xmldoc.freeDoc()
                return
                
            blueprinttable = xmldoc.xpathEval('//table[@id="milestone_specs"]//tbody//tr')
            for row in blueprinttable:
                m = row.xpathEval('td[1]//a')
                assert m
                url = m[0].prop("href")
                title = m[0].prop("title")
                spec = m[0].content
                
                m = row.xpathEval('td[2]//span[not(@class="sortkey")]')
                assert m
                priority = m[0].prop("class")
                
                # is the mentorship-icon used?
                mentorship = bool(row.xpathEval('td[2]//img[@alt="mentoring"]'))
                #add INFORMATIONAL
                
                m = row.xpathEval('td[3]/a')
                if m:
                    assignee = user.parse_html_user(m[0])
                else:
                    assignee = user(None)
                
                m = row.xpathEval('td[4]//span[not(@class="sortkey")]')
                assert m
                delivery = m[0].prop("class")
                
                yield BPInfo(priority, spec, title, url, None, delivery, assignee, None, mentorship)

        next = xmldoc.xpathEval('//a[@rel="next"]//@href')
        m = xmldoc.xpathEval('//h2[@id="specification-count"]')
        length = batchsize = int(m[0].content.split(" ")[0])
        assert not next, "milestone_specs are supposed to be single-paged, does it changed? url='%s'" %url
        return _parse(), False, batchsize, length
        

class BlueprintList(LPBugList):
    """
    returns a SET of LPBugInfo objects
    searches baseurl and its following pages
    """
    def __init__(self, baseurl, connection=None, all_tasks=False, progress_hook=None):
        if hasattr(baseurl, "baseurl"):
            baseurl.baseurl = valid_lp_url(baseurl.baseurl, BASEURL.BLUEPRINTLIST)
        else:
            baseurl = valid_lp_url(baseurl, BASEURL.BLUEPRINTLIST)
        LPBugList.__init__(self, baseurl, connection, all_tasks,
                    BlueprintPage, progress_hook)
        
    def __repr__(self):
        return "<BlueprintList %s>" %self.baseurl.split("?")[0]
        
    def __str__(self):
        return "BlueprintList([%s])" %",".join(repr(i) for i in self)
    
    def sort(self, optsort):
        """ returns a LIST of bugs sorted by optsort """
        return sorted(self, cmp=lambda x,y: blueprint_sort(x,y,optsort.strip("-")),
                        reverse=optsort.startswith("-"))
        
    def add(self, item):
        assert isinstance(item, (BlueprintInfo, LPBluePrint))
        LPBugList.add(self, item)
