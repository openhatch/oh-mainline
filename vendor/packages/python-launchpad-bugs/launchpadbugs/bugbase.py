from utils import valid_lp_url, bugnumber_to_url
from lphelper import LateBindingProperty
from lpconstants import BASEURL

class LPBugInfo(object):
    def __init__(self, nr, url, status, importance, summary, package=None, all_tasks=False):
        assert nr, "'LPBugInfo' needs at least the bugnumber as an argument"
        self.__bugnumber = int(nr)
        self.__url = url
        self.__status = status
        self.__importance = importance
        self.__summary = summary
        self.__sourcepackage = package
        self.__all_tasks = all_tasks
       
    @property
    def bugnumber(self):
        return int(self.__bugnumber)
        
    @property
    def url(self):
        return self.__url or bugnumber_to_url(self.bugnumber)
        
    @property
    def status(self):
        return self.__status or "unknown"
        
    @property
    def importance(self):
        return self.__importance or "unknown"
        
    @property
    def summary(self):
        return self.__summary or "unknown"
        
    @property
    def sourcepackage(self):
        return self.__sourcepackage or ""
       
    def __int__(self):
        return self.bugnumber
    def __repr__(self):
        return "<BugInfo %s>" %self.bugnumber
    def __str__(self):
        return "[Bug %s %s: %s/%s]" %(self.bugnumber, self.sourcepackage, self.status, self.importance)
    def __hash__(self):
        if not self.__all_tasks:
            return self.bugnumber
        else:
            return super(LPBugInfo, self).__hash__()
    def __eq__(self, other):
        return hash(self) == hash(other)
        
        

class Bug(object):
    def __init__(self, bug=None, url=None, connection=None):
        assert len([i for i in (bug, url) if i]) == 1, "Bug needs one argument, either <bug> or <url>"
        assert connection, "Connection object needed"

        [self.__bugnumber, self.__url, self.__status, self.__importance,
            self.__sourcepackage, self.__summary] = [None]*6

        self.__connection = connection
        self.__saved_hash = None

        if bug:
            if isinstance(bug, str):
                bug = int(bug)
                
            if isinstance(bug, int):
                self.__bugnumber = bug
                self.__url = bugnumber_to_url(self.__bugnumber)
            elif isinstance(bug, LPBugInfo):
                self.__bugnumber = int(bug)
                self.__url = bug.url
                self.__status = bug.status
                self.__importance = bug.importance
                self.__sourcepackage = bug.sourcepackage
                self.__summary = bug.summary
                self.__saved_hash = hash(bug)
            else:
                assert None, "type of bugnumber must be INT or STRING or bugnumber must be an instance of BugInfo, %s" %bug
        elif url:
            #TODO: check for valid url
            self.__url = valid_lp_url(url, BASEURL.BUG)
            assert self.__url, "Invalid launchpad url %s" %url
            self.__bugnumber = int(self.__url.split("/")[-1])
            
    def __int__(self):
        return int(self.bugnumber)
        
    def __repr__(self):
        return "<Bug %s>" %self.bugnumber
        
    def __str__(self):
        return "[Bug %s %s: %s/%s]" %(self.bugnumber, self.sourcepackage or "", self.status, self.importance)
        
    def __hash__(self):
        if not self.__saved_hash is None:
            return self.__saved_hash
        else:
            return super(Bug, self).__hash__()
            
    def __eq__(self, other):
        return hash(self) == hash(other)

##############################################################################
# Abstract properties
##############################################################################
    ##################################
    # Read only
    # (url, bugnumber, reporter, date, activity log, duplicates)
    ##################################
            
    def get_url(self):
        return self.__url 
    url = property(get_url, doc="returns url of a bug report")
        
        
    def get_bugnumber(self):
        return self.__bugnumber
    bugnumber = property(get_bugnumber, doc="returns bugnumber of a bug report")
        
        
    def get_reporter(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    reporter = LateBindingProperty(get_reporter, doc="returns reporter of a bugreport")    
        
        
    def get_date(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_reported = date = LateBindingProperty(get_date, doc="returns date of a bugreport")    
        
        
    def get_text(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    text = LateBindingProperty(get_text, doc="returns raw text of a bugreport (.description & .comments.text)")
    
        
        
    def get_activity(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    activity = LateBindingProperty(get_activity, doc="parses the activity log")
        
        
    def get_duplicates(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    duplicates = LateBindingProperty(get_duplicates, doc="returns a set of duplicates")
        
        
    def get_description_raw(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    description_raw = LateBindingProperty(get_description_raw, doc="returns description in raw format")
        
    ##############################################
    # Edit via '+edit'
    # (title/summary, description, tags, nickname)
    ##############################################

    def get_title(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_title(self, title):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    summary = title = LateBindingProperty(get_title, set_title, doc="returns title of a bugreport")


    def get_description(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_description(self, description):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    description = LateBindingProperty(get_description, set_description, doc="description of a bugreport")


    def get_tags(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    tags = LateBindingProperty(get_tags, doc="tags of a bugreport")


    def get_nickname(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_nickname(self, nickname):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    nickname = LateBindingProperty(get_nickname, set_nickname, doc="nickname of a bugreport")
    
    #############################################################################
    # Edit via '+editstatus'
    # (read-only: infotable, info)
    # (project/package==target, status, importance,  milestone, assignee, [comment, mail])
    #############################################################################
    
    def get_infotable(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    infotable = LateBindingProperty(get_infotable, doc="returns the infotable of a bugreport")
    
    
    def get_info(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    info = LateBindingProperty(get_info, doc="returns the infotable of a bugreport")
    
    
    def get_target(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_target(self, target):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    target = LateBindingProperty(get_target, set_target, doc="returns target of a bugreport")
    
    
    def get_importance(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_importance(self, importance):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    importance = LateBindingProperty(get_importance, set_importance, doc="returns importance of a bugreport")
    
    
    def get_status(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_status(self, status):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    status = LateBindingProperty(get_status, set_status, doc="returns status of a bugreport")    
    
    
    def get_milestone(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_milestone(self, milestone):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    milestone = LateBindingProperty(get_milestone, set_milestone, doc="returns milestone of a bugreport")    
    
    
    def get_assignee(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_assignee(self, lplogin):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    assignee = LateBindingProperty(get_assignee, set_assignee, doc="returns assignee of a bugreport")
    
    
    def get_sourcepackage(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_sourcepackage(self, target):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    sourcepackage = LateBindingProperty(get_sourcepackage, set_sourcepackage, doc="sourcepackage of a bugreport")        
    
    
    def get_affects(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    affects = LateBindingProperty(get_affects, doc="affected product of a bugreport")   
    
    #########################################################################
    # Edit via '+dublicate'
    # (duplicate)
    #########################################################################
    
    def get_duplicates(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    duplicates = LateBindingProperty(get_duplicates, doc="returns duplicates of a bugreport")
        
    def get_duplicate(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_duplicate(self, bugnumber):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    duplicate_of = LateBindingProperty(get_duplicate, set_duplicate, doc="mark this bug as duplicate of another")
    
    #########################################################################
    # Edit via '+secrecy'
    # (duplicate)
    #########################################################################
    
    def get_security(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_security(self, value):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    security = LateBindingProperty(get_security, set_security, doc="returns security of a bugreport")
    
    def get_private(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_private(self, value):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    private = LateBindingProperty(get_private, set_private, doc="returns private of a bugreport")
    
        
    #########################################################################
    # subscriptions
    #########################################################################
    
    def get_subscriptions(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def set_subscriptions(self, lplogin):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'        
    subscribtions = subscriptions = subscribers = LateBindingProperty(get_subscriptions, set_subscriptions,
            doc="returns subscriptions to a bugreport")
    
    def get_subscriptions_category(self, type):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    def get_comments(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    comments = LateBindingProperty(get_comments, doc="returns a list of comments of a bugreport")
        
        
    def get_attachments(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    attachments = LateBindingProperty(get_attachments, doc="returns a list of attachments of a bugreport")
    
    
    #########################################################################
    # mentoring information
    #########################################################################
    
    def get_mentors(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    mentors = LateBindingProperty(get_mentors, doc="returns mentoring information")
    
    
    #########################################################################
    # date_* from /+text (needs implementation in html-mode)
    #########################################################################
    
    def get_date_updated(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_updated = LateBindingProperty(get_date_updated, doc="returns date when bugreport was updated")
    
    
    #########################################################################
    # attached branches
    #########################################################################
    
    
    def get_branches(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    branches = LateBindingProperty(get_branches, doc="returns list of attached bzr branches")
        

