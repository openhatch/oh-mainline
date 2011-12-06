"""
TODO:
 * check .private/.security: this seems to be wrong/maybe it  does not work
 * remove these ugly dict-element vs. object-attribute things
"""

from bugbase import Bug as BugBase
import email
import cStringIO as StringIO
import re
import ConfigParser

from lptime import LPTime
from lphelper import user, product
from tasksbase import LPTasks, LPTask
from attachmentsbase import LPAttachments, LPAttachment
from commentsbase import LPComments, LPComment
        
class Task(LPTask):
    def __init__(self, task_dict):
                
        #print task_dict
        task_dict["affects"], task_dict["targeted_to"] = product.parse_text_product(task_dict["task"])
        for i in ("reporter", "assignee"):
            task_dict[i] = user.parse_text_user(task_dict[i])
        for i in ("date-created", "date-confirmed", "date-assigned",
                  "date-inprogress", "date-closed", "date-left-new",
                  "date-incomplete", "date-triaged", "date-fix-committed",
                  "date-fix-released"):
            if task_dict.has_key(i):
                task_dict[i] = LPTime(task_dict[i])
            else:
                task_dict[i] = None
        task_dict["remote"] = task_dict.get("watch", None)
        #print task_dict
        LPTask.__init__(self, task_dict)
                    
    def get_date_created(self):
        return self._date_created
    
    def get_date_confirmed(self):
        return self._date_confirmed
    
    def get_date_assigned(self):
        return self._date_assigned
    
    def get_date_inprogress(self):
        return self._date_inprogress
    
    def get_date_closed(self):
        return self._date_closed
        
    def get_date_left_new(self):
        return self._date_left_new
        
    def get_date_incomplete(self):
        return self._date_incomplete

    def get_date_triaged(self):
        return self._date_triaged

    def get_date_fix_committed(self):
        return self._date_fix_committed

    def get_date_fix_released(self):
        return self._date_fix_released
    
    def get_user(self):
        return self._user

    def get_component(self):
        return self._component
        
        
class BugReport(object): 
    def __init__(self, bug_dict, connection=None):
        self.__data = bug_dict
        for i in ("tags", "duplicates"):
            self.__data[i] = self.__data[i].split()
        self.__data["bugnumber"] = int(bug_dict["bug"])
        del self.__data["bug"]
        self.__data["reporter"] = user.parse_text_user(self.__data["reporter"])
        self.__data["subscribers"] = [user.parse_text_user(u) for u in self.__data["subscribers"].split("\n") if u]
        
        self.__data["description"] = ""
        for i in ("date-reported", "date-updated"):
            self.__data[i] = LPTime(self.__data[i])
        a = list()
        for i in [i for i in self.__data["attachments"].split("\n") if i]:
            try:
                url, contenttype = i.split(" ", 1)
            except ValueError:
                if not i.startswith("http://"):
                    continue
                else:
                    raise
            contenttype = contenttype.split(";")[0]
            a.append(Attachment(url, contenttype, connection, self.__data["bugnumber"]))
        self.__data["attachments"] = Attachments(a)
        
    def _add_description(self, description):
        self.__data["description"] = description
        
    def __getattr__(self, name):
        try:
            return self.__data[name.replace("_", "-")]
        except KeyError:
            if name in ["bugnumber", "title", "reporter", "duplicate_of", "duplicates", "subscribers",
                        "assignee", "private", "security", "tags", "date_reported", "date_updated",
                        "description", "attachments"]:
                return None
            else:
                raise AttributeError
        
class Comments(LPComments):
    def __init__(self):
        LPComments.__init__(self)
        
class Comment(LPComment):
    
    def __init__(self, nr, author, date, comment):
        LPComment.__init__(self,text=comment)
        self.set_attr(nr=nr, user=user.parse_text_user(author[0]), date=LPTime(date[0]))


class Attachments(LPAttachments):
    def __init__(self, a_set):
        LPAttachments.__init__(self, attachments=a_set, parsed=True)
        
    def add(self, attachment):
        raise NotImplementedError, "It is impossible to add attachments in the text-mode"
        
    def remove(self, key=None, func=None):
        raise NotImplementedError, "It is impossible to remove attachments in the text-mode"

class Attachment(LPAttachment):
    def __init__(self, url, contenttype, connection, bugnumber=None):
        LPAttachment.__init__(self, connection, url=url, contenttype=contenttype)
        self.__bugnumber = bugnumber
                    
    def get_sourcepackage(self):
        if self.is_up:
            return "unknown_sourcepackage"
            
    def get_bugnumber(self):
        if self.is_up:
            return self.__bugnumber
        
        

class TextPage(object):
    def __init__(self, url, connection):
        self.parsed = False
        self.__url = url + "/+text"
        self.__connection = connection
        self.__data = {}
        
    def __getitem__(self, key):
        if not self.parsed:
            self.parse()
        return self.__data.get(key, [])
        
    def parse(self):
        text = self.__connection.get(self.__url).text
        parts = text.split("\n\n")
        tmp_task = LPTasks({"url": self.__url})
        self.__data["comments"] = Comments()
        current_task_tupel = LPTasks.current_from_url(self.__url)
        while parts:
            #~ print "LEN", len(parts)
            if parts[0].startswith("bug:"):
                x = parts.pop(0)
                x = "[bug]\n" + x
                #~ print "BUG"
                data = ConfigParser.ConfigParser()
                data.readfp(StringIO.StringIO(x))
                self.__data["bug"] = BugReport(dict(data.items("bug")), connection=self.__connection)
            elif parts[0].startswith("task:"):
                x = parts.pop(0)
                x = "[task]\n" + x
                #~ print "TASK"
                data = ConfigParser.ConfigParser()
                data.readfp(StringIO.StringIO(x))
                task_obj = Task(dict(data.items("task")))
                if task_obj.is_current(current_task_tupel):
                    tmp_task._current = len(tmp_task)
                tmp_task.append(task_obj)
                continue
            elif parts[0].startswith("Content-Type:"):
                l = "\n\n".join(parts)
                comments_msg = email.message_from_string(l)
                messages = comments_msg.get_payload()
                description = messages.pop(0)
                self.__data["bug"]._add_description(description.get_payload(decode=True))
                for i, msg in enumerate(messages):
                    self.__data["comments"].append(Comment(i+1, msg.get_all("Author"), msg.get_all("Date"), msg.get_payload(decode=True)))
                parts = False
                continue
            else:
                raise RuntimeError
        if tmp_task._current is None and len(tmp_task) == 1:
            # "only one task, this must be current"
            tmp_task._current = 0
        self.__data["task"] = tmp_task
        self.parsed = True
                    


class Bug(BugBase):
    def __init__(self, bug=None, url=None, connection=None):
            
        BugBase.__init__(self, bug, url, connection)
        self.__textpage = TextPage(self.url, self.__connection)
        
    def get_url(self):
        return self.url
    
    def get_bugnumber(self):
        assert self.bugnumber == self.__textpage["bug"].bugnumber[0]
        return self.__textpage["bug"].bugnumber[0]
        
    def get_reporter(self):
        return self.__textpage["bug"].reporter
        
    def get_title(self):
        return self.__textpage["bug"].title
        
    def get_subscriptions(self):
        return set(self.__textpage["bug"].subscribers)
        
    def get_duplicate(self):
        try: return self.__textpage["bug"].duplicate_of[0]
        except: return None
        
    def get_duplicates(self):
        # the 'or []'-statement ensures that this always returns a list and not 'None'
        return set(self.__textpage["bug"].duplicates or [])
        
    def get_infotable(self):
        return self.__textpage["task"]
        
    def get_info(self):
        return self.__textpage["task"].current
        
    def get_status(self):
        return self.__textpage["task"].current.status
        
    def get_importance(self):
        return self.__textpage["task"].current.importance
        
    def get_target(self):
        return self.__textpage["task"].current.target
        
    def get_milestone(self):
        return self.__textpage["task"].current.milestone
        
    def get_assignee(self):
        return self.__textpage["task"].current.assignee
        
    def get_sourcepackage(self):
        return self.__textpage["task"].current.sourcepackage
        
    def get_affects(self):
        return self.__textpage["task"].current.affects

    def get_private(self):
        return bool(self.__textpage["bug"].private)

    def get_security(self):
        return bool(self.__textpage["bug"].security)

    def get_tags(self):
        return self.__textpage["bug"].tags
        
    def get_attachments(self):
        return self.__textpage["bug"].attachments

    def get_date(self):
        return self.__textpage["bug"].date_reported

    def get_date_updated(self):
        return self.__textpage["bug"].date_updated
        
    def get_comments(self):
        return self.__textpage["comments"]
        
    def get_description(self):
        return self.__textpage["bug"].description or ""
    get_description_raw = get_description
        
    def get_text(self):
        return "%s\n%s" %(self.description,"\n".join([c.text for c in self.comments]))
