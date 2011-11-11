
from lphelper import change_obj, product, user, LateBindingProperty
import re
import urlparse


class LPTask(object):
    """ The 'LPTask'-object represents on task of a bugreport
    
    * editable attributes:
        .sourcepackage: lp-name of a package/project
        .status: valid lp-status
        .importance: valid lp-importance (if the user is not permitted to
            change 'importance' an 'IOError' will be raised
        .assignee: lp-login of an user/group
        .milestone: value must be in '.valid_milestones'
        
    * read-only attributes:
        .affects, .target, .valid_milestones
        
    TODO: * rename 'Info' into 'Task'
    
    Arguments
        affects (h,t,rw)
        status (h,t,rw)
        importance (h,t,rw)
        assignee (h,t,rw)
        current
        editurl
        type
        milestone
        available_milestone
        lock_importance
        targeted_to
        remote
        editlock
        edit_fields
        connection
        
    Attributes:
        sourcepackage
        status
        importance
        assignee
        milestone
        targeted_to
        remote
        affects
        target
        valid_milestones
        component
    
    """
    def __init__(self, value_dict={}):
    
                #(self, affects, status, importance, assignee, current,
                    #editurl, type, milestone, available_milestone,
                    #lock_importance, targeted_to, remote, editlock,
                    #edit_fields, connection):
        self._connection = value_dict.get("connection", None)
        self._editlock = value_dict.get("editlock", True)
        self._edit_fields = value_dict.get("edit_fields", set())
        self._lock_importance = value_dict.get("lock_importance", False)
        self._target = None
        self._affects = value_dict.get("affects", product(None))
        temp = self._affects.split(" ")
        #FIXME: does not work .sourcepackage is not None, maybe needs .lower()
        if temp[0] == "Ubuntu":
            self._sourcepackage = None
        else:
            self._sourcepackage = temp[0]
        r = re.match(r'^.*\((.*)\)$', self._affects.longname)
        if r:
            self._target = r.group(1).lower()
        self._status = value_dict.get("status", None)
        self._importance = value_dict.get("importance", None)
        self._assignee = value_dict.get("assignee", user(None))
        self._current = value_dict.get("current", None)
        self._editurl = value_dict.get("editurl", None)
        self._type = value_dict.get("type", None)
        self._milestone = value_dict.get("milestone", None)
        self._available_milestone = value_dict.get("available_milestone", {})
        self._targeted_to = value_dict.get("targeted_to", None)
        self._remote = value_dict.get("remote", None)
        
        #"date-created", "date-confirmed", "date-assigned", "date-inprogress", "date-closed"
        self._date_created = value_dict.get("date-created", None)
        self._date_confirmed = value_dict.get("date-confirmed", None)
        self._date_assigned = value_dict.get("date-assigned", None)
        self._date_inprogress = value_dict.get("date-inprogress", None)
        self._date_closed = value_dict.get("date-closed", None)
        self._date_left_new = value_dict.get("date-left-new", None)
        self._date_incomplete = value_dict.get("date-incomplete", None)
        self._date_triaged = value_dict.get("date-triaged", None)
        self._date_fix_committed = value_dict.get("date-fix-committed", None)
        self._date_fix_released = value_dict.get("date-fix-released", None)
        
        #user==reporter
        self._user = value_dict.get("reporter", user(None))
        
        #"component"
        self._component = value_dict.get("component", None)

        self._cache = {}        
    
    def __str__(self):
        targeted_to = (self._targeted_to and " (%s)" %self._targeted_to) or ""
        remote = (self._remote and " (remote)") or ""
        return "[%s%s%s: %s/%s]" % (self.affects.longname or self.affects,
                    targeted_to, remote, self.status, self.importance)
        
    def __repr__(self):
        targeted_to = (self._targeted_to and " (%s)" %self._targeted_to) or ""
        remote = (self._remote and " (remote)") or ""
        try:
            number = (not self._editlock and self._editurl.split("/")[-2]) or self._editurl.split("/")[-1]
        except AttributeError:
            number = "unknown"
        return "<Info of '%s%s%s (#%s)'>" %(self.affects.longname or self.affects,
                    targeted_to, remote, number)
            
    def is_current(self, current_task_tupel):
        if current_task_tupel == (self.target, self.targeted_to, self.sourcepackage):
            return True
        return False
        
                    
    def get_date_created(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_created = LateBindingProperty(get_date_created)
    
    def get_date_confirmed(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_confirmed = LateBindingProperty(get_date_confirmed)
    
    def get_date_assigned(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_assigned = LateBindingProperty(get_date_assigned)
    
    def get_date_inprogress(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_inprogress = LateBindingProperty(get_date_inprogress)
    
    def get_date_closed(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_closed = LateBindingProperty(get_date_closed)
    
    def get_date_left_new(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_left_new = LateBindingProperty(get_date_left_new)
    
    def get_date_incomplete(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_incomplete = LateBindingProperty(get_date_incomplete)

    def get_date_triaged(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_triaged = LateBindingProperty(get_date_triaged)

    def get_date_fix_committed(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_fix_committed = LateBindingProperty(get_date_fix_committed)

    def get_date_fix_released(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    date_fix_released = LateBindingProperty(get_date_fix_released)
    
    def get_user(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    user = LateBindingProperty(get_user)

    def get_component(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    component = LateBindingProperty(get_component)
                     
    def get_targeted_to(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._targeted_to
    targeted_to = LateBindingProperty(get_targeted_to)
        
    def get_remote(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._remote
    remote = LateBindingProperty(get_remote)
                     
    def get_affects(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._affects
    affects = LateBindingProperty(get_affects)
        
    def get_target(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._target
    target = LateBindingProperty(get_target)
        
    def get_sourcepackage(self):
        return self._sourcepackage
        
    def set_sourcepackage(self, package):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    sourcepackage = LateBindingProperty(get_sourcepackage, set_sourcepackage, doc="sourcepackage of a bug")

    def get_assignee(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._assignee
        
    def set_assignee(self, lplogin):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    assignee = LateBindingProperty(get_assignee, set_assignee, doc="assignee to a bugreport")
    
    def get_status(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._status
        
    def set_status(self, status):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    status = LateBindingProperty(get_status, set_status, doc="status of a bugreport")
                              
        
    def get_importance(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._importance
        
    def set_importance(self, importance):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    importance = LateBindingProperty(get_importance, set_importance, doc="importance of a bugreport")
    
    def get_valid_milestones(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._available_milestone
    valid_milestones = LateBindingProperty(get_valid_milestones)    
        
    def get_milestone(self):
        #raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self._milestone
        
    def set_milestone(self, milestone):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    milestone = LateBindingProperty(get_milestone, set_milestone, doc="milestone of a bugreport")
    
        
    def get_changed(self):
        changed = set()
        for k in self._cache:
            if self._cache[k] != getattr(self, k):
                changed.add(k)
        return frozenset(changed)
    changed = property(get_changed, doc="get a list of changed attributes")
    
    def commit(self, force_changes=False, ignore_lp_errors=True):
        """ Commits the local changes to launchpad.net
        
        * force_changes: general argument, has not effect in this case
        * ignore_lp_errors: if the user tries to commit invalid data to launchpad,
            launchpad returns an error-page. If 'ignore_lp_errors=False' Info.commit()
            will raise an 'ValueError' in this case, otherwise ignore this
            and leave the bugreport in launchpad unchanged (default=True)
        """
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'



class LPTasks(list):
    """ The 'LPTasks'-object represents the tasks related to a bugreport
        
    * read-only attributes:
        .current: returns the highlighted Info-object of the bugreport
    
    TODO:  * rename 'InfoTable' into 'TaskTable'
           * allow adding of tasks (Also affects upstream/Also affects distribution)
           * does current/tracked work as expected?
           * remote: parse editable values
    """
    def __init__(self, conf_data={}):
        self._current = None 
        self.parsed = False
        self._url = conf_data.get("url","")
        self._xml = conf_data.get("xml","")
        self._connection = conf_data.get("connection",None)
        self.__added = []
        list.__init__(self)
        
    def __repr__(self):
        return "<InfoTable>"
        
    def __str__(self):
        x = (len(self) > 1 and "[%s]") or "%s"
        return x %",".join(str(i) for i in self)
        
    def addTask(self, task):
        if not isinstance(task, LPTask):
            raise TypeError, "task has to be instance of 'LPTask'"
        self.__added.append(task)
        self.append(task)
        
    def remove(self, item):
        if not item in self.__added:
            raise RuntimeError, "LP does not allow to remove Tasks"
        list.remove(self, item)

    def parse(self):
        pass
        
    re_url = re.compile(r"^(/([a-z0-9-]+)/([a-z0-9-]+)?/?\+source)?/([a-z0-9-]+)/\+bug/.*$")
        
    @staticmethod
    def current_from_url(url):
        """ returns (<distibution>,<release>,<product>) or False """
        x = LPTasks.re_url.search(urlparse.urlsplit(url)[2])
        if x:
            return x.groups()[1:]
        else:
            return False
            
    re_listurl = re.compile(r"^(/([a-z0-9\-\.]+)/([a-z0-9\-\.]+)?/?\+source)?/([a-z0-9\-\.]+)/?(\+bugs)?$")
        
    @staticmethod
    def current_from_listurl(url):
        """ returns (<distibution>,<release>,<product>) or False """
        x = LPTasks.re_listurl.search(urlparse.urlsplit(url)[2])
        if x:
            return x.groups()[1:-1]
        else:
            return False      
        
    def get_current(self):
        if self._current == None:
            raise AttributeError, "There is no row of the info-table linked to this bugreport (%s)" %self._url
        assert isinstance(self._current, int), "No task related to %s?" %self._url
        return self[self._current]
    current = property(get_current, doc= "get the info-object for the current bug")
    
    def has_target(self, target):
        if not target:
            return None in [i.target for i in self]
        target = target.lower()
        for i in self:
            if i.target:
                if i.target.lower() == target:
                    return True
        return False
        
    @property
    def changed(self):
        ret = list()
        for i in self:
            if i in self.__added:
                ret.append(change_obj(i, "added"))
            elif i.changed:
                ret.append(change_obj(i))
        return ret
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        """ delegates commit() to each changed element """
        for i in self.changed:
            if i.action == "added":
                self._LP_create_task(i, force_changes, ignore_lp_errors)
            else:
                i.component.commit(force_changes, ignore_lp_errors)
                
    def _LP_create_task(task, force_changes, ignore_lp_errors):
        raise NotImplementedError
            

#some test-cases
if __name__ == '__main__':
    for i in (  "https://launchpad.net/bugs/12345",
                "https://bugs.edge.launchpad.net/bughelper/+bug/152499",
                "https://bugs.edge.launchpad.net/ubuntu/+source/bughelper/+bug/107735",
                "https://bugs.edge.launchpad.net/ubuntu/feisty/+source/bughelper/+bug/109213",
                "https://bugs.edge.launchpad.net/ubuntu/+source/python-launchpad-bugs/+bug/153842"):
        print i, "\t\t", LPTasks.current_from_url(i)
