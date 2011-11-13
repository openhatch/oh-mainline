"""TODO:
 * move urlcheck to subclasses"""

import copy
import itertools

from exceptions import LaunchpadError


class LPBugPage(object):
    """ Base-class which represents one batch of bugs
    
    Each subclass must implement a staticmethod 'find_parse_function'
    which delegates the actual parsing.
    A LPBugPage-object is iterable and has aditional attributes
      - .parser: generator over elements of the page, this generator
          is also accesible directly via __iter__
      - .following_page: False or url of next batch
      - .batchsize: number of items on this bugpage
      - .length: overall size of the search result
    """
    @staticmethod
    def find_parse_function(connection, url, all_tasks):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    
    def __init__(self, url, connection, all_tasks=False):
        assert hasattr(connection, "get"), "Connection object needed"
        
        (self.parser, self.following_page,
         self.batchsize, self.length) = self.find_parse_function(connection, url, all_tasks)
        
    def __iter__(self):
        return self.parser
        
class _ProgressWrapper(object):
    """ helper-class to fake the behavoiur of the progress_hook for
    the connections object.
    """
    def __init__(self, hook, blocksize):
        self.counter = 0
        self.ticks = 0
        self.hook = hook
        self.blocksize = blocksize
        
    def reset(self):
        self.counter = 0
        self.ticks = 0
        
    def __call__(self, size, blocksize=None):
        self.counter += 1
        if not self.counter % self.blocksize or blocksize is None:
            self.ticks += 1
            self.hook(self.ticks, self.blocksize, size)

class LPBugList(set):
    """ set-like representation of a launchpad query
    
    TODO:
        * on-demand parsing -thekorn: DONE, we are using generators now, that should be enough
        * documentation
    """
    @staticmethod
    def _create_progress_hook(hook_func, blocksize=25):
        assert blocksize, "blocksize needs to be an integer greater than 0"
        assert callable(hook_func), "hook_func needs to be callable with three arguments"
        return _ProgressWrapper(hook_func, blocksize)
    
    def __new__(cls, *args, **kwargs):
        """ this is necessary to allow keyword-arguments in python2.4 """
        obj = set.__new__(cls)
        return obj
    
    def __init__(self, baseurl, connection=None, all_tasks=False,
                    helper_bugpage=None, progress_hook=None):
                        
        ##why?->
        self.__args = locals().copy()
        del self.__args["self"]
        ###<-
        assert connection, "Connection object needed"
        self.__connection = connection
        self.__all_tasks = all_tasks
        
        self.set_progress_hook(progress_hook)
        
        if hasattr(baseurl, "baseurl") and hasattr(baseurl, "functions"):
            self.baseurl = baseurl.baseurl
            self.__filter = baseurl.functions
        else:
            self.baseurl = baseurl
            self.__filter = set()
        
        self.class_helper_bugpage = helper_bugpage
            
        set.__init__(self)
        self._add(self.baseurl)
        
    def __repr__(self):
        return "<BugList %s>" %self.baseurl.split("?")[0]
        
    def __str__(self):
        return "BugList([%s])" %",".join(repr(i) for i in self)
        
    def __copy__(self):
        return self.__class__(**self.__args)    
        
    def copy(self):
        return copy.copy(self)
    
    def __iadd__(self, other):
        """ let l be an instance of BugList,
        l += BugList(<LP-URL>) will add bugs to l
        l.add(<LP-URL>) is still possible
        """
        for bug in other:
            self.add(bug)
        return self
    
    def sort(self, optsort):
        """ returns a LIST of bugs sorted by optsort """
        raise NotImplementedError
        
    def _fetch(self, url):
        """
        searches given bugpage for bugs and 'next'-page and returns both values
        
        if calling <url> returns an LaunchpadError, this error will be
        ignored if there are still bugs in the buglist, otherwise raised
        again
        """
        if self.class_helper_bugpage is None:
            raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        try:
            bugpage = self.class_helper_bugpage(url,
                connection=self.__connection, all_tasks=self.__all_tasks)
        except LaunchpadError:
            bugpage = None
            if not self:
                raise
        return bugpage    

    def _add(self, url, follow=True):
        """ adds bugs to the buglist """
        follow_page = True
        bugpage = None
        if not self.__progress_hook is None:
            # reset progress-hook incase there are more than one 
            # fetching actions for one LPBugList-object
            self.__progress_hook.reset()
        while(url and follow_page):
            bugpage = self._fetch(url)
            if bugpage is None:
                break
            if self.__filter:
                #has filter-funct
                b = self._stoppable_filter(bugpage)
            else:
                if self.__progress_hook is None:
                    b = bugpage
                else:
                    b = itertools.imap(lambda x: self.__progress_hook(bugpage.length, bugpage.batchsize) or x, bugpage)
            self += b
            url = bugpage.following_page
            follow_page = follow and bool(url)
        if bugpage is not None and self.__progress_hook is not None:
            self.__progress_hook(bugpage.length)
            
    def _stoppable_filter(self, bugpage):
        for bug in bugpage:
            if not self.__progress_hook is None:
                self.__progress_hook(bugpage.length, bugpage.batchsize)
            try:
                for func in self.__filter:
                    bug = func(bug)
                    if not bug:
                        break
                else:
                    yield bug
            except StopIteration:
                bugpage.following_page = False
                break
            
    def _get_class_helper_bugpage(self):
        if not self.__class_helper_bugpage:
            raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        return self.__class_helper_bugpage
        
    def _set_class_helper_bugpage(self, value):
        #if not (issubclass(value, LPBugPage) or value is None):
        if not (value is None or issubclass(value, LPBugPage)):
            raise TypeError, "BugList.class_helper_bugpage needs to be instance of LPBugPage"
        self.__class_helper_bugpage = value
    class_helper_bugpage = property(_get_class_helper_bugpage, _set_class_helper_bugpage)
            
    def get_bugs(self):
        # should be removed in the future, as self is now a set itself
        return self
    bugs = property(fget=get_bugs,doc="get list of bugs")
        
    def set_progress_hook(self, hook_func, blocksize=25):
        if hook_func is None:
            self.__progress_hook = None
        elif isinstance(hook_func, _ProgressWrapper):
            self.__progress_hook = hook_func
        else:
            self.__progress_hook = self._create_progress_hook(hook_func, blocksize)
