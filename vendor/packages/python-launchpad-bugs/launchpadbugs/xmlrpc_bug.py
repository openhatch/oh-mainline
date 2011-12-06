from bugbase import Bug as BugBase

class XMLRPC_Con(object):
    def __init__(self):
        pass

class Bug(BugBase):

    def __init__(self, bug=None, url=None, connection=None):
            
        BugBase.__init__(self, bug, url, connection=XMLRPC_Con())

    def get_importance(self):
        return "test importance"
        
    def get_attachments(self):
        return "This would return a list of attachments generated via XMLRPC"
