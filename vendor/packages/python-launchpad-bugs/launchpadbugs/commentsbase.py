#UNDER DEVELOPMENT - CURRENTLY NOT WORKING
from lphelper import change_obj, user, LateBindingProperty
from attachmentsbase import LPAttachments, LPAttachment

import exceptions


class LPComment(object):
    def __init__(self, subject=None, text=None, attachment=None):
        self.subject = subject
        self.text = text
        self.__attachments = set()
        if attachment is None:
            attachment = set()
        if isinstance(attachment, LPAttachment):
            attachment = set((attachment,))
        if attachment:
            x = [a for a in attachment if not isinstance(a, LPAttachment)]
            if x:
                e = dict((k, "type is '%s'" %type(k)) for k in x)
                raise exceptions.PythonLaunchpadBugsValueError(values=e,
                        msg="Files attached to a Comment have to be instance of LPAttachment")
            self.__attachments = attachment
        self.__nr = id(self) #  set unique number since comment is not attached to comments
        self.__user = None
        self.__date = None
        
    def set_attr(self, **kwargs):
        self.__nr = kwargs.get("nr", self.__nr)
        self.__user = kwargs.get("user", self.__user)
        self.__date = kwargs.get("date", self.__date)
        
    def __repr__(self):
        if self.__nr and self.__user and self.__date:
            return "<Comment #%s by %s on %s>" %(self.__nr, self.__user, self.__date)
        else:
            return "<Comment 'unknown'>"
        
    @property
    def number(self):
        return self.__nr
    
    @property
    def user(self):
        return self.__user
    
    @property
    def date(self):
        '''TODO: return Date-object ??'''
        return self.__date
        
        
    def get_attachments(self):
        return self.__attachments
        
    def set_attachments(self, attachment):
        if isinstance(attachment, Attachment):
            assert not self.attachments, "Impossible to add more then one file to a comment"
            self.__attachments.add(attachment)
        else:
            raise TypeError, ""
    attachments = property(get_attachments, set_attachments, doc="attachment added to a comment")


class LPComments(list):
    
    def __init__(self, comments=None, url=None):
        self._cache = []
        self.__url = url
        self.parsed = False
        if comments is None:
            comments = list()
        if comments:
            x = [c for c in comments if not isinstance(c, LPComment)]
            if x:
                e = dict((k, "type is '%s'" %type(k)) for k in x)
                raise exceptions.PythonLaunchpadBugsValueError(values=e,
                        msg="All Comments have to be instance of LPComment")
        list.__init__(self, comments)
        
    def __repr__(self):
        #TODO: add bugnumber, parse from self.__url
        return "<Commentslist>"
        
    def __str__(self):
        x = (len(self) > 1 and "[%s]") or "%s"
        return x %",".join(str(i) for i in self)
        
    def new(self, *args, **kwargs):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
      
    def parse(self):
        pass
        
    def add(self, comment):
        if isinstance(comment, LPComment):
            self.append(comment)
        else:
            #TODO: raise TypeError
            raise IOError, "'comment' must be an instance of 'LPComment'"
    
    @property
    def changed(self):
        changed = []
        save = self[:]
        while True:
            if self._cache == save:
                return changed
            else:
                x = save.pop()
                changed.insert(0,change_obj(x, action="added"))
            
    def commit(self, force_changes=False, ignore_lp_errors=True):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'

