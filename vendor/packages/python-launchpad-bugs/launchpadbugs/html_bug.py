"""
TODO:
    * TODOs are specified in the classes
    * being more verbose in 'container'-object's __repr__: add bugnumber to each object
    * standardize *.changed (output: frozenset/list, property)
    * how to handle global attachment-related variables?
    * add revert()-function(s)
THIS IS STILL WORK IN PROGRESS!!
"""
import re
import os
import libxml2

import exceptions
from exceptions import parse_error

from bugbase import Bug as BugBase
from lptime import LPTime
from tasksbase import LPTasks, LPTask
from attachmentsbase import LPAttachments, LPAttachment
from commentsbase import LPComments, LPComment
from lphelper import user, product, change_obj, unicode_for_libxml2
from lpconstants import BUG, BASEURL
from subscribersbase import LPSubscribers
from utils import valid_lp_url
        
# deactivate error messages from the validation [libxml2.htmlParseDoc]
def noerr(ctx, str):
    pass

libxml2.registerErrorHandler(noerr, None)
        

def _small_xpath(xml, expr):
    """ Returns the content of the first result of a xpath expression  """
    result = xml.xpathEval(expr)
    if not result:
        return False
    return result[0].content
        
def get_bug(id):
    return Bug._container_refs[id]


def _blocked(func, error=None):
    def f(a, *args, **kwargs):
        try:
            x = a.infotable.current
        except AttributeError, e:
            error = "%s %s" %(f.error, e)
            raise AttributeError, error
        return func(a, *args, **kwargs)
    f.error = error or "Unable to get current InfoTable row."
    return f 

def _attr_ext(i, s):
    if i.startswith("__"):
        return "_%s%s" %(s.__class__.__name__,i)
    else:
        return i


def _gen_getter(attr):
    """ Returns a function to return the value of an attribute
    
    Example:
        get_example = _gen_getter("x.y")
    is like:
        def get_example(self):
            if not x.parsed:
                x.parse()
            return x.y
    
    """
    def func(s):
        attributes = attr.split(".")
        attributes = map(lambda a: _attr_ext(a, s), attributes)
        x = getattr(s, attributes[0])
        attributes.insert(0, s)
        if not x.parsed:
            x.parse()
        return reduce(getattr, attributes)
    return func

        
def _gen_setter(attr):
    """ Returns a function to set the value of an attribute
    
    Example:
        set_example = _gen_setter("x.y")
    is like:
        def set_example(self, value):
            if not x.parsed:
                x.parse()
            x.y = value
    
    """
    def func(s, value):
        attributes = attr.split(".")
        attributes = map(lambda a: _attr_ext(a, s), attributes)
        x = getattr(s, attributes[0])
        attributes.insert(0, s)
        if not x.parsed:
            x.parse()
        setattr(reduce(getattr, attributes[:-1]), attributes[-1], value)
    return func

def create_project_task(project):
    x = [None]*14
    task = Info(product(project), *x)
    task._type = "%s.product" %project
    return task

def create_distro_task(distro=None, sourcepackage=None, url=None):
    x = [None]*14
    if distro is None:
        distro = "Ubuntu"
    if not sourcepackage is None:
        affects = product("%s (%s)"%(sourcepackage, distro.title()))
    else:
        affects = product(distro.title())
    task = Info(affects, *x)
    task._type = "%s.sourcepackagename" %affects
    task._remote = url
    return task
        
class Info(LPTask):
    """ The 'Info'-object represents one row of the 'InfoTable' of a bugreport
    
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
    """
    def __init__(self, affects, status, importance, assignee, current,
                    editurl, type, milestone, available_milestone,
                    lock_importance, targeted_to, remote, editlock,
                    edit_fields, connection):
        data_dict = { "affects": affects,
                      "status": status,
                      "importance": importance,
                      "assignee": assignee,
                      "current": current,
                      "editurl": editurl,
                      "type": type,
                      "milestone": milestone,
                      "available_milestone": available_milestone,
                      "lock_importance": lock_importance,
                      "targeted_to": targeted_to,
                      "remote": remote,
                      "editlock": editlock,
                      "edit_fields": edit_fields,
                      "connection": connection}
                        
        LPTask.__init__(self, data_dict)
        self._cache = {"sourcepackage" : self._sourcepackage,
                "status": self._status, "importance": self._importance,
                "assignee": self._assignee, "milestone": self._milestone}
                        
    def set_sourcepackage(self, package):
        if self._editlock:
            raise IOError, "The sourcepackage of this bug can't be edited, maybe because this bug is a duplicate of an other one"
        self._sourcepackage = package
        
    def set_assignee(self, lplogin):
        if self._editlock:
            raise IOError, "The assignee of this bug can't be edited, maybe because this bug is a duplicate of an other one"
        if self._remote:
            raise IOError, "This task is linked to a remote-bug system, please change the assignee there"
        self._assignee = lplogin
        
    def set_status(self, status):
        if self._editlock:
            raise IOError, "The status of this bug can't be edited, maybe because this bug is a duplicate of an other one"
        if self._remote:
            raise IOError, "This task is linked to a remote-bug system, please change the status there"
        if status not in BUG.STATUS.values():
            raise ValueError, "Unknown status '%s', status must be one of these: %s" %(status, BUG.STATUS.values())
        self._status = status
        
    def set_importance(self, importance):
        if self._editlock:
            raise IOError, "The importance of this bug can't be edited, maybe because this bug is a duplicate of an other one"
        if self._remote:
            raise IOError, "This task is linked to a remote-bug system, please change the importance there"
        if self._lock_importance:
            raise IOError, "'Importance' changeable only by a project maintainer or bug contact"
        if importance not in BUG.IMPORTANCE.values():
            raise ValueError, "Unknown importance '%s', importance must be one of these: %s" %(importance, BUG.IMPORTANCE.values())
        self._importance = importance
        
    def set_milestone(self, milestone):
        if self._editlock:
            raise IOError, "The milestone of this bug can't be edited, maybe because this bug is a duplicate of an other one"
        if not self.__available_milestone:
            raise ValeError, "No milestones defined for this product"
        if milestone not in self._available_milestone:
            raise ValueError, "Unknown milestone, milestone must be one of these: %s" %self._available_milestone
        self._milestone = milestone
        
    
    def commit(self, force_changes=False, ignore_lp_errors=True):
        """ Commits the local changes to launchpad.net
        
        * force_changes: general argument, has not effect in this case
        * ignore_lp_errors: if the user tries to commit invalid data to launchpad,
            launchpad returns an error-page. If 'ignore_lp_errors=False' Info.commit()
            will raise an 'ValueError' in this case, otherwise ignore this
            and leave the bugreport in launchpad unchanged (default=True)
        """
        changed = self.changed
        if changed:
            if self._type:
                full_sourcepackage = self._type[:self._type.rfind(".")]
            else:
                full_sourcepackage = "%s_%s" %(self.targeted_to, str(self._affects))
            s = self.sourcepackage
            if s == "ubuntu":
                s = ""
            args = { '%s.actions.save' %full_sourcepackage: '1',
                '%s.comment_on_change' %full_sourcepackage: ''# set_status_comment
                    }
            if self._type:
                args[self._type] = s
            if ".status" in self._edit_fields:
                args['%s.status-empty-marker' %full_sourcepackage] = '1'
                args['%s.status' %full_sourcepackage] = self.status
            if ".importance" in self._edit_fields:
                args['%s.importance' %full_sourcepackage] = self.importance
                args['%s.importance-empty-marker' %full_sourcepackage] = '1'
            if ".milestone" in self._edit_fields:
                args['%s.mlestone' %full_sourcepackage] = ""
                args['%s.milestone-empty-marker' %full_sourcepackage] = '1'
            args['%s.assignee.option' %full_sourcepackage] = '%s.assignee.assign_to' %full_sourcepackage
            args['%s.assignee' %full_sourcepackage] = self.assignee or ""
                
            result = self._connection.post(self._editurl, args)
            if result.url.endswith("+editstatus") and not ignore_lp_errors:
                raise exceptions.PythonLaunchpadBugsValueError({"arguments": args},
                    self._editurl, "one or more arguments might be wrong")


class InfoTable(LPTasks):
    """ The 'InfoTable'-object represents the tasks at the top of a bugreport
        
    * read-only attributes:
        .current: returns the highlighted Info-object of the bugreport
    
    TODO:  * rename 'InfoTable' into 'TaskTable'
           * allow adding of tasks (Also affects upstream/Also affects distribution)
           * does current/tracked work as expected?
           * remote: parse editable values
    """
    def __init__(self, connection, xml, url):
        LPTasks.__init__(self, {"connection":connection, "url":url, "xml":xml})
        self.__url = url
        self.__xml = xml

    def parse(self):
        """ Parsing the info-table
        
        * format:  'Affects'|'Status'|'Importance'|'Assigned To'
        
        TODO: * working on 'tracked in...' - currently there is only one 'tracked in'
                entry per bugreport supported
              * REMOTE BUG!!!
        """
        if self.parsed:
            return True
        rows = self.__xml[0].xpathEval('tbody/tr[not(@style="display: none") and not(@class="secondary")]')
        parse_error(self.__xml[0], "InfoTable.rows", xml=self.__xml, url=self.__url)
        
        highl_target = None
        # status of (remote)-bugs can be 'unknown''
        temp_status = BUG.STATUS.copy()
        temp_status["statusUNKNOWN"] = "Unknown"
        # importance of (remote)-bugs can be 'unknown''
        temp_importance = BUG.IMPORTANCE.copy()
        temp_importance["importanceUNKNOWN"] = "Unknown"
        
        tracked = False
        affects = product(None)
        for row in rows:
            edit_fields = set()
            tmp_affects = affects
            current = False
            remote = None
                
            if row.prop("class") == "highlight":
                current = True
                
            row_cells = row.xpathEval("td")
            row_cells = [i for i in row_cells if not i.prop("class") == "icon left right"]
            
            if not tracked:
                # parse affects
                parse_error(row_cells[0], "InfoTable.affects.1", xml=row_cells, url=self.__url)
                m_type = row_cells[0].xpathEval("img")
                parse_error(m_type, "InfoTable.affects.2", xml=row_cells, url=self.__url)
                
                affects_type = m_type[0].prop("src").split("/")[-1]
                m_name = row_cells[0].xpathEval("a")
                parse_error(m_name, "InfoTable.affects.3", xml=row_cells, url=self.__url)
                
                affects_lpname = m_name[0].prop("href").split("/")[-1]
                affects_longname = m_name[0].content
            affects = product(affects_lpname, affects_longname, affects_type)
                
            if row_cells[1].prop("colspan"):
                tracked = True
                if current:
                    highl_target = row_cells[1].xpathEval('span')[0].content.split("\n")[2].lstrip().rstrip()
                    current = False
                continue # ignore "tracked in ..." - rows
            tracked = False
                
            targeted_to = None
            if row_cells[0].xpathEval('img[@alt="Targeted to"]'):
                targeted_to = row_cells[0].xpathEval('a')[0].content
                affects = tmp_affects
                if highl_target:
                    if targeted_to.lower() == highl_target.lower():
                        current = True
                            
            xmledit = row.xpathEval('following-sibling::tr[@style="display: none"][1]')
            
            type = None
            milestone = None
            available_milestone = {}
            editurl = None
            editlock = False
            lock_importance = False
            
            if xmledit:
                xmledit = xmledit[0]
                editurl = xmledit.xpathEval('td/form')
                parse_error(editurl, "InfoTable.editurl", xml=xmledit, url=self.__url)
                
                editurl = valid_lp_url(editurl[0].prop('action'), BASEURL.BUG)
            
                if xmledit.xpathEval('descendant::label[contains(@for,"bugwatch")]'):
                    x = xmledit.xpathEval('descendant::label[contains(@for,"bugwatch")]/a')
                    if x:
                        remote = x[0].prop("href")
                    else:
                        # if the status of the bug is updated manually.
                        remote = True
                    
                if not remote:
                    for i in ["product", "sourcepackagename"]:
                        x = xmledit.xpathEval('td/form/div//table//input[contains(@id,".%s")]' %i)
                        if x:
                            type = x[0].prop("id")
                    if not type:
                        if not row.xpathEval('td[2]//img[contains(@src,"milestone")]'):
                            parse_error(False, "InfoTable.type.milestone", xml=xmledit, url=self.__url)
                
                    m = xmledit.xpathEval('descendant::select[contains(@id,".milestone")]//option')
                    if m:
                        for i in m:
                            available_milestone[i.prop("value")] = i.content
                            if i.prop("selected"):
                                milestone = i.content
                            
                    m = xmledit.xpathEval('descendant::td[contains(@title, "Changeable only by a project maintainer") and count(span)=0]')
                    if len(m) == 1 and not milestone:
                        milestone = m[0].content.strip("\n ")
            
                if not xmledit.xpathEval('descendant::select[contains(@id,".importance")]'):
                    lock_importance = True
                m = set([".sourcepackagename", ".product", ".status", ".status-empty-marker",
                            ".importance", ".importance-empty-marker", ".milestone" ,
                            ".milestone-empty-marker"])
                for i in m:
                    x = xmledit.xpathEval('td/form//input[contains(@name,"%s")]' %i)
                    y = xmledit.xpathEval('td/form//select[contains(@name,"%s")]' %i)
                    if x or y:
                        edit_fields.add(i)
            else:
                editlock = True
                        
            parse_error(row_cells[1], "InfoTable.status.1", xml=row_cells, url=self.__url)
            parse_error(row_cells[1].prop("class") in temp_status , "InfoTable.status.2",
                            msg="unknown bugstatus '%s' in InfoTable.parse()" %row_cells[1].prop("class"),
                            error_type=exceptions.VALUEERROR,
                            url=self.__url)
            status = temp_status[row_cells[1].prop("class")]
            
            parse_error(row_cells[2], "InfoTable.importance.1", xml=row_cells, url=self.__url)
            parse_error(row_cells[2].prop("class") in temp_importance, "InfoTable.importance.2",
                            msg="unknown bugimportance '%s' in InfoTable.parse()" %row_cells[2].prop("class"),
                            error_type=exceptions.VALUEERROR,
                            url=self.__url)
            importance = temp_importance[row_cells[2].prop("class")]
            
            assignee = row_cells[3].xpathEval("a")
            if assignee:
                assignee = assignee[0]
                if remote:
                    assignee = " ".join([i.lstrip().rstrip() for i in assignee.content.split("\n") if i.lstrip()])
                else:
                    assignee = user.parse_html_user(assignee)
            else:
                assignee = user(None)
            
            if current:
                self._current = len(self)
            self.append(Info(affects, status, importance,
                            assignee, current, editurl or self._url, type, milestone,
                            available_milestone, lock_importance,
                            targeted_to, remote, editlock, edit_fields,
                            connection=self._connection))

        self.parsed = True
        return True
        
    def _LP_create_task(self, task, force_changes, ignore_lp_errors):
        tsk = task.component._type or ""
        if tsk.endswith(".product"):
            url = "%s/+choose-affected-product" %self._url
            args = {"field.visited_steps": "choose_product, specify_remote_bug_url",
                    "field.product": str(task.component.affects),
                    "field.actions.continue": "Add to Bug Report"}
            result = self._connection.post(url, args)
            if result.url == url:
                # possible errors:
                #  * project does not exist
                #  * 'A fix for this bug has already been requested for ...'
                raise exceptions.choose_pylpbugsError(error_type=exceptions.VALUEERROR, text=result.text, url=url)
        elif tsk.endswith(".sourcepackagename"):
            url = "%s/+distrotask" %self._url
            args = { "field.distribution": task.component.target or "ubuntu",
                     "field.distribution-empty-marker": 1,
                     "field.sourcepackagename": task.component.sourcepackage or "",
                     "field.visited_steps": "specify_remote_bug_url",
                     "field.bug_url": task.component.remote or "",
                     "field.actions.continue": "Continue"}
            result = self._connection.post(url, args)
            if result.url == url:
                # possible errors
                # * "This bug is already open on <distro> with no package specified."
                # * "There is no package in <distro> named <sourcepackage>"
                # (not sure of other errors)
                raise exceptions.choose_pylpbugsError(error_type=exceptions.VALUEERROR, text=result.text, url=url)
                
        else:
            raise NotImplementedError
        

   
class BugReport(object):
    """ The 'BugReport'-object is the report itself
    
    * editable attributes:
        .description: any text
        .title/.summary: any text
        .tags: list, use list operations to add/remove tags
        .nickname
        
    * read-only attributes:
        .target: e.g. 'upstream'
        .sourcepackage: 'None' if not package specified
        .reporter, .date
    """
    def __init__(self, connection, xml, url):
        [self.__title, self.__description, self.__tags, self.__nickname,
        self.target, self.sourcepackage, self.reporter, self.date] = [None]*8
        self.__cache = {}
        self.parsed = False
        self.__connection=connection
        self.__xml = xml
        self.__url = url
        self.__description_raw = None
        
    def __repr__(self):
        return "<BugReport>"

    def parse(self):
        if self.parsed:
            return True
        
        # getting text (description) of the bugreport
        description = self.__xml.xpathEval('//body//div[@class="report"]/\
div[@id="bug-description"]')
        parse_error(description, "BugReport.description", xml=self.__xml, url=self.__url)
        
        # hack to change </p> into \n - any better idea? - NOT just eye-candy
        # this is also the format needed when committing changes
        p = description[0].xpathEval('p')
        description = ""
        for i in p[:-1]:
            description = "".join([description,i.content,"\n\n"])
        description = "".join([description,p[-1:].pop().content])
        self.__description = description
        
        # getting tile (summary) of the bugreport
        title = self.__xml.xpathEval('//title')
        parse_error(title, "BugReport.title", self.__xml, self.__url)
        titleFilter = 'Bug #[0-9]* in ([^:]*?): (.*)'
        title = re.findall(titleFilter, title[0].content)
        parse_error(title, "BugReport.__title", url=self.__url)
        self.__title = title[0][1].rstrip('\xe2\x80\x9d').lstrip('\xe2\x80\x9c')
        
        # getting target and sourcepackage
        target = title[0][0].split(" ")
        if len(target) == 2:
            self.target = target[1].lstrip("(").rstrip(")")
        self.sourcepackage = target[0]
        # fix sourcepackage
        if self.sourcepackage == 'Ubuntu':
            self.sourcepackage = None
        
        # getting tags of bugreport
        tags = self.__xml.xpathEval('//body//div[@class="report"]//\
div[@id="bug-tags"]//a')
        self.__tags = [i.content for i in tags]

        
        # (thekorn) 20080828: design on edge changed
        # edge and stable have significantly diverged
        # if they are in sync again this conditional construct can
        # be removed again
        # affected: nickname, date, reporter
        m = self.__xml.xpathEval('//span[@class="object identifier"]') #stable
        m = m or self.__xml.xpathEval('//div[@class="object identifier"]') #edge
        parse_error(m, "BugReport.__nickname", xml=self.__xml, url=self.__url)
        r = re.search(r'\(([^\)]+)\)', m[0].content)
        self.__nickname = (r and r.group(1)) or None
        
        d = self.__xml.xpathEval('//span[@class="object timestamp"]/span') #stable
        d = d or self.__xml.xpathEval('//p[@class="object timestamp"]/span') #edge
        parse_error(d, "BugReport.date", xml=m[0], url=self.__url)
        self.date = LPTime(d[0].prop("title"))
        
        
        d = self.__xml.xpathEval('//span[@class="object timestamp"]/a') #stable
        d = d or self.__xml.xpathEval('//p[@class="object timestamp"]/a') #edge
        parse_error(d, "BugReport.reporter", xml=m[0], url=self.__url)
        self.reporter = user.parse_html_user(d[0])
        
        self.__cache = {"title": self.__title, "description" : self.__description,
                            "tags" : self.__tags[:], "nickname" : self.__nickname}
        self.parsed = True
        return True
        
    def get_title(self):
        return self.__title
 
    def set_title(self, title):
        self.__title = title
    title = property(get_title, set_title, doc="title of a bugreport")
         
    def get_description(self):
        return self.__description
 
    def set_description(self, description):
        self.__description = description
    description = property(get_description, set_description,
                    doc="description of a bugreport")

    @property
    def tags(self):
        return self.__tags
         
    def get_nickname(self):
        return self.__nickname
 
    def set_nickname(self, nickname):
        self.__nickname = nickname
    nickname = property(get_nickname, set_nickname,
                    doc="nickname of a bugreport")
    
    @property
    def changed(self):
        changed = set()
        for k in self.__cache:
            if self.__cache[k] != getattr(self, k):
                changed.add(change_obj(k))
        return frozenset(changed)
        
    @property
    def description_raw(self):
        if not self.__description_raw:
            url = "%s/+edit" %self.__url
            result = self.__connection.get(url)
            xmldoc = libxml2.htmlParseDoc(unicode_for_libxml2(result.text), "UTF-8")
            x = xmldoc.xpathEval('//textarea[@name="field.description"]')
            parse_error(x, "BugReport.description_raw", xml=xmldoc, url=url)
            self.__description_raw = x[0].content
        return self.__description_raw
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        """ Commits the local changes to launchpad.net
        
        * force_changes: if a user adds a tag which has not been used before
            and force_changes is True then commit() tries to create a new
            tag for this package; if this fails or force_changes=False
            commit will raise a 'ValueError'
        * ignore_lp_errors: if the user tries to commit invalid data to launchpad,
            launchpad returns an error-page. If 'ignore_lp_errors=False' Info.commit()
            will raise an 'ValueError' in this case, otherwise ignore this
            and leave the bugreport in launchpad unchanged (default=True)
        """
        if self.changed:
            if "description" not in [i.component for i in self.changed]:
                description = self.description_raw
            else:
                description = self.__description
            if "nickname" not in [i.component for i in self.changed]:
                nickname = ""
            else:
                nickname = self.nickname
            if not (self.title and description):
                raise exceptions.PythonLaunchpadBugsValueError(msg="To change a bugreport 'description' \
and 'title' don't have to be empty", url=self.__url)
            args = { 'field.actions.change': '1', 
                 'field.title': self.title, 
                 'field.description': description, 
                 'field.tags': ' '.join(self.tags),
                 'field.name': nickname
                  }
            url = "%s/+edit" %self.__url
            result = self.__connection.post(url, args)
            
            if result.url == url and (not ignore_lp_errors or force_changes):
                x = libxml2.htmlParseDoc(result.text, "UTF-8")
                # informational message - 'new tag'
                if x.xpathEval('//p[@class="informational message"]/input[@name="field.actions.confirm_tag"]'):
                    if force_changes:
                        # commit new tag
                        args['field.actions.confirm_tag'] = '1'
                        url = "%s/+edit" %self.__url
                        result = self.__connection.post(url, args)
                    else:
                        raise ValueError, "Can't set 'tag', because it has not yet been used before."
                y = x.xpathEval('//p[@class="error message"]')
                if y:
                    raise ValueError, "launchpad.net error: %s" %y[0].content


class Attachment(LPAttachment):
    """ Returns an 'Attachment'-object
    
    * editable attributes:
        .description: any text
        .contenttype: any text
        .is_patch: True/False
        
    * read-only attributes:
        .id: hash(local_filename) for local files,
            launchpadlibrarian-id for files uploaded to launchpadlibrarian.net
        .is_down: True if a file is downloaded to ATTACHMENT_PATH
        .is_up: True if file is uploaded to launchpadlibrarian.net
        ...
    TODO: work on docstring
    """
    def __init__(self, connection, url=None, localfilename=None, localfileobject=None,
                        description=None, is_patch=None, contenttype=None, comment=None):
        LPAttachment.__init__(self, connection, url, localfilename,
                                localfileobject, description, is_patch,
                                contenttype, comment)
            
    def get_bugnumber(self):
        if self.is_up:
            return self.edit_url.split("/")[-3]
                    
    def get_sourcepackage(self):
        if self.is_up:
            return self.edit_url.split("/")[-5]
            
    def get_edit_url(self):
        if self.is_up:
            return valid_lp_url(self._edit, BASEURL.BUG)
        

class Attachments(LPAttachments):
    def __init__(self, comments, connection, xml):
        LPAttachments.__init__(self, comments=comments)
        self.__xml = xml
        self.__connection = connection
        self.__comments = comments
        
    def parse(self):
        super(Attachments, self).parse()
        if self.__xml:
            attachments = self.__xml[0].xpathEval('li[@class="download"]')
            all_att = {}
            for a in attachments:
                url = a.xpathEval('a')[0].prop("href")
                edit = a.xpathEval('small/a')[0].prop("href")
                all_att[url] = edit
            for i in self:
                i._edit = all_att.get(i.url, None)
                if not i._edit and i.is_up:
                    parse_error(False, "Attachments.edit.1",
                                    msg="There is an attachment (id=%s) which is added to a comment but does not appear in the sidepanel ('%s')" %(i.id, self.__comments._url),
                                    error_type=exceptions.RUNTIMEERROR)
        else:
            parse_error(not self._current, "Attachments.edit.2",
                            msg="Unable to parse the 'attachments' sidepanel although there are files attached to comments ('%s')" %self.__comments._url,
                            error_type=exceptions.RUNTIMEERROR)
            
                
    def commit(self, force_changes=True, ignore_lp_errors=False, com_subject=None):
        """
            when adding a new attachment, this attachment is added as a new comment.
            this new comment has no subject but a subject is required.
            setting
                force_changes=True and ignore_lp_errors=False
            results in adding a subject like:
                "Re: <bug summary>"
        """
        # nested functions:
        def _lp_edit(attachment):
            args = {'field.actions.change': '1', 'field.title': attachment.description,
                    'field.patch': attachment.is_patch and 'on' or 'off', 'field.contenttype': attachment.contenttype or "text/plain"}
            self.__connection.post("%s/+edit" %attachment.edit_url, args)
        def _lp_delete(attachment):
            args = {'field.actions.delete': '1', 'field.title': attachment.description,
                    'field.patch': 'off', 'field.contenttype': 'text/plain'}
            self.__connection.post("%s/+edit" %attachment.edit_url, args)
            
        def _lp_add(attachment):
            """ delegated to comments """
            assert isinstance(attachment, Attachment), "<attachment> has to be an instance of 'Attachment'"
            c = Comment(attachment=(attachment,))
            # delegate to Comments
            self.__comments._lp_add_comment(c, force_changes, ignore_lp_errors, com_subject)
            
        changed = set(self.changed)
        for i in changed:
            if i.action == "added":
                _lp_add(i.component)
            elif i.action == "deleted":
                _lp_delete(i.component)
            elif i.action == "changed":
                _lp_edit(i.component)
            else:
                raise AttributeError, "Unknown action '%s' in Attachments.commit()" %i.component


class Comment(LPComment):
    def __init__(self, subject=None, text=None, attachment=None):
        LPComment.__init__(self, subject, text, attachment)


class Comments(LPComments):
    
    def __init__(self, connection, xml, url):        
        LPComments.__init__(self, url=url)
        self.__xml = xml
        self.__connection = connection
        self.__url = url
        
    def parse(self):
        for com in self.__xml:
            if com.xpathEval('div[@class="boardBugActivityBody"]'):
                continue

            m = com.xpathEval('div[@class="boardCommentDetails"]/a[1]')
            parse_error(m, "Comments.user", xml=self.__xml, url=self.__url)
            com_user = user.parse_html_user(m[0])

            m = com.xpathEval('div[@class="boardCommentDetails"]/a[2]')
            parse_error(m, "Comments.nr", xml=self.__xml, url=self.__url)
            com_nr = m[0].prop('href').split('/')[-1]

            m = com.xpathEval('div[@class="boardCommentDetails"]/span')
            parse_error(m, "Comments.date", xml=self.__xml, url=self.__url)
            com_date = LPTime(m[0].prop('title'))
            
            #optional subject
            m = com.xpathEval('div[@class="boardCommentDetails"]/a[2]/strong')
            if m:
                com_subject = m[0].content
            else:
                com_subject = None
            
            m = com.xpathEval('div[@class="boardCommentBody"]/div')
            parse_error(m, "Comments.text", xml=self.__xml, url=self.__url)
            com_text = m[0].content
            
            com_attachments = set()
            m = com.xpathEval('div[@class="boardCommentBody"]/ul/li')
            for a in m:
                a_url = a.xpathEval("a").pop()
                a = re.search(r",\n +(\S+)(;|\))", a.content)
                parse_error(a, "Comments.attachment.re.%s" %a_url.prop('href'), xml=com, url=self.__url)
                a_contenttype = a.group(1)
                com_attachments.add(Attachment(self.__connection, url=a_url.prop('href'),
                    description=a_url.content, comment=com_nr, contenttype=a_contenttype))
                
            c = Comment(com_subject, com_text, com_attachments)
            c.set_attr(nr=com_nr,user=com_user,date=com_date)
            self.add(c)
        self._cache = self[:]
        self.parsed = True
        return True
        
    def new(self, subject=None, text=None, attachment=None):
        return Comment(subject, text, attachment, all_attachments=self._attachments)
        
    @property
    def _url(self):
        return self.__url
        
                
    def _lp_add_comment(self, comment, force_changes, ignore_lp_errors, com_subject):
        assert isinstance(comment, Comment)
        args = {
            'field.subject': comment.subject or com_subject or "Re:",
            'field.comment': comment.text or "", 
            'field.actions.save': '1',
            'field.filecontent.used': '',
            'field.email_me.used': ''
                }
        if comment.attachments:
            # attachment is always a list, currently only 1 attachment per new comment supported
            assert isinstance(comment.attachments, set), "comment.attachments has to be a set()"
            assert len(comment.attachments) == 1, "currently LP only supports uploading of one comment at a time"
            ca = list(comment.attachments)[0]
            assert isinstance(ca, Attachment), "the file added to a comment has to be an instance of 'Attachment'"
            assert ca.description, "each attachment needs al east a description"
            args['field.patch.used'] = ''
            args['field.filecontent.used'] = ''
            args['field.filecontent'] = ca.local_fileobject
            args['field.attachment_description'] = ca.description or ""
            args['field.patch'] = ca.is_patch and 'on' or 'off'
         
        # print args #DEBUG
        url = self.__url + '/+addcomment'
        result = self.__connection.post(url, args)
        # print result.url #DEBUG
        if result.url == url and not ignore_lp_errors:# or force_changes):
            # print "check result" #DEBUG
            x = libxml2.htmlParseDoc(result.text, "UTF-8")
            y = x.xpathEval('//p[@class="error message"]')
            if y:
                if force_changes:
                    z = x.xpathEval('//input[@name="field.subject" and @value=""]')
                    if z:
                        # print "has no 'subject' - add one!" #DEBUG
                        z = x.xpathEval('//div[@class="pageheading"]/div')
                        comment.subject = "Re: %s" %z[0].content.split("\n")[-2].lstrip().rstrip()
                        self._lp_add_comment(comment, False, ignore_lp_errors)
                else:
                    # print result.text
                    raise ValueError, "launchpad.net error: %s" %y[0].content
        return result
            
    def commit(self, force_changes=False, ignore_lp_errors=True, com_subject=None):
        for i in self.changed:
            if i.action == "added":
                self._lp_add_comment(i.component, force_changes, ignore_lp_errors, com_subject)
            else:
                raise AttributeError, "Unknown action '%s' in Comments.commit()" %i.component


class Duplicates(object):
    def __init__(self, connection, xml, url):
        self.parsed = False
        self.__cache = None
        self.__connection=connection
        self.__xml = xml
        self.__url = url
        [self.__duplicate_of, self.__duplicates] = [None]*2
        
    def __repr__(self):
        return "<Duplicates>"
        
    def parse(self):
        if self.parsed:
            return True
        # Check if this bug is already marked as a duplicate
        nodes = self.__xml.xpathEval('//body//a[@id="duplicate-of"]')
        if len(nodes)>0:
            self.__duplicate_of = int(nodes[0].prop('href').split('/').pop())
        result = self.__xml.xpathEval('//body//div[@class="portlet"]/h2[contains(.,"Duplicates of this bug")]/../div[@class="portletBody"]/div/ul//li/a')
        self.__duplicates = set([int(i.prop("href").split('/')[-1]) for i in result])
        self.__cache = self.__duplicate_of
        self.parsed = True
        return True
        
    def get_duplicates(self):
        return self.__duplicates
    duplicates = property(get_duplicates, doc="get a list of duplicates")
    
    def get_duplicate_of(self):
        return self.__duplicate_of
        
    def set_duplicate_of(self, bugnumber):
        if bugnumber == None:
            self.__duplicate_of = None
        else:
            self.__duplicate_of = int(bugnumber)
    duplicate_of = property(get_duplicate_of, set_duplicate_of, doc="this bug report is duplicate of")
    
    @property
    def changed(self):
        __changed = set()
        if self.__cache != self.__duplicate_of:
            __changed.add("duplicate_of")
        return frozenset(__changed)
        
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        if self.changed:
            args = { 'field.actions.change': '1', 
                     'field.duplicateof': self.__duplicate_of or ""
                    }
            url = "%s/+duplicate" %self.__url
            result = self.__connection.post(url, args)
            
            if result.url == url and not ignore_lp_errors:# or force_changes):
                x = libxml2.htmlParseDoc(result.text, "UTF-8")
                # informational message - 'new tag'
                y = x.xpathEval('//p[@class="error message"]')
                if y:
                    raise ValueError, "launchpad.net error: %s" %y[0].content
            
    
class Secrecy(object):
    def __init__(self, connection, xml, url):
        self.parsed = False
        self.__cache = set()
        self.__connection=connection
        self.__xml = xml
        self.__url = url
        [self.__security, self.__private] = [False]*2
        
    def __repr__(self):
        return "<Secrecy>"
        
    def parse(self):
        if self.parsed:
            return True
        # (thekorn) 20080711: design on edge changed
        # edge and stable have significantly diverged
        # if they are in sync again this conditional construct can
        # be removed again
        #~ this error check makes no sense
        #~ parse_error(self.__xml, "Secrecy.__xml", xml=self.__xml, url=self.__url)
        stable_xml = self.__xml.xpathEval('//body//div[@id="big-badges"]')
        if stable_xml:
            if stable_xml[0].xpathEval('img[@alt="(Security vulnerability)"]'):
                self.__security = True
            if stable_xml[0].xpathEval('img[@alt="(Private)"]'):
                self.__private = True
        else:
            self.__private = bool(self.__xml.xpathEval('//a[contains(@href, "+secrecy")]/strong'))
            self.__security = bool(self.__xml.xpathEval('//div[contains(@style, "/@@/security")]'))
        self.__cache = {"security": self.__security, "private" : self.__private}
        self.parsed = True
        return True
            
    def _editlock(self):
        return bool(get_bug(id(self)).duplicate_of)
            
    def get_security(self):
        assert self.parsed, "parse first"
        return self.__security
    
    def set_security(self, security):
        # if self._editlock():
        #    raise IOError, "'security' of this bug can't be edited, maybe because this bug is a duplicate of an other one"
        self.__security = bool(security)
    security = property(get_security, set_security, doc="security status")

    def get_private(self):
        assert self.parsed, "parse first"
        return self.__private
    
    def set_private(self, private):
        # if self._editlock():
        #    raise IOError, "'private' of this bug can't be edited, maybe because this bug is a duplicate of an other one"
        self.__private = bool(private)
    private = property(get_private, set_private, doc="private status")

    def get_changed(self):
        __changed = set()
        for k in self.__cache:
            if self.__cache[k] != getattr(self, k):
                __changed.add(k)
        return frozenset(__changed)
    changed = property(get_changed, doc="get a list of changed attributes")
        
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        __url = "%s/+secrecy" %self.__url
        status = ["off", "on"]
        if self.changed:
            __args = { 'field.private': status[int(self.private)],
                 'field.security_related': status[int(self.security)],
                 'field.actions.change': 'Change'
               }
            __result = self.__connection.post(__url, __args)


class Subscribers(LPSubscribers):
    """ TODO:
        * change structure: use three different sets instead of one big one
    """
    def __init__(self, connection, xml, url):
        self.parsed = False
        self.__connection=connection
        self.__xml = xml
        self.__url = url
        LPSubscribers.__init__(self, ("directly", "notified", "duplicates"))
        
    def parse(self):
        
        if self.parsed:
            return True
        parse_error(self.__xml, "Subscribers.__xml", xml=self.__xml, url=self.__url)
        xml = self.__xml[0].xpathEval('div[(@class="section" or @class="Section") and @id]') #fix for v6739
        xml_YUI = self.__xml[0].xpathEval('script[@type="text/javascript"]')
        if xml_YUI and not xml:
            bugnumber = int(self.__url.split("/")[-1])
            url = "https://launchpad.net/bugs/%i/+bug-portlet-subscribers-content" %bugnumber
            page = self.__connection.get(url)
            ctx = libxml2.htmlParseDoc(unicode_for_libxml2(page.text), "UTF-8")
            xml = ctx.xpathEval('//div[(@class="section" or @class="Section") and @id]')
        if xml:
            sections_map = {"subscribers-direct": "directly",
                            "subscribers-indirect": "notified",
                            "subscribers-from-duplicates": "duplicates",
                            }
            for s in xml:
                kind = sections_map[s.prop("id")]
                nodes = s.xpathEval("div/a")
                for i in nodes:
                    self[kind].add(user.parse_html_user(i))            
        else:
            if xml_YUI:
                n = ".YUI"
            else:
                n = ""
            parse_error(False, "Subscribers.__xml.edge.stable%s" %n, xml=self.__xml, url=self.__url)
        self.parsed = True
        return True
                
    def commit(self, force_changes=False, ignore_lp_errors=True):
        x = self.changed
        if x:
            for i in [a.component for a in x if a.action == "removed"]:
                self._remove(i)
            for i in [a.component for a in x if a.action == "added"]:
                self._add(i)
        
    def _add(self, lplogin):
        '''Add a subscriber to a bug.'''
        url = "%s/+addsubscriber" %self.__url
        args = { 'field.person': lplogin, 
                 'field.actions.add': 'Add'
               }
        result = self.__connection.post(url, args)
        if result.url == url:
            x = libxml2.htmlParseDoc(result.text, "UTF-8")
            if x.xpathEval('//div[@class="message" and contains(.,"Invalid value")]'):
                raise ValueError, "Unknown Launchpad ID. You can only subscribe someone who has a Launchpad account."
            else:
                raise ValueError, "Unknown error while subscribe %s to %s" %(lplogin, url)
        return result
        
    def _remove(self, lplogin):
        '''Remove a subscriber from a bug.'''
        url = "%s/" %self.__url
        args = { 'field.subscription': lplogin, 
                 'unsubscribe': 'Continue'
               }
        result = self.__connection.post(url, args)
        return result
        

class ActivityWhat(str):
    def __new__(cls, what, url=None):
        obj = super(ActivityWhat, cls).__new__(ActivityWhat, what)
        obj.__task = None
        obj.__attribute = None
        x = what.split(":")
        if len(x) == 2:
            obj.__task = x[0]
            obj.__attribute = x[1].strip()
        elif len(x) == 1:
            obj.__attribute = x[0]
        else:
            raise ValueError
        return obj
        
    @property
    def task(self):
        return self.__task
        
    @property
    def attribute(self):
        return self.__attribute


     
class Activity(object):
    def __init__(self, date, user, what, old_value, new_value, message):
        self.__date = date
        self.__user = user
        self.__what = what
        self.__old_value = old_value
        self.__new_value = new_value
        self.__message = message
        
    def __repr__(self):
        return "<%s %s '%s'>" %(self.user, self.date, self.what)        
        
    @property
    def date(self):
        return self.__date
        
    @property
    def user(self):
        return self.__user
        
    @property
    def what(self):
        return self.__what
        
    @property
    def old_value(self):
        return self.__old_value
        
    @property
    def new_value(self):
        return self.__new_value
        
    @property
    def message(self):
        return self.__message
        
        
class ActivityLog(object):
    """
    TODO: there is nor clear relation between an entry in the activity log
        and a certain task, this is why the result of when(), completed(),
        assigned() and started_work() may differ from the grey infobox added
        to each task. Maybe we should also parse this box.
    """
    def __init__(self, connection, url):
        self.parsed = False
        self.__connection=connection  
        self.__activity = []
        self.__url = url
        
    def __repr__(self):
        return "<activity log>"
        
    def __str__(self):
        return str(self.__activity)
        
    def __iter__(self):
        for i in self.activity:
            yield i
            
    def __getitem__(self, key):
        return self.activity[key]
        
    def __len__(self):
        return len(self.activity)
        
    @property
    def activity(self):
        if not self.parsed:
            self.parse()
        return self.__activity
        
    def _activity_rev(self):
        if not self.parsed:
            self.parse()
        return self.__activity_rev
        
    def parse(self):
        if self.parsed:
            return True
        page = self.__connection.get("%s/+activity" %self.__url)
        
        self.__xmldoc = libxml2.htmlParseDoc(unicode_for_libxml2(page.text), "UTF-8")
        table = self.__xmldoc.xpathEval('//body//table[@class="listing"][1]//tbody//tr')
        parse_error(table, "ActivityLog.__table", xml=self.__xmldoc, url=self.__url)
        for row in table:
            r = row.xpathEval("td")
            parse_error(len(r) == 6, "ActivityLog.len(td)", xml=row, url=self.__url)
            
            date = LPTime(r[0].content)
            x = r[1].xpathEval("a")
            parse_error(x, "ActivityLog.lp_user", xml=row, url=self.__url)
            lp_user = user.parse_html_user(x[0])
            try:
                what = ActivityWhat(r[2].content)
            except ValueError:
                parse_error(False, "ActivityLog.ActivityWhat", xml=self.__xmldoc, url="%s/+activity" %self.__url)
            old_value = r[3].content
            new_value = r[4].content
            message = r[5].content
            
            self.__activity.append(Activity(date, lp_user, what,
                                        old_value, new_value, message))
        self.__activity_rev = self.__activity[::-1]
        self.parsed = True
        return True
        
    def assigned(self, task):
        for i in self._activity_rev():
            if i.what.task == task and i.what.attribute == "assignee":
                return i.date
                
    def completed(self, task):
        for i in self._activity_rev():
            if i.what.task == task and i.what.attribute == "status" and i.new_value in ["Invalid", "Fix Released"]:
                return i.date
                
    def when(self, task):
        for i in self._activity_rev():
            if i.what == "bug" and i.message.startswith("assigned to") and i.message.count(task):
                return i.date
                
    def started_work(self, task):
        for i in self._activity_rev():
            if i.what.task == task and i.what.attribute == "status" and i.new_value in ["In Progress", "Fix Committed"]:
                return i.date
            
                
class Mentoring(object):
    def __init__(self, connection, xml, url):
        self.parsed = False
        self.__cache = set()
        self.__connection=connection
        self.__xml = xml
        self.__url = url
        self.__mentor = set()
        
    def __repr__(self):
        return "<Mentor for #%s>" %self.__url
        
    def parse(self):
        if self.parsed:
            return True
        for i in self.__xml:
            self.__mentor.add(user.parse_html_user(i))
        self.__cache = self.__mentor.copy()
        self.parsed = True
        return True
        
    @property
    def mentor(self):
        return self.__mentor
        
    @property
    def changed(self):
        """get a list of changed attributes
        currently read-only
        """
        return set()
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        raise NotImplementedError, 'this method is not implemented ATM'
        
        
class BzrBranch(object):
    def __init__(self, title, url, status):
        self.__title = title
        self.__url = url
        self.__status = status
        
    def __repr__(self):
        return "BzrBranch(%s, %s, %s)" %(self.title, self.url, self.status)
        
    __str__ = __repr__
            
    @property
    def title(self):
        return self.__title
        
    @property
    def url(self):
        return self.__url
        
    @property
    def status(self):
        return self.__status
        
        
        
class Branches(set):
    def __init__(self, connection, xml, url):
        self.parsed = False
        set.__init__(self)
        self.__url = url
        self.__xml = xml
        self.__connection = connection
        
    def parse(self):
        if self.parsed:
            return True
        for i in self.__xml:
            m = i.xpathEval("a[1]")
            assert m
            title = m[0].prop("title")
            url = m[0].prop("href")
            m = i.xpathEval("span")
            assert m
            status = m[0].content
            self.add(BzrBranch(title, url, status))
        self.parsed = True
        
    @property
    def changed(self):
        """get a list of changed attributes
        currently read-only
        """
        return set()
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        raise NotImplementedError, 'this method is not implemented ATM'


class Bug(BugBase):
    _container_refs = {}

    def __init__(self, bug=None, url=None, connection=None):
            
        BugBase.__init__(self, bug, url, connection)

        bugpage = self.__connection.get(self.__url)

        # self.text contains the whole HTML-formated Bug-Page
        self.__text = bugpage.text
        # Get the rewritten URL so that we have a valid one to attach comments
        # to
        self.__url = bugpage.url
        
        self.xmldoc = libxml2.htmlParseDoc(unicode_for_libxml2(self.__text), "UTF-8")
        
        self.__bugreport = BugReport(connection=self.__connection, xml=self.xmldoc, url=self.__url)
        self.__infotable = InfoTable(connection=self.__connection, xml=self.xmldoc.xpathEval('//body//table[@class="listing" or @class="duplicate listing"][1]'), url=self.__url)
        self.__comments = Comments(connection=self.__connection, xml=self.xmldoc.xpathEval('//body//div[normalize-space(@class)="boardComment"]'), url=self.__url)
        self.__attachments = Attachments(self.__comments, self.__connection, self.xmldoc.xpathEval('//body//div[@id="portlet-attachments"]/div/div/ul'))
        self.__duplicates = Duplicates(connection=self.__connection, xml=self.xmldoc, url=self.__url)
        self.__secrecy = Secrecy(connection=self.__connection, xml=self.xmldoc, url=self.__url)
        self.__subscribers = Subscribers(connection=self.__connection, xml=self.xmldoc.xpathEval('//body//div[@id="portlet-subscribers"]'), url=self.__url)
        self.__mentor = Mentoring(connection=self.__connection, xml=self.xmldoc.xpathEval('//body//img [@src="/@@/mentoring"]/parent::p//a'), url=self.__url)
        self.__activity = ActivityLog(connection=self.__connection, url=self.__url)
        self.__branches = Branches(self.__connection, self.xmldoc.xpathEval('//body//div[@class="bug-branch-summary"]'), self.__url)
        
        Bug._container_refs[id(self.__attachments)] = self
        Bug._container_refs[id(self.__comments)] = self
        Bug._container_refs[id(self.__secrecy)] = self

    def __del__(self):
        "run self.xmldoc.freeDoc() to clear memory"
        if hasattr(self, "xmldoc"):
            self.xmldoc.freeDoc()
        
    @property
    def changed(self):
        __result = []
        for i in filter(lambda a: a.startswith("_Bug__"),dir(self)):
            # just for Developing; later each object should have a 'changed' property
            try:
                a = getattr(self.__dict__[i], "changed")
            except AttributeError:
                continue
            if a:
                __result.append(change_obj(self.__dict__[i]))
        return __result
        
    def commit(self, force_changes=False, ignore_lp_errors=True):
        for i in self.changed:
            if isinstance(i.component, Comments):
                result = i.component.commit(force_changes, ignore_lp_errors, "Re: %s" %self.title)
            else:
                result = i.component.commit(force_changes, ignore_lp_errors)
                        
    def revert(self):
        """ need a function to revert changes """
        pass
                
            
        
       
# Overwrite the abstract functions in bugbase.Bug        
        
    # read-only
    
    get_url = _gen_getter("__url")
    get_bugnumber = _gen_getter("__bugnumber")
    
    get_reporter = _gen_getter("__bugreport.reporter")
    get_date = _gen_getter("__bugreport.date")
    get_duplicates = _gen_getter("__duplicates.duplicates")
    get_description_raw = _gen_getter("__bugreport.description_raw")
    get_activity = _gen_getter("__activity")
        
    def get_text(self):
        return "%s\n%s" %(self.description,"\n".join([c.text for c in self.comments]))
    
    #...
    
    # +edit

    get_title = _gen_getter("__bugreport.title")
    get_description = _gen_getter("__bugreport.description")
    set_description = _gen_setter("__bugreport.description")
    get_tags = _gen_getter("__bugreport.tags")
    get_nickname = _gen_getter("__bugreport.nickname")
    
    #...
    
    #+mentoring
    
    get_mentors = _gen_getter("__mentor.mentor")

    # +editstatus

    get_infotable = _gen_getter("__infotable")
    get_info = _blocked(_gen_getter("__infotable.current"), "No 'current' available.")
    get_target = _blocked(_gen_getter("__infotable.current.target"), "Can't get 'target'.")
    get_importance = _blocked(_gen_getter("__infotable.current.importance"), "Can't get 'importance'.")
    set_importance = _blocked(_gen_setter("__infotable.current.importance"), "Can't set 'importance'.")
    get_status = _blocked(_gen_getter("__infotable.current.status"), "Can't get 'status'.")
    set_status = _blocked(_gen_setter("__infotable.current.status"), "Can't set 'status'.")
    get_assignee = _blocked(_gen_getter("__infotable.current.assignee"), "Can't get 'assignee'.")
    set_assignee = _blocked(_gen_setter("__infotable.current.assignee"), "Can't set 'assignee'.")
    get_milestone = _blocked(_gen_getter("__infotable.current.milestone"), "Can't get 'milestone'.")
    set_milestone = _blocked(_gen_setter("__infotable.current.milestone"), "Can't set 'milestone'.")
    get_sourcepackage = _blocked(_gen_getter("__infotable.current.sourcepackage"), "Can't get 'sourcepackage'.")
    set_sourcepackage = _blocked(_gen_setter("__infotable.current.sourcepackage"), "Can't set 'sourcepackage'.")
    get_affects = _blocked(_gen_getter("__infotable.current.affects"), "Can't get 'affects'.")
    
    def has_target(self, target):
        if not self.__infotable.parsed:
            self.__infotable.parse()
        return self.__infotable.has_target(target)
        
    # ...
    
    # +duplicate

    get_duplicates = _gen_getter("__duplicates.duplicates")
    get_duplicate = _gen_getter("__duplicates.duplicate_of")
    set_duplicate = _gen_setter("__duplicates.duplicate_of")
    
    #...
    
    # +secrecy
    
    get_security = _gen_getter("__secrecy.security")
    set_security = _gen_setter("__secrecy.security")
    get_private = _gen_getter("__secrecy.private")
    set_private = _gen_setter("__secrecy.private")
    
    #...
        
    # subscription
    
    get_subscriptions = _gen_getter("__subscribers")
    get_attachments = _gen_getter("__attachments")    
    def get_comments(self):
        x = self.attachments
        if not self.__comments.parsed:
            self.comments.parse()
        return self.__comments

    def get_subscriptions_category(self, type):
        """ get subscriptions for a given category, possible categories are "directly", "notified", "duplicates" """
        if not self.__subscribers.parsed:
            self.__subscribers.parse()
        return self.__subscribers.get_subscriptions(type)
        
    get_branches = _gen_getter("__branches")
     
    
    
def create_new_bugreport(product, summary, description, connection, tags=[], security_related=False):
    """ creates a new bugreport and returns its bug object
    
        product keys: "name", "target" (optional)
        tags: list of tags
    """
    
    args = {"field.title": summary,
            "field.comment": description,
            "field.actions.submit_bug": 1}
    if tags:
        args["field.tags"] = " ".join(tags)
    if security_related:
        args["field.security_related"] = "on"
    if product.has_key("target"):
        url = "https://bugs.launchpad.net/%s/+source/%s/+filebug-advanced" %(product["target"], product["name"])
        args["field.packagename"] = product["name"]
    else:
        url = "https://bugs.launchpad.net/%s/+filebug-advanced" %product["name"]
    
    try:
        result = connection.post(url, args)
    except exceptions.LaunchpadError, e:
        try:
            x = connection.needs_login()
        except exceptions.LaunchpadError:
            x = False
        if x:
            raise exceptions.LaunchpadLoginError(url)
        elif isinstance(e, exceptions.LaunchpadURLError):
            if "Page not found" in e.msg:
                m = """Maybe there is no product '%s' in """ %product["name"]
                if product.has_key("target"):
                    m += """the distribution '%s'""" %product["target"]
                else:
                    m += "launchpad.net"
                raise exceptions.PythonLaunchpadBugsValueError(msg=m)
        else:
            raise
            
    if not result.url.endswith("+filebug-advanced"):
        return Bug(url=result.url, connection=connection)
    else:
        raise exceptions.choose_pylpbugsError(error_type=exceptions.VALUEERROR, text=result.text, url=url)
