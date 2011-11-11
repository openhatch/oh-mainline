from lpconstants import CONNECTOR, _MODE_WRAPPER
from exceptions import LaunchpadError

#
# factory 
#

class LaunchpadConnector(object):
    def __init__(self, cls, method=CONNECTOR.MODES.DEFAULT):
        if isinstance(method, str):
            method = method.upper()
            try:
                method = getattr(CONNECTOR.MODES, method)
            except AttributeError:
                raise NotImplementedError, "Connection method '%s' not implemented" %method
        self.__method = method
        
        if not isinstance(self.method, _MODE_WRAPPER):
            raise ValueError
        
        try:            
            cls_id = CONNECTOR.CONNECTIONS[self.method][cls][0]
        except:
            raise ValueError        
        try:
            self.__module = __import__(cls_id, globals(), locals(), [], -1)
        except TypeError:
            self.__module = __import__(cls_id, globals(), locals(), [])
        self.__cls = getattr(self.module, cls)
        
        try:
            connection_id = CONNECTOR.CONNECTIONS[self.method][cls][1]
        except:
            ValueError
        try:
            mod_connection = __import__(connection_id[0], globals(), locals(), [], -1)
        except TypeError:
            mod_connection = __import__(connection_id[0], globals(), locals(), [])
        self.__connection = getattr(mod_connection, connection_id[1])()
        
    @property
    def connection(self):
        return self.__connection
    
    def set_connection_mode(self, mode):
        self.connection.set_mode(mode)
       
    def get_auth(self):
        return self.connection.get_auth()
        
    def set_auth(self, auth):
        self.connection.set_auth(auth)
    authentication = property(get_auth, set_auth)
        
    @property
    def cls(self):
        return self.__cls
        
    @property
    def method(self):
        return self.__method
        
    @property
    def module(self):
        return self.__module
        
    @property
    def needs_login(self):
        return self.connection.needs_login()
    
    #wrapper around old exception class
    class Error:
        LPUrlError = LaunchpadError
        

class ConnectBug(LaunchpadConnector):
    def __init__(self, method=CONNECTOR.MODES.DEFAULT):
        LaunchpadConnector.__init__(self, "Bug", method)
        
    def __call__(self, bug=None, url=None):
        return self.cls(bug, url, connection=self.connection)
    
    @property
    def content_types(self):
        return self.connection.content_types
    
    def NewAttachment(self, *args, **kwargs):
        """ returns a Attachment-class """
        if self.method == CONNECTOR.MODES.TEXT:
            raise NotImplementedError, "It is impossible to add attachments in the text-mode"
        return getattr(self.module, "Attachment")(connection=self.connection, *args, **kwargs)
    
    def NewComment(self, *args, **kwargs):
        """ returns a Comment-object """
        if self.method == CONNECTOR.MODES.TEXT:
            raise NotImplementedError, "It is impossible to add comments in the text-mode"
        return getattr(self.module, "Comment")(*args, **kwargs)
    
    def NewTask(self, task_type, *args, **kwargs):
        """ returns a Comment-object """
        if self.method == CONNECTOR.MODES.TEXT:
            raise NotImplementedError, "It is impossible to add a task in the text-mode"
        try:
            return getattr(self.module, "create_%s_task" %task_type.lower())(*args, **kwargs)
        except AttributeError:
            raise NotImplementedError, "creating of new '%s'-tasks is not implemented" %task_type
        
    def New(self, *args, **kwargs):
        """ returns a Bug-object """
        if self.method == CONNECTOR.MODES.TEXT:
            raise NotImplementedError, "It is impossible to create bugreports in the text-mode"
        return getattr(self.module, "create_new_bugreport")(connection=self.connection, *args, **kwargs)


class ConnectBugList(LaunchpadConnector):
    def __init__(self, method=CONNECTOR.MODES.DEFAULT, all_tasks=False):
        LaunchpadConnector.__init__(self, "BugList", method)
        self.__all_tasks = all_tasks
        self.__progress_hook = None
        
    def __call__(self, baseurl=None):
        return self.cls(baseurl, connection=self.connection,
                        all_tasks=self.__all_tasks,
                        progress_hook=self.__progress_hook)
    
    def set_progress_hook(self, progress_hook, blocksize=25):
        self.__progress_hook = self.cls._create_progress_hook(progress_hook, blocksize)
    
    
def ConnectTaskList(method=CONNECTOR.MODES.DEFAULT):
    return ConnectBugList(method, all_tasks=True)
    
    
class ConnectBlueprint(LaunchpadConnector):
    def __init__(self, method=CONNECTOR.MODES.DEFAULT):
        LaunchpadConnector.__init__(self, "Blueprint", method)
        
    def __call__(self, url):
        return self.cls(url, self.connection)
    

class ConnectBlueprintList(LaunchpadConnector):
    def __init__(self, method=CONNECTOR.MODES.DEFAULT):
        LaunchpadConnector.__init__(self, "BlueprintList", method)
        self.__progress_hook = None
        
    def __call__(self, baseurl=None):
        return self.cls(baseurl, connection=self.connection,
                        progress_hook=self.__progress_hook)

    def set_progress_hook(self, progress_hook, blocksize=25):
        self.__progress_hook = self.cls._create_progress_hook(progress_hook, blocksize)


class ConnectProjectList(LaunchpadConnector):
    def __init__(self,method=CONNECTOR.MODES.DEFAULT):
        LaunchpadConnector.__init__(self,"ProjectList",method)
        self.__progress_hook=None
        
    def __call__(self,baseurl=None):
        return self.cls(baseurl,connection=self.connection,all_tasks=False,progress_hook=self.__progress_hook)
    
    def set_progress_hook(self, progress_hook, blocksize=25):
        self.__progress_hook=self.cls._create_progress_hook(progress_hook,blocksize)

        
class ConnectProjectPackageList(LaunchpadConnector):
    def __init__(self,method=CONNECTOR.MODES.DEFAULT):
        LaunchpadConnector.__init__(self,"ProjectPackageList",method)
        self.__progress_hook=None
        
    def __call__(self,baseurl=None):
        return self.cls(baseurl,connection=self.connection,all_tasks=False,progress_hook=self.__progress_hook)
    
    def set_progress_hook(self,progress_hook,blocksize=25):
        self.__progress_hook=self.cls._create_progress_hook(progress_hook,blocksize)
