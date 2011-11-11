import re
import libxml2

from blueprintbase import LPBluePrint
from lphelper import _gen_getter, user, unicode_for_libxml2
from lptime import LPTime
from bugbase import LPBugInfo
from subscribersbase import LPSubscribers

def _get_content(xml, path):
    x = xml.xpathEval(path)
    assert x
    res = x[0].content.strip("\n ")
    x = res.split("\n")
    if len(x) > 1:
        res = " ".join([i.strip() for i in x if i])
    return res
    
def _get_user(xml, path):
    m = xml.xpathEval(path)
    if m:
        return user.parse_html_user(m[0])
    else:
        m = xml.xpathEval("td")
        assert m
        assert "None" in m[0].content
        # in this case this attribute is set to 'None'
        return user(None)

class InfoBox(object):
    def __init__(self, xml):
        self.xmldoc = xml[0]
        self.parsed = False
        self.__priority = None
        self.__status = None
        self.__delivery = None
        self.__goal = None
        self.__assignee = user(None)
        self.__drafter = user(None)
        self.__approver = user(None)
        self.__sprints = set()
        
    def parse(self):
        if self.parsed:
            return True
        
        rows = self.xmldoc.xpathEval("tr")
        #count = len(rows)
        #print count
        
        for row in rows:
            if row.xpathEval('th[contains(.,"Priority")]'):
                assert not self.__priority
                self.__priority = _get_content(row, "td")
            elif row.xpathEval('th[contains(.,"Definition")]'):
                assert not self.__status
                self.__status = _get_content(row, "td")
            elif row.xpathEval('th[contains(.,"Implementation")]'):
                assert not self.__delivery
                self.__delivery = _get_content(row, "td")
            elif row.xpathEval('th[contains(.,"Series goal")]'):
                # currently not used
                assert not self.__goal
                self.__goal = _get_content(row, "td")
            elif row.xpathEval('th[contains(.,"Assignee")]'):
                assert not self.__assignee
                self.__assignee = _get_user(row, "td/a")
            elif row.xpathEval('th[contains(.,"Drafter")]'):
                assert not self.__drafter
                self.__drafter = _get_user(row, "td/a")
            elif row.xpathEval('th[contains(.,"Approver")]'):
                assert not self.__approver
                self.__approver = _get_user(row, "td/a")
            elif row.xpathEval('th[contains(.,"Sprints")]'):
                m = row.xpathEval("td//a")
                for i in m:
                    self.__sprints.add(i.content)
            else:
                assert None, "unknown attribute in InfoBox: %s" %row.xpathEval('th').content
        self.parsed = True
        
    @property
    def priority(self):
        return self.__priority
        
    @property
    def status(self):
        return self.__status
        
    @property
    def delivery(self):
        return self.__delivery
        
    @property
    def assignee(self):
        return self.__assignee
        
    @property
    def drafter(self):
        return self.__drafter
        
    @property
    def approver(self):
        return self.__approver
        
    @property
    def sprints(self):
        return self.__sprints
    

class Subscribers(LPSubscribers):
    def __init__(self, xml):
        self.parsed = False
        self.xmldoc = xml
        LPSubscribers.__init__(self, ("essential", "inessential"))
        
    def parse(self):
        if self.parsed:
            return True
            
        for i in self.xmldoc:
            m = i.xpathEval("a")
            assert m
            x = user.parse_html_user(m[0])
            
            m = i.xpathEval("img")
            assert m
            if "inessential" in m[0].prop("src"):
                self["inessential"].add(x)
            elif "essential" in m[0].prop("src"):
                self["essential"].add(x)
            else:
                assert None, "unsupported type"
            
        self.parsed = True
        
    def add(self):
        raise NotImplementedError, 'read-only'
        
        
class Lifecycle(object):
    def __init__(self, xml):
        self.xmldoc = xml[0]
        self.parsed = False
        
        self.registrant = user(None)
        self.date_registered = None
        
        self.starter = user(None)
        self.date_started = None
        
        self.completer = user(None)
        self.date_completed = None
        
        
        
    def parse(self):
        if self.parsed:
            return True
            
        rows = self.xmldoc.xpathEval("tr")
        #count = len(rows)
        #print count
        
        for row in rows:
            if row.xpathEval('th[contains(.,"Registered by")]'):
                assert not self.registrant
                self.registrant = _get_user(row, "td/a")
            elif row.xpathEval('th[contains(.,"When")]'):
                assert not self.date_registered
                x = _get_content(row, "td/span/@title")
                self.date_registered = LPTime(x)
            elif row.xpathEval('th[contains(.,"Started")]'):
                assert not self.date_started
                x = _get_content(row, "td")
                self.date_started = LPTime(x)
            elif row.xpathEval('th[contains(.,"Completed")]'):
                assert not self.date_completed
                x = _get_content(row, "td")
                self.date_completed = LPTime(x)
            elif row.xpathEval('th[contains(.,"by")]'):
                #print row.xpathEval('th')[0].content
                i = row.xpathEval('preceding-sibling::tr/th')
                assert i
                if "started" in i[-1].content.lower():
                    #print "Started by"
                    assert not self.starter
                    self.starter = _get_user(row, "td/a")
                elif "completed" in i[-1].content.lower():
                    #print "completed by"
                    assert not self.completer
                    self.completer = _get_user(row, "td/a")                  
                else:
                    assert None, "wrong xpath"
            else:
                assert None, "unknown attribute in InfoBox: %s" %row.xpathEval('th').content
        
        self.parsed = True


class BugInfo(LPBugInfo):
    def __init__(self, nr, url, summary):
        LPBugInfo.__init__(self, nr, url, None, None, summary, None, False)
        
    def __str__(self):
        return "[Bug %s]" %self.url
    

class RelatedBugs(set):
    def __init__(self, xml):
        self.xmldoc = xml
        self.parsed = False
        set.__init__(self)
        
    def parse(self):
        if self.parsed:
            return True
            
        for i in self.xmldoc:
            m = i.xpathEval("a")
            assert m
            u = m[0].prop("href")
            nr = int(u.split("/").pop())
            s = m[0].content.split(":").pop()
            summary = s.strip("\n ")
            self.add(BugInfo(nr, u, summary))
            
        self.parsed = True
        

class Overview(object):
    def __init__(self, xml):
        self.xmldoc = xml
        self.parsed = False
        
    def parse(self):
        if self.parsed:
            return True
            
        assert self.xmldoc
        self.text = self.xmldoc[0].content
        self.parsed = True
        

class FullSpec(object):
    def __init__(self, xml):
        self.xmldoc = xml
        self.parsed = False
        
    def parse(self):
        if self.parsed:
            return True
            
        assert self.xmldoc
        self.url = self.xmldoc[0].prop("href")
        self.parsed = True    


class Mentors(set):
    def __init__(self, xml):
        self.xmldoc = xml
        self.parsed = False
        set.__init__(self)
        
    def parse(self):
        if self.parsed:
            return True
            
        for i in self.xmldoc:
            x = user.parse_html_user(i)
            self.add(x)
            
        self.parsed = True
        

class WhiteBoard(object):
    def __init__(self, xml):
        self.xmldoc = xml
        self.parsed = False
        self.text = ""
        
    def parse(self):
        if self.parsed:
            return True
            
        if self.xmldoc:
            self.text = self.xmldoc[0].content
        self.parsed = True
        
class _Request(object):
    def __init__(self, user, target, text):
        self.user = user
        self.target = target
        self.text = text
        
    def __repr__(self):
        return "<FeedbackRequest from '%s' to '%s'>" %(self.user, self.target)


class FeedbackRequest(list):
    def __init__(self, xml):
        self.xmldoc = xml
        self.parsed = False
        list.__init__(self)
        
    def parse(self):
        if self.parsed:
            return True
            
        for i in self.xmldoc:
            m = i.xpathEval("a")
            assert m
            r_user = user.parse_html_user(m[0])
            
            m = i.xpathEval("strong/a")
            assert m
            r_target = user.parse_html_user(m[0])
            
            m = i.xpathEval('div[@style="font-style: italic;"]')
            assert m
            r_text = m[0].content
            
            self.append(_Request(r_user,r_target,r_text))
            
        self.parsed = True
        
        

class Blueprint(LPBluePrint):
    def __init__(self, url, connection):
        LPBluePrint.__init__(self, url, connection)
        
        page = self._connection.get(self.url)
        #TODO: check redirection
        
        self.xmldoc = libxml2.htmlParseDoc(unicode_for_libxml2(page.text), "UTF-8")
        
        self.__info_box = InfoBox(self.xmldoc.xpathEval('//table[@class="summary"]/tbody'))
        self.__subscribers = Subscribers(self.xmldoc.xpathEval('//div[@id="portlet-subscribers"]/div[@class="portletBody"]//div'))
        self.__lifecycle = Lifecycle(self.xmldoc.xpathEval('//div[@id="portlet-lifecycle"]/div/table/tbody'))
        self.__related_bugs = RelatedBugs(self.xmldoc.xpathEval('//div[@id="portlet-related-bugs"]/div/ul//li'))
        self.__overview = Overview(self.xmldoc.xpathEval('//table[@class="summary"]/following-sibling::p[1]'))
        self.__full_spec = FullSpec(self.xmldoc.xpathEval('//table[@class="summary"]/following-sibling::ul[1]/li/a'))
        self.__mentors = Mentors(self.xmldoc.xpathEval('//table[@class="summary"]/following-sibling::p[2]//a'))
        self.__whiteboard = WhiteBoard(self.xmldoc.xpathEval('//h2[contains(.,"Whiteboard")]/following-sibling::div'))
        self.__feedback_request = FeedbackRequest(self.xmldoc.xpathEval('//div[@id="portlet-feedback"]/div/ul//li'))
        
        
    #######INFO-BOX
    get_priority = _gen_getter("__info_box.priority")
    get_status = _gen_getter("__info_box.status")
    get_delivery = _gen_getter("__info_box.delivery")
    get_assignee = _gen_getter("__info_box.assignee")
    get_drafter = _gen_getter("__info_box.drafter")
    get_approver = _gen_getter("__info_box.approver")
    get_sprints = _gen_getter("__info_box.sprints")
    ##########


    #####subscribers
    get_subscribers = _gen_getter("__subscribers")
    def get_subscriptions_category(self, type):
        return self.__subscribers.get_subscriptions(type)
    #####
    
    get_lifecycle = _gen_getter("__lifecycle")
    
    get_related_bugs = _gen_getter("__related_bugs")

    get_overview = _gen_getter("__overview.text")
    
    get_full_spec = _gen_getter("__full_spec.url")
    
    get_mentors = _gen_getter("__mentors")
    
    get_whiteboard = _gen_getter("__whiteboard.text")
    
    get_feedback_request = _gen_getter("__feedback_request")
    
    def get_title(self):
        x = self.xmldoc.xpathEval('//div[@class="main"]')
        assert x
        return x[0].content
        
    def get_spec(self):
        return self.url.split("/").pop()
        
    def get_project(self):
        x = self.xmldoc.xpathEval('//div[@class="intro"]')
        assert x
        return x[0].content.split("Blueprint for").pop().strip()
