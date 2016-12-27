"""
Various ugly utility functions for twill.

Apart from various simple utility functions, twill's robust parsing
code is implemented in the ConfigurableParsingFactory class.
"""

from cStringIO import StringIO
import os
import base64

import subprocess

import _mechanize_dist as mechanize
from _mechanize_dist import ClientForm
from _mechanize_dist._util import time
from _mechanize_dist._http import HTTPRefreshProcessor
from _mechanize_dist import BrowserStateError

class ResultWrapper:
    """
    Deal with mechanize/urllib2/whatever results, and present them in a
    unified form.  Returned by 'journey'-wrapped functions.
    """
    def __init__(self, http_code, url, page):
        if http_code is not None:
            self.http_code = int(http_code)
        else:
            self.http_code = 200
        self.url = url
        self.page = page

    def get_url(self):
        return self.url

    def get_http_code(self):
        return self.http_code

    def get_page(self):
        return self.page

def trunc(s, length):
    """
    Truncate a string s to length length, by cutting off the last 
    (length-4) characters and replacing them with ' ...'
    """
    if not s:
        return ''
    
    if len(s) > length:
        return s[:length-4] + ' ...'
    
    return s

def print_form(n, f, OUT):
    """
    Pretty-print the given form, assigned # n.
    """
    if f.name:
        print>>OUT, '\nForm name=%s (#%d)' % (f.name, n + 1)
    else:
        print>>OUT, '\nForm #%d' % (n + 1,)

    if f.controls:
        print>>OUT, "## ## __Name__________________ __Type___ __ID________ __Value__________________"


    submit_indices = {}
    n = 1
    for c in f.controls:
        if c.is_of_kind('clickable'):
            submit_indices[c] = n
            n += 1
            
    clickies = [c for c in f.controls if c.is_of_kind('clickable')]
    nonclickies = [c for c in f.controls if c not in clickies]

    for n, field in enumerate(f.controls):
        if hasattr(field, 'items'):
            items = [ i.name for i in field.items ]
            value_displayed = "%s of %s" % (field.value, items)
        else:
            value_displayed = "%s" % (field.value,)

        if field.is_of_kind('clickable'):
            submit_index = "%-2s" % (submit_indices[field],)
        else:
            submit_index = "  "
        strings = ("%-2s" % (n + 1,),
                   submit_index,
                   "%-24s %-9s" % (trunc(str(field.name), 24),
                                   trunc(field.type, 9)),
                   "%-12s" % (trunc(field.id or "(None)", 12),),
                   trunc(value_displayed, 40),
                   )
        for s in strings:
            print>>OUT, s,
        print>>OUT, ''

    print ''

def make_boolean(value):
    """
    Convert the input value into a boolean like so:
    
    >> make_boolean('true')
    True
    >> make_boolean('false')
    False
    >> make_boolean('1')
    True
    >> make_boolean('0')
    False
    >> make_boolean('+')
    True
    >> make_boolean('-')
    False
    """
    value = str(value)
    value = value.lower().strip()

    # true/false
    if value in ('true', 'false'):
        if value == 'true':
            return True
        return False

    # 0/nonzero
    try:
        ival = int(value)
        return bool(ival)
    except ValueError:
        pass

    # +/-
    if value in ('+', '-'):
        if value == '+':
            return True
        return False

    # on/off
    if value in ('on', 'off'):
        if value == 'on':
            return True
        return False

    raise TwillException("unable to convert '%s' into true/false" % (value,))

def set_form_control_value(control, val):
    """
    Helper function to deal with setting form values on checkboxes, lists etc.
    """
    if isinstance(control, ClientForm.CheckboxControl):
        try:
            checkbox = control.get()
            checkbox.selected = make_boolean(val)
            return
        except ClientForm.AmbiguityError:
            # if there's more than one checkbox, use the behaviour for
            # ClientForm.ListControl, below.
            pass
            
    if isinstance(control, ClientForm.ListControl):
        #
        # for ListControls (checkboxes, multiselect, etc.) we first need
        # to find the right *value*.  Then we need to set it +/-.
        #

        # figure out if we want to *select* it, or if we want to *deselect*
        # it (flag T/F).  By default (no +/-) select...
        
        if val.startswith('-'):
            val = val[1:]
            flag = False
        else:
            flag = True
            if val.startswith('+'):
                val = val[1:]

        # now, select the value.

        try:
            item = control.get(name=val)
        except ClientForm.ItemNotFoundError:
            try:
                item = control.get(label=val)
            except ClientForm.AmbiguityError:
                raise ClientForm.ItemNotFoundError('multiple matches to value/label "%s" in list control' % (val,))
            except ClientForm.ItemNotFoundError:
                raise ClientForm.ItemNotFoundError('cannot find value/label "%s" in list control' % (val,))

        if flag:
            item.selected = 1
        else:
            item.selected = 0
    else:
        control.value = val

def _all_the_same_submit(matches):
    """
    Utility function to check to see if a list of controls all really
    belong to the same control: for use with checkboxes, hidden, and
    submit buttons.
    """
    name = None
    value = None
    for match in matches:
        if match.type not in ['submit', 'hidden']:
            return False
        if name is None:
            name = match.name
            value = match.value
        else:
            if match.name != name or match.value!= value:
                return False
    return True

def _all_the_same_checkbox(matches):
    """
    Check whether all these controls are actually the the same
    checkbox.

    Hidden controls can combine with checkboxes, to allow form
    processors to ensure a False value is returned even if user
    does not check the checkbox. Without the hidden control, no
    value would be returned.
    """
    name = None
    for match in matches:
        if match.type not in ['checkbox', 'hidden']:
            return False
        if name is None:
            name = match.name
        else:
            if match.name != name:
                return False
    return True

def unique_match(matches):
    return len(matches) == 1 or \
           _all_the_same_checkbox(matches) or \
           _all_the_same_submit(matches)

#
# stuff to run 'tidy'...
#

_tidy_cmd = ["tidy", "-q", "-ashtml"]
_tidy_exists = True

def run_tidy(html):
    """
    Run the 'tidy' command-line program on the given HTML string.

    Return a 2-tuple (output, errors).  (None, None) will be returned if
    'tidy' doesn't exist or otherwise fails.
    """
    global _tidy_cmd, _tidy_exists

    from commands import _options
    require_tidy = _options.get('require_tidy')

    if not _tidy_exists:
        if require_tidy:
            raise TwillException("tidy does not exist and require_tidy is set")
        return (None, None)
    
    #
    # run the command, if we think it exists
    #
    
    clean_html = None
    if _tidy_exists:
        try:
            process = subprocess.Popen(_tidy_cmd, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, bufsize=0,
                                       shell=False)
        
            (stdout, stderr) = process.communicate(html)

            clean_html = stdout
            errors = stderr
        except OSError:
            _tidy_exists = False

    errors = None
    if require_tidy and clean_html is None:
        raise TwillException("tidy does not exist and require_tidy is set")

    return (clean_html, errors)

class ConfigurableParsingFactory(mechanize.Factory):
    """
    A factory that listens to twill config options regarding parsing.

    First: clean up passed-in HTML using tidy?
    Second: parse using the regular parser, or BeautifulSoup?
    Third: should we fail on, or ignore, parse errors?
    """
    
    def __init__(self):
        self.basic_factory = mechanize.DefaultFactory()
        self.soup_factory = mechanize.RobustFactory()

        self.set_response(None)

    def set_request_class(self, request_class):
        self.basic_factory.set_request_class(request_class)
        self.soup_factory.set_request_class(request_class)

    def set_response(self, response):
        if not response:
            self.factory = None
            self._orig_html = self._html = self._url = None
            return

        ###

        if self.use_BS():
            self.factory = self.soup_factory
        else:
            self.factory = self.basic_factory
        cleaned_response = self._cleanup_html(response)
        self.factory.set_response(cleaned_response)

    def links(self):
        return self.factory.links()
    
    def forms(self):
        return self.factory.forms()

    def get_global_form(self):
        return self.factory.global_form
    global_form = property(get_global_form)

    def _get_title(self):
        return self.factory.title
    title = property(_get_title)

    def _get_encoding(self):
        return self.factory.encoding
    encoding = property(_get_encoding)

    def _get_is_html(self):
        return self.factory.is_html
    is_html = property(_get_is_html)

    def _cleanup_html(self, response):
        response.seek(0)
        self._orig_html = response.read()
        self._url = response.geturl()
        response.seek(0)

        self._html = self._orig_html

        from twill.commands import _options
        use_tidy = _options.get('use_tidy')
        if use_tidy:
            (new_html, errors) = run_tidy(self._html)
            if new_html:
                self._html = new_html

        return mechanize.make_response(self._html, response._headers.items(),
                                       response._url, response.code,
                                       response.msg)
                                       
    def use_BS(self):
        from twill.commands import _options
        flag = _options.get('use_BeautifulSoup')

        return flag

###

class FixedHTTPBasicAuthHandler(mechanize.HTTPBasicAuthHandler):
    """
    Fix a bug that exists through Python 2.4 (but NOT in 2.5!)
    """
    def retry_http_basic_auth(self, host, req, realm):
        user,pw = self.passwd.find_user_password(realm, req.get_full_url())
        # ----------------------------------------------^^^^^^^^^^^^^^^^^^ CTB
        if pw is not None:
            raw = "%s:%s" % (user, pw)
            auth = 'Basic %s' % base64.encodestring(raw).strip()
            if req.headers.get(self.auth_header, None) == auth:
                return None
            req.add_header(self.auth_header, auth)
            return self.parent.open(req)
        else:
            return None
    

###

_debug_print_refresh = False
class FunctioningHTTPRefreshProcessor(HTTPRefreshProcessor):
    """
    Fix an issue where the 'content' component of the http-equiv=refresh
    tag may not contain 'url='.  CTB hack.
    """
    def http_response(self, request, response):
        from twill.commands import OUT, _options
        do_refresh = _options.get('acknowledge_equiv_refresh')
        
        code, msg, hdrs = response.code, response.msg, response.info()

        if code == 200 and hdrs.has_key("refresh") and do_refresh:
            refresh = hdrs.getheaders("refresh")[0]
            
            if _debug_print_refresh:
                print>>OUT, "equiv-refresh DEBUG: code 200, hdrs has 'refresh'"
                print>>OUT, "equiv-refresh DEBUG: refresh header is", refresh
                
            i = refresh.find(";")
            if i != -1:
                pause, newurl_spec = refresh[:i], refresh[i+1:]
                pause = int(pause)

                if _debug_print_refresh:
                    print>>OUT, "equiv-refresh DEBUG: pause:", pause
                    print>>OUT, "equiv-refresh DEBUG: new url:", newurl_spec
                
                j = newurl_spec.find("=")
                if j != -1:
                    newurl = newurl_spec[j+1:]
                else:
                    newurl = newurl_spec

                if _debug_print_refresh:
                    print>>OUT, "equiv-refresh DEBUG: final url:", newurl

                print>>OUT, "Following HTTP-EQUIV=REFRESH to %s" % (newurl,)
                    
                if (self.max_time is None) or (pause <= self.max_time):
                    if pause != 0 and 0:  # CTB hack! ==#  and self.honor_time:
                        time.sleep(pause)
                    hdrs["location"] = newurl
                    # hardcoded http is NOT a bug
                    response = self.parent.error(
                        "http", request, response,
                        "refresh", msg, hdrs)

        return response

    https_response = http_response

####

class HistoryStack(mechanize._mechanize.History):
    def __len__(self):
        return len(self._history)
    def __getitem__(self, i):
        return self._history[i]
    
####

def _is_valid_filename(f):
    return not (f.endswith('~') or f.endswith('.bak') or f.endswith('.old'))

def gather_filenames(arglist):
    """
    Collect script files from within directories.
    """
    l = []

    for filename in arglist:
        if os.path.isdir(filename):
            thislist = []
            for (dirpath, dirnames, filenames) in os.walk(filename):
                for f in filenames:
                    if _is_valid_filename(f):
                        f = os.path.join(dirpath, f)
                        thislist.append(f)
                        
            thislist.sort()
            l.extend(thislist)
        else:
            l.append(filename)

    return l
