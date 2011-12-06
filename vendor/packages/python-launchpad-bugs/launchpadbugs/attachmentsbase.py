import os

import exceptions
import utils

from lphelper import change_obj, LateBindingProperty
from lpconstants import ATTACHMENTS


class LPAttachment(object):
    """ Returns an 'Attachment'-object
    
    * editable attributes:
        .description: any text
        .contenttype: any text
        .is_patch: True/False
        
    * read-only attributes:
        .id: hash(local_filename) for local files,
            launchpadlibrarian-id for files uploaded to launchpadlibrarian.net
        .is_down: True if a file is downloaded to ATTACHMENTS.ATTACHMENT_PATH
        .is_up: True if file is uploaded to launchpadlibrarian.net
        ...
    TODO: work on docstring
    """
    def __init__(self, connection, url=None, localfilename=None, localfileobject=None,
                    description=None, is_patch=None, contenttype=None, comment=None):
        if [localfilename, localfileobject].count(None) == 0:
            raise exceptions.PythonLaunchpadBugsValueError(msg="Attachment can not take localfilename and localfileobject")
        self.__connection = connection
        self.__description = description
        self.__is_patch = is_patch
        if self.__is_patch:
            self.__contenttype = "text/plain"
        else:
            self.__contenttype = contenttype
            
        self.__local_filename = localfilename
        self.__open_in_object = False
        if localfileobject:
            if isinstance(localfileobject, file):
                self.__local_fileobject = localfileobject
            else:
                raise TypeError, "Attachment: localfileobject needs to be a file-like object"
        else:
            if self.__local_filename:
                self.__local_fileobject = open(self.__local_filename, "r")
                self.__open_in_object = True
            else:
                self.__local_fileobject = None
                
        self.__url = url
        self.__text = None
        self.__download_location = None
        try:
            self.__comment = int(comment)
        except:
            self.__comment = None
        self.__cache = {"description": self.description,
            "is_patch": self.is_patch, "contenttype": self.contenttype}

    def __repr__(self):
        s = list()
        if self.is_up:
            s.append("(up: #%s)" %self.lp_id)
        if self.is_down:
            s.append("(down: %s)" %self.local_filename)
        return "<Attachment %s>" %", ".join(s)
        
    def __del__(self):
        if self.__open_in_object and self.__local_fileobject:
            self.__local_fileobject.close()
           
    @property
    def id(self):
        if self.is_up:
            return self.lp_id
        else:
            if self.__local_fileobject:
                return hash(self.__local_fileobject)
            elif self.local_filename:
                return hash(self.local_filename)
            raise ValueError, "unable to get hash of the given file"
        
    @property
    def is_down(self):
        """checks if
            * file is already in attachment cache => change .__local_filename to cache-location => returns True
            * file is in old cache location => move it to new location => change .__local_filename to cache-location => returns true
            * file is in any other location => return True
            * else return False
        """
        if self.__download_location:
            return True
        if self.is_up:
            filename_old = \
                os.path.expanduser(os.path.join(ATTACHMENTS.ATTACHMENT_PATH,
                    str(self.lp_id), self.lp_filename))
            cache_filename = \
                os.path.expanduser(os.path.join(ATTACHMENTS.ATTACHMENT_PATH,
                    self.sourcepackage, str(self.bugnumber),
                    str(self.lp_id), self.lp_filename))
            if os.path.exists(filename_old):
                os.renames(filename_old, cache_filename)
            if os.path.exists(cache_filename):
                self.__local_filename = cache_filename
                return True
        return bool(self.local_filename)
        
    @property
    def is_up(self):
        return bool(self.url)
        
    @property
    def url(self):
        return self.__url or ""
    
    @property
    def lp_id(self):
        if self.is_up:
            return self.url.split("/")[-2]
        
    @property
    def lp_filename(self):
        if self.is_up:
            return self.url.split("/")[-1]
        else:
            return ""
            
    def get_bugnumber(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    bugnumber = LateBindingProperty(get_bugnumber)
                    
    def get_sourcepackage(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    sourcepackage = LateBindingProperty(get_sourcepackage)
                    
            
    def get_edit_url(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
    edit_url = LateBindingProperty(get_edit_url)
            
    @property
    def local_filename(self):
        return self.__local_filename
        
    @property
    def local_fileobject(self):
        return self.__local_fileobject
            
    def get_contenttype(self):
        return self.__contenttype
        
    def set_contenttype(self, type):
        if not self.is_patch:
            self.__contenttype = type
    contenttype = property(get_contenttype, set_contenttype, doc="contenttype of an attachment")
    
    def get_description(self):
        return self.__description
        
    def set_description(self, text):
        self.__description = str(text)
    description = property(get_description, set_description, doc="description of an attachment")
    
    def get_ispatch(self):
        return self.__is_patch
        
    def set_ispatch(self, value):
        self.__is_patch = bool(value)
    is_patch = property(get_ispatch, set_ispatch, "type of an attachment")
        
    def get_changed(self):
        changed = set()
        for k in self.__cache:
            if self.__cache[k] != getattr(self, k):
                changed.add(k)
        return frozenset(changed)
    changed = property(get_changed, doc="get a list of changed attributes")
    
    
    @property
    def text(self):
        """get content of an attachment"""
        if not self.is_down:
            self.download()
        else:
            self.read_local()
        return self.__text
       
    def read_local(self):
        if self.is_down and self.__text == None:
            if not self.local_fileobject:
                self.__local_fileobject = open(self.local_filename, "r")
            self.__text = self.local_fileobject.read()
       
    def download(self, location=None):
        """ save attachment in ATTACHMENTS.ATTACHMENT_PATH if not already done """            
        if location is None:
            self.__local_filename = \
                os.path.expanduser(os.path.join(ATTACHMENTS.ATTACHMENT_PATH,
                    self.sourcepackage, str(self.bugnumber), str(self.lp_id), self.lp_filename))
        else:
            path = os.path.expanduser(location)
            self.__download_location = path
            self.__local_filename = path
                
        if self.is_up:
            try:
                attachment = self.__connection.get(self.url)
            except IOError, e:
                bugnumber = getattr(self, "bugnumber", "unknown")
                msg = "Error while downloading attachments #%s (bug=#%s)\n" %(self.lp_id, bugnumber)
                msg += "original error message: %s" %e
                raise exceptions.PythonLaunchpadBugsIOError(msg)
            self.__text = attachment.text
            self.contenttype = attachment.contenttype
            utils.lazy_makedir(os.path.dirname(self.local_filename))
            attachment_file = open(self.local_filename, "w")
            attachment_file.write(self.__text)
            attachment_file.close()
            
    @property
    def comment(self):
        return self.__comment
            
            
class LPAttachments(object):
    def __init__(self, comments=None, attachments=None, parsed=False):
        if comments is None:
            self.parsed = True
        else:
            self.parsed = parsed
            self.__comments = comments
        self.__added = set()
        self.__removed = set()
        self._current = attachments or list()
        self.__cache = self.__current[:]
        
    def _get_attachments(self):
        r = list()
        c = self.__comments
        x = [i.component for i in c.changed]
        for i in c:
            if i in x:
                self.__added = self.__added.union(i.attachments)
            else:
                r.extend(i.attachments)
        r.extend(self.__added)
        for i, a in enumerate(r[:]):
            if a.id in self.__removed:
                del r[i]
        return r        
        
    def _get_current(self):
        if not self.parsed:
            self.parse()
        return self.__current
        
    def _set_current(self, list):
        self.__current = list
    _current = property(_get_current, _set_current)
    
        
    def __getitem__(self, key):
        if isinstance(key, LPAttachment):
            key = key.id
        list_id = [a.id for a in self._current]
        if key in list_id:
            return self._current[list_id.index(key)]
        try:
            return self._current[key]
        except IndexError:
            list_id = [a.id for a in self.__removed]
            if key in list_id:
                raise ValueError, "This attachment has been removed"
        raise IndexError, "could not find '%s' in attachments ('%s')" %(key, self._url or "unknown url")
        
    def __str__(self):
        return str(self._current)
        
    def __repr__(self):
        return "<Attachmentlist>"
        
    def __iter__(self):
        for i in self._current:
            yield i
            
    def __len__(self):
        return len(self.__current)
            
    def filter(self, func):
        for a in self._current:
            if func(a):
                yield a
        
    def add(self, attachment):
        if isinstance(attachment, LPAttachment):
            self.__added.add(attachment)
            self._current.append(attachment)
        else:
            #TODO: raise TypeError
            raise IOError, "'attachment' must be an instance of 'Attachment'"
        
    def remove(self, key=None, func=None):
        arg = [i for i in (key,func) if i is None]
        assert len(arg) == 1, "exactly one argument needed"
        if func:
            key = list(self.filter(func))
        def _isiterable(x):
            try:
                i = iter(x)
                return not isinstance(x, str) or False
            except TypeError:
                return False
        if _isiterable(key):
            for i in key:
                self.remove(key=i)
            return True
        try:
            if hasattr(key, "id"):
                key = key.id
            x = self[key]
            self.__removed.add(x)
            try:
                self.__current.remove(x)
            except ValueError:
                raise RunTimeError, "this should not happen"
        except (TypeError, IndexError):
            raise TypeError, "unsupported type of 'key' in Attachment.remove()"
        
    def parse(self):
        r = True
        if self.parsed:
            return True
        if not self.__comments.parsed:
            r = self.__comments.parse()
        self.__cache = self._get_attachments()
        self._current = self.__cache[:]
        self.parsed = True
        return r
        
    @property
    def deleted(self):
        return frozenset(self.__removed)
    
    @property
    def added(self):
        return frozenset(self.__added)
    
    @property
    def changed(self):
        changed = []
        deleted = self.deleted
        added = self.added
        x = set()
        for i in self.__comments.changed:
            x = x.union(i.component.attachments)
        for i in deleted:
            changed.append(change_obj(i, action="deleted"))
        for i in added:
            if i in x:
                continue
            changed.append(change_obj(i, action="added"))
        for i in set(self.__cache) - added - deleted:
            if i.changed:
                changed.append(change_obj(i))
        return changed
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
        
