import lpconstants as lpc
import utils

from lphelper import LateBindingProperty

class BlueprintInfo(object):
    def __init__(self, priority, spec, title, url, design, delivery, assignee, project, mentorship):
        self.__priority = lpc.BLUEPRINT.PRIORITY.get(priority, None)
        self.__spec = spec
        self.__title = title
        self.__url = url
        self.__status = lpc.BLUEPRINT.STATUS.get(design, None)
        self.__delivery = lpc.BLUEPRINT.DELIVERY.get(delivery, None)
        self.__assignee = assignee
        self.__project = project
        self.__mentorship = mentorship
        
    @property
    def url(self):
        return self.__url
        
    @property
    def spec(self):
        return self.__spec
    
    @property
    def title(self):
        return self.__title
        
    @property
    def priority(self):
        return self.__priority
        
    @property
    def status(self):
        return self.__status
    design = definition = status
        
    @property
    def delivery(self):
        return self.__delivery
    implementation = delivery
        
    @property
    def assignee(self):
        return self.__assignee
        
    @property
    def project(self):
        return self.__project
    series = product = project
    
    @property
    def mentorship(self):
        return self.__mentorship
        
    def __repr__(self):
        return "<BlueprintInfo %s>" %self.spec
    def __str__(self):
        return "[blueprint '%s' %s: %s]" %(self.spec, self.assignee or "", self.priority)
        
        
        
        
class LPBluePrint(object):
    def __init__(self, url, connection):
        self.__url = utils.valid_lp_url(url,utils.BLUEPRINT)
        self._connection = connection
        
    @property
    def url(self):
        return self.__url
        
    def __repr__(self):
        return "<BlueprintInfo %s>" %self.spec
    def __str__(self):
        return "[blueprint '%s' %s: %s]" %(self.spec, self.assignee or "", self.priority)
        
    def get_spec(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    spec = LateBindingProperty(get_spec, doc="returns short name of a blueprint") 

    def get_title(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    title = LateBindingProperty(get_title, doc="returns title of a blueprint")     
    
    def get_priority(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    priority = LateBindingProperty(get_priority, doc="returns priority of a blueprint")
    
    def get_status(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    status = LateBindingProperty(get_status, doc="returns status of a blueprint")
    design = definition = status     
    
    def get_delivery(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    delivery = LateBindingProperty(get_delivery, doc="returns state of implementation of a blueprint")
    implementation = delivery
    
    def get_assignee(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    assignee = LateBindingProperty(get_assignee, doc="returns assignee of a blueprint")
    
    def get_drafter(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    drafter = LateBindingProperty(get_drafter, doc="returns drafter of a blueprint")
    
    def get_approver(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    approver = LateBindingProperty(get_approver, doc="returns approver of a blueprint")
    
    def get_project(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    project = LateBindingProperty(get_project, doc="returns project a blueprint")
    product = project
         
    def get_mentors(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    mentorship = LateBindingProperty(get_mentors, doc="returns available mentors of a blueprint")
         
    def get_overview(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    overview = LateBindingProperty(get_overview, doc="returns overview of a blueprint")
         
    def get_full_spec(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    full_spec = LateBindingProperty(get_full_spec, doc="returns url to the full spec")
         
    def get_whiteboard(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    whiteboard = LateBindingProperty(get_whiteboard, doc="returns whiteboard of a blueprint")
         
    def get_sprints(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    sprints = LateBindingProperty(get_sprints, doc="returns sprints related to a blueprint")
         
    def get_subscribers(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    subscribers = LateBindingProperty(get_subscribers, doc="returns subscribers to a blueprint")
    
    def get_subscriptions_category(self, type):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
         
    def get_lifecycle(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    lifecycle = LateBindingProperty(get_lifecycle, doc="returns lifecycle info of a blueprint")
         
    def get_related_bugs(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    related_bugs = LateBindingProperty(get_related_bugs, doc="returns related bugs to a blueprint")
         
    def get_feedback_request(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    feedback_request = LateBindingProperty(get_feedback_request, doc="returns requested feedbacks")
        
        
        
        
        
        
