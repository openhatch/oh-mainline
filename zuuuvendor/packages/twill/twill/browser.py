"""
Implements TwillBrowser, a simple stateful wrapper for mechanize.Browser.

See _browser.py for mechanize code.
"""

OUT=None

# Python imports
import re

# wwwsearch imports
import _mechanize_dist as mechanize
from _mechanize_dist import BrowserStateError, LinkNotFoundError, ClientForm

# twill package imports
from _browser import PatchedMechanizeBrowser
from utils import print_form, ConfigurableParsingFactory, \
     ResultWrapper, unique_match, HistoryStack
from errors import TwillException
     

#
# TwillBrowser
#

class TwillBrowser(object):
    """
    Wrap mechanize behavior in a simple stateful way.

    Public variables:

      * result -- mechanize-style 'result' object.
    """
    def __init__(self):
        #
        # create special link/forms parsing code to run tidy on HTML first.
        #
        
        factory = ConfigurableParsingFactory()

        #
        # Create the mechanize browser.
        #
        
        b = PatchedMechanizeBrowser(history=HistoryStack(), factory=factory)

        self._browser = b
        
        self.result = None
        self.last_submit_button = None

        #
        # create & set a cookie jar.
        #
        
        policy = mechanize.DefaultCookiePolicy(rfc2965=True)
        cj = mechanize.LWPCookieJar(policy=policy)
        self._browser.set_cookiejar(cj)
        self.cj = cj

        # Ask for MIME type 'text/html' by preference.
        self._browser.addheaders = [("Accept", "text/html, */*")]

        # ignore robots.txt
        self._browser.set_handle_robots(None)

        # create an HTTP auth handler
        self.creds = mechanize.HTTPPasswordMgr()

        # do handle HTTP-EQUIV properly.
        self._browser.set_handle_equiv(True)

        # callables to be called after each page load.
        self._post_load_hooks = []

    ### get/set HTTP authentication stuff.

    def _set_creds(self, creds):
        self._creds = creds
        self._browser.set_password_manager(creds)

    def _get_creds(self):
        return self._creds

    creds = property(_get_creds, _set_creds)
        
    def go(self, url):
        """
        Visit given URL.
        """
        try_urls = [ url, ]

        # if this is an absolute URL that is just missing the 'http://' at
        # the beginning, try fixing that.
        
        if url.find('://') == -1:
            full_url = 'http://%s' % (url,)  # mimic browser behavior
            try_urls.append(full_url)

        # if this is a '?' URL, then assume that we want to tack it onto
        # the end of the current URL.

        if url.startswith('?'):
            current_url = self.get_url()
            current_url = current_url.split('?')[0]
            try_urls = [ current_url + url, ]

        success = False

        for u in try_urls:
            try:
                self._journey('open', u)
                success = True
                break
            except IOError:             # @CTB test this!
                pass

        if success:
            print>>OUT, '==> at', self.get_url()
        else:
            raise BrowserStateError("cannot go to '%s'" % (url,))

    def reload(self):
        """
        Tell the browser to reload the current page.
        """
        self._journey('reload')
        print>>OUT, '==> reloaded'

    def back(self):
        """
        Return to previous page, if possible.
        """
        try:
            self._journey('back')
            print>>OUT, '==> back to', self.get_url()
        except BrowserStateError:
            print>>OUT, '==> back at empty page.'

    def get_code(self):
        """
        Get the HTTP status code received for the current page.
        """
        if self.result:
            return self.result.get_http_code()
        return None

    def get_html(self):
        """
        Get the HTML for the current page.
        """
        if self.result:
            return self.result.get_page()
        return None

    def get_title(self):
        """
        Get content of the HTML title element for the current page.
        """
        return self._browser.title()

    def get_url(self):
        """
        Get the URL of the current page.
        """
        if self.result:
            return self.result.get_url()
        return None

    def find_link(self, pattern):
        """
        Find the first link with a URL, link text, or name matching the
        given pattern.
        """

        #
        # first, try to find a link matching that regexp.
        #
        
        try:
            l = self._browser.find_link(url_regex=pattern)
        except LinkNotFoundError:

            #
            # then, look for a text match.
            #
            
            try:
                l = self._browser.find_link(text_regex=pattern)
            except LinkNotFoundError:
                #
                # finally, look for a name match.
                #
                
                try:
                    l = self._browser.find_link(name_regex=pattern)
                except LinkNotFoundError:
                    l = None

        return l

    def follow_link(self, link):
        """
        Follow the given link.
        """
        self._journey('follow_link', link)
        print>>OUT, '==> at', self.get_url()

    def set_agent_string(self, agent):
        """
        Set the agent string to the given value.
        """
        for i in xrange(len(self._browser.addheaders)):
            if self._browser.addheaders[i][0] == "User-agent":
                del self._browser.addheaders[i]
                break
        self._browser.addheaders += [("User-agent", agent)]

    def showforms(self):
        """
        Pretty-print all of the forms.  Include the global form (form
        elements outside of <form> pairs) as forms[0] iff present.
        """
        forms = self.get_all_forms()
        
        for n, f in enumerate(forms):
            print_form(n, f, OUT)

    def showlinks(self):
        """
        Pretty-print all of the links.
        """
        print>>OUT, 'Links:\n'
        for n, link in enumerate(self._browser.links()):
            print>>OUT, "%d. %s ==> %s" % (n, link.text, link.url,)
        print>>OUT, ''

    def showhistory(self):
        """
        Pretty-print the history of links visited.
        """
        print>>OUT, ''
        print>>OUT, 'History: (%d pages total) ' % (len(self._browser._history))

        n = 1
        for (req, resp) in self._browser._history:
            if req and resp:            # only print those that back() will go
                print>>OUT, "\t%d. %s" % (n, resp.geturl())
                n += 1
            
        print>>OUT, ''

    def get_all_forms(self):
        """
        Return a list of all of the forms, with global_form at index 0
        iff present.
        """
        global_form = self._browser.global_form()
        forms = list(self._browser.forms())

        if global_form.controls:
            forms.insert(0, global_form)
            
        return forms

    def get_form(self, formname):
        """
        Return the first form that matches 'formname'.
        """
        formname = str(formname)
        
        forms = self.get_all_forms()
        
        # first try ID
        for f in forms:
            id = f.attrs.get("id")
            if id and str(id) == formname:
                return f
        
        # next try regexps
        regexp = re.compile(formname)
        for f in forms:
            if f.name and regexp.search(f.name):
                return f

        # ok, try number
        try:
            formnum = int(formname)
            if formnum >= 1 and formnum <= len(forms):
                return forms[formnum - 1]
        except ValueError:              # int() failed
            pass
        except IndexError:              # formnum was incorrect
            pass

        return None

    def get_form_field(self, form, fieldname):
        """
        Return the control that matches 'fieldname'.  Must be
        a *unique* regexp/exact string match.
        """
        fieldname = str(fieldname)
        
        found = None
        found_multiple = False

        matches = [ c for c in form.controls if str(c.id) == fieldname ]

        # test exact match.
        if matches:
            if unique_match(matches):
                found = matches[0]
            else:
                found_multiple = True   # record for error reporting.
        
        matches = [ c for c in form.controls if str(c.name) == fieldname ]

        # test exact match.
        if matches:
            if unique_match(matches):
                found = matches[0]
            else:
                found_multiple = True   # record for error reporting.

        # test index.
        if found is None:
            # try num
            clickies = [c for c in form.controls]
            try:
                fieldnum = int(fieldname) - 1
                found = clickies[fieldnum]
            except ValueError:          # int() failed
                pass
            except IndexError:          # fieldnum was incorrect
                pass

        # test regexp match
        if found is None:
            regexp = re.compile(fieldname)

            matches = [ ctl for ctl in form.controls \
                        if regexp.search(str(ctl.name)) ]

            if matches:
                if unique_match(matches):
                    found = matches[0]
                else:
                    found_multiple = True # record for error

        if found is None:
            # try value, for readonly controls like submit keys
            clickies = [ c for c in form.controls if c.value == fieldname \
                         and c.readonly ]
            if clickies:
                if len(clickies) == 1:
                    found = clickies[0]
                else:
                    found_multiple = True   # record for error

        # error out?
        if found is None:
            if not found_multiple:
                raise TwillException('no field matches "%s"' % (fieldname,))
            else:
                raise TwillException('multiple matches to "%s"' % (fieldname,))

        return found

    def clicked(self, form, control):
        """
        Record a 'click' in a specific form.
        """
        if self._browser.form != form:
            # construct a function to choose a particular form; select_form
            # can use this to pick out a precise form.

            def choose_this_form(test_form, this_form=form):
                if test_form is this_form:
                    return True

                return False

            self._browser.select_form(predicate=choose_this_form)
            assert self._browser.form == form

            self.last_submit_button = None

        # record the last submit button clicked.
        if isinstance(control, ClientForm.SubmitControl):
            self.last_submit_button = control

    def submit(self, fieldname=None):
        """
        Submit the currently clicked form using the given field.
        """
        if fieldname is not None:
            fieldname = str(fieldname)
        
        if not self.get_all_forms():
            raise TwillException("no forms on this page!")
        
        ctl = None
        
        form = self._browser.form
        if form is None:
            forms = [ i for i in self.get_all_forms() ]
            if len(forms) == 1:
                form = forms[0]
            else:
                raise TwillException("""\
more than one form; you must select one (use 'fv') before submitting\
""")

        # no fieldname?  see if we can use the last submit button clicked...
        if not fieldname:
            if self.last_submit_button:
                ctl = self.last_submit_button
            else:
                # get first submit button in form.
                submits = [ c for c in form.controls \
                            if isinstance(c, ClientForm.SubmitControl) ]

                if len(submits):
                    ctl = submits[0]
                
        else:
            # fieldname given; find it.
            ctl = self.get_form_field(form, fieldname)

        #
        # now set up the submission by building the request object that
        # will be sent in the form submission.
        #
        
        if ctl:
            # submit w/button
            print>>OUT, """\
Note: submit is using submit button: name="%s", value="%s"
""" % (ctl.name, ctl.value)
            
            if isinstance(ctl, ClientForm.ImageControl):
                request = ctl._click(form, (1,1), "", mechanize.Request)
            else:
                request = ctl._click(form, True, "", mechanize.Request)
                
        else:
            # submit w/o submit button.
            request = form._click(None, None, None, None, 0, None,
                                  "", mechanize.Request)

        #
        # add referer information.  this may require upgrading the
        # request object to have an 'add_unredirected_header' function.
        #

        upgrade = self._browser._ua_handlers.get('_http_request_upgrade')
        if upgrade:
            request = upgrade.http_request(request)
            request = self._browser._add_referer_header(request)

        #
        # now actually GO.
        #
        
        self._journey('open', request)

    def save_cookies(self, filename):
        """
        Save cookies into the given file.
        """
        self.cj.save(filename, ignore_discard=True, ignore_expires=True)

    def load_cookies(self, filename):
        """
        Load cookies from the given file.
        """
        self.cj.load(filename, ignore_discard=True, ignore_expires=True)

    def clear_cookies(self):
        """
        Delete all of the cookies.
        """
        self.cj.clear()

    def show_cookies(self):
        """
        Pretty-print all of the cookies.
        """
        print>>OUT, '''
There are %d cookie(s) in the cookiejar.
''' % (len(self.cj,))
        
        if len(self.cj):
            for cookie in self.cj:
                print>>OUT, '\t', cookie

            print>>OUT, ''

    #### private functions.

    def _journey(self, func_name, *args, **kwargs):
        """
        'func_name' should be the name of a mechanize method that either
        returns a 'result' object or raises a HTTPError, e.g.
        one of 'open', 'reload', 'back', or 'follow_link'.

        journey then runs that function with the given arguments and turns
        the results into a nice friendly standard ResultWrapper object, which
        is stored as 'self.result'.

        All exceptions other than HTTPError are unhandled.
        
        (Idea stolen straight from PBP.)
        """
        # reset
        self.last_submit_button = None
        self.result = None

        func = getattr(self._browser, func_name)
        try:
            r = func(*args, **kwargs)
        except mechanize.HTTPError, e:
            r = e

        # seek back to 0 if a seek() function is present.
        seek_fn = getattr(r, 'seek', None)
        if seek_fn:
            seek_fn(0)

        # some URLs, like 'file:' URLs, don't have return codes.  In this
        # case, assume success (code=200) if no such attribute.
        code = getattr(r, 'code', 200)

        ## special case refresh loops!?
        if code == 'refresh':
            raise TwillException("""\
infinite refresh loop discovered; aborting.
Try turning off acknowledge_equiv_refresh...""")

        self.result = ResultWrapper(code, r.geturl(), r.read())

        #
        # Now call all of the post load hooks with the function name.
        #
        
        for callable in self._post_load_hooks:
            callable(func_name, *args, **kwargs)
