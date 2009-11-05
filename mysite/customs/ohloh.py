import xml.etree.ElementTree as ET
import xml.parsers.expat
import sys, urllib, hashlib
import urllib2
import cStringIO as StringIO
from urlparse import urlparse
from urllib2 import HTTPError
from django.conf import settings
import mysite.customs.models

def uni_text(s):
    if type(s) == unicode:
        return s
    return s.decode('utf-8')

import lxml.html
import mechanize
import re

from typecheck import accepts, returns
from typecheck import Any as __

def mechanize_get(url, referrer=None, attempts_remaining=6, person=None):
    """Input: Some stuff regarding a web URL to request.
    Output: A browser instance that just open()'d that, plus an unsaved
    WebResponse object representing that browser's final state."""
    web_response = mysite.customs.models.WebResponse()

    b = mechanize.Browser()
    b.set_handle_robots(False)
    addheaders = [('User-Agent',
                     'Mozilla/4.0 (compatible; MSIE 5.0; Windows 98; (compatible;))')]
    if referrer is not None:
        b.set_handle_referer(False)
        addheaders.extend([('Referer',
                           referrer)])
    b.addheaders = addheaders
    try:
        b.open(url)
    except HTTPError, e:
        # FIXME: Test with mock object.
        if e.code == 504 and attempts_remaining > 0:
            message_schema = "Tried to talk to %s, got 504, retrying %d more times..."

            long_message = message_schema % (url, attempts_remaining)
            print >> sys.stderr, long_message

            if person:
                short_message = message_schema % (urlparse(url).hostname, attempts_remaining)
                person.user.message_set.create(message=short_message)
            return mechanize_get(url, referrer, attempts_remaining-1, person)
        else:
            raise

    return b

def ohloh_url2data(url, selector, params = {}, many = False, API_KEY = None, person=None):
    '''Input: A URL to get,
    a bunch of parameters to toss onto the end url-encoded,
    many (a boolean) indicating if we should return a list of just one datum,
    API_KEY suggesting a key to use with Ohloh, and a
    Person object to, if the request is slow, log messages to.

    Output: A list/dictionary of Ohloh data plus a saved WebResponse instance that
    logs information about the request.'''

    if API_KEY is None:
        API_KEY = settings.OHLOH_API_KEY


    my_params = {'api_key': API_KEY}
    my_params.update(params)
    params = my_params ; del my_params

    # FIXME: We return more than just "ret" these days! Rename this variable.
    ret = []
    
    encoded = urllib.urlencode(params)
    url += encoded
    try:
        b = mechanize_get(url, person)
        web_response = mysite.customs.models.WebResponse.create_from_browser(b)
        web_response.save() # Always save the WebResponse, even if we don't know
        # that any other object will store a pointer here.
    except urllib2.HTTPError, e:
        # FIXME: Also return a web_response for error cases
        if str(e.code) == '404':
            if many:
                return [], None
            return {}, None
        else:
            raise

    try:
        s = web_response.text
        tree = ET.parse(StringIO.StringIO(s))
    except xml.parsers.expat.ExpatError:
        # well, I'll be. it doesn't parse.
        return None, web_response
        
    # Did Ohloh return an error?
    root = tree.getroot()
    if root.find('error') is not None:
        raise ValueError, "Ohloh gave us back an error. Wonder why."

    interestings = root.findall(selector)
    for interesting in interestings:
        this = {}
        for child in interesting.getchildren():
            if child.text:
                this[unicode(child.tag)] = uni_text(child.text)
        ret.append(this)

    if many:
        return ret, web_response
    if ret:
        return ret[0], web_response
    return None, web_response

class Ohloh(object):

    def get_latest_project_analysis_id(self, project_name):
        """ Retrieve from Ohloh.net the latest project
        analysis id for a given project."""
        # {{{
        url = 'https://www.ohloh.net/p/%s/analyses/latest.xml?' % urllib.quote(
                project_name)
        data, web_response = ohloh_url2data(url, 'result/analysis')
        return int(data['id'])
        # }}}

    def project_id2projectdata(self, project_id=None, project_name=None):
        if project_name is None:
            project_query = str(int(project_id))
        else:
            project_query = str(project_name)
        url = 'http://www.ohloh.net/projects/%s.xml?' % urllib.quote(
            project_query)
        data, web_response = ohloh_url2data(url=url, selector='result/project')
        return data
    
    def project_name2projectdata(self, project_name_query):
        url = 'http://www.ohloh.net/projects.xml?'
        args = {'query': project_name_query}
        data, web_response = ohloh_url2data(url=url, selector='result/project',
                                   params=args, many=True)
        # Sometimes when we search Ohloh for e.g. "Debian GNU/Linux", the project it gives
        # us back as the top-ranking hit for full-text relevance is "Ubuntu GNU/Linux." So here
        # we see if the project dicts have an exact match by project name.

        if not data:
            return None # If there is no matching project possibilit at all, get out now.

        exact_match_on_project_name = [ datum for datum in data
                                        if datum.get('name', None).lower() == project_name_query.lower()]
        if exact_match_on_project_name:
            # If there's an exact match on the project name, return this datum
            return exact_match_on_project_name[0]

        # Otherwise, trust Ohloh's full-text relevance ranking and return the first hit
        return data[0]
    
    @accepts(object, int)
    def analysis2projectdata(self, analysis_id):
        url = 'http://www.ohloh.net/analyses/%d.xml?' % analysis_id
        data, web_response = ohloh_url2data(url=url, selector='result/analysis')

        # Otherwise, get the project name
        proj_id = data['project_id']
        return self.project_id2projectdata(int(proj_id))
        
    def get_contribution_info_by_username(self, username, person=None):
        '''Input: A username. We go out and ask Ohloh, "What repositories
        have you indexed where that username was a committer?"
        Optional: a Person model, which is used to log messages to the user
        in case Ohloh is being slow.

        Output: A list of ContributorFact dictionaries, plus an instance (unsaved)
        of the WebResponse class, which stores raw information on the response
        such as the response data and HTTP status.'''
        data = []
        url = 'http://www.ohloh.net/contributors.xml?'
        c_fs, web_response = ohloh_url2data(
            url=url, selector='result/contributor_fact', 
            params={'query': username}, many=True, person=person)

        # For each contributor fact, grab the project it was for
        for c_f in c_fs:
            if 'analysis_id' not in c_f:
                continue # this contributor fact is useless
            eyedee = int(c_f['analysis_id'])
            project_data = self.analysis2projectdata(eyedee)
            this = dict(
                project=project_data['name'],
                project_homepage_url=project_data.get('homepage_url', None),
                primary_language=c_f['primary_language_nice_name'],
                man_months=int(c_f['man_months']))
            data.append(this)

        return data, web_response

    def get_name_by_username(self, username):
        url = 'https://www.ohloh.net/accounts/%s.xml?' % urllib.quote(username)
        account_info, web_response = ohloh_url2data(url, 'result/account')
        if 'name' in account_info:
            return account_info['name']
        raise ValueError

    def get_contribution_info_by_username_and_project(self, project, username):
        ret = []
        url = 'http://www.ohloh.net/p/%s/contributors.xml?' % project
        c_fs, web_response = ohloh_url2data(url, 'result/contributor_fact',
                                   {'query': username}, many=True)

        # Filter these guys down and be sure to only return the ones
        # where contributor_name==username
        for c_f in c_fs:
            if 'analysis_id' not in c_f:
                continue # this contributor fact is useless
            eyedee = int(c_f['analysis_id'])
            project_data = self.analysis2projectdata(eyedee)
            this = dict(
                project=project_data['name'],
                project_homepage_url=project_data.get('homepage_url', None),
                primary_language=c_f['primary_language_nice_name'],
                man_months=int(c_f['man_months']))
            ret.append(this)

        return ret

    def get_contribution_info_by_email(self, email):
        ret = []
        ret.extend(self.search_contribution_info_by_email(email))
        ret.extend(self.get_contribution_info_by_ohloh_username(
            self.email_address_to_ohloh_username(email)))
        return ret

    def email_address_to_ohloh_username(self, email):
        hasher = hashlib.md5(); hasher.update(email)
        hashed = hasher.hexdigest()
        url = 'https://www.ohloh.net/accounts/%s' % urllib.quote(hashed)
        try:
            b = mechanize_get(url)
        except urllib2.HTTPError:
            # well, it failed. get outta here
            return None
            
        parsed = lxml.html.parse(b.response()).getroot()
        one, two = parsed.cssselect('h1 a')[0], parsed.cssselect('a.avatar')[0]
        href1, href2 = one.attrib['href'], two.attrib['href']
        assert href1 == href2
        parts = filter(lambda s: bool(s), href1.split('/'))
        assert len(parts) == 2
        assert parts[0] == 'accounts'
        username = parts[1]
        return username

    def get_contribution_info_by_ohloh_username(self, ohloh_username):
        if ohloh_username is None:
            return []

        b = mechanize.Browser()
        b.set_handle_robots(False)
        b.addheaders = [('User-Agent',
                        'Mozilla/4.0 (compatible; MSIE 5.0; Windows 98; (compatible;))')]
        try:
            b.open('https://www.ohloh.net/accounts/%s' % urllib.quote(
            ohloh_username))
        except urllib2.HTTPError, e:
            if str(e.code) == '404':
                return []
            else:
                raise
        root = lxml.html.parse(b.response()).getroot()
        relevant_links = root.cssselect('a.position')
        relevant_hrefs = [link.attrib['href'] for link in relevant_links]
        relevant_project_and_contributor_id_pairs = []
        # FIXME: do more logging here someday?
        for href in relevant_hrefs:
            project, contributor_id = re.split('[/][a-z]+[/]', href, 1
                                               )[1].split('/contributors/')
            relevant_project_and_contributor_id_pairs.append(
                (project, int(contributor_id)))

        ret = []
        
        for (project, contributor_id) in relevant_project_and_contributor_id_pairs:
            url = 'https://www.ohloh.net/p/%s/contributors/%d.xml?' % (
                urllib.quote(project), contributor_id)
            c_fs, web_response = ohloh_url2data(url, 'result/contributor_fact', many=True)
            # For each contributor fact, grab the project it was for
            for c_f in c_fs:
                if 'analysis_id' not in c_f:
                    continue # this contributor fact is useless
                eyedee = int(c_f['analysis_id'])
                project_data = self.analysis2projectdata(eyedee)
                this = dict(
                    project=project_data['name'],
                    project_homepage_url=project_data.get('homepage_url', None),
                    primary_language=c_f.get(
                        'primary_language_nice_name',''),
                    man_months=int(c_f.get('man_months',0)))
                ret.append(this)
        return ret

    def search_contribution_info_by_email(self, email):
        ret = []
        url = 'http://www.ohloh.net/contributors.xml?'
        c_fs, web_response = ohloh_url2data(url, 'result/contributor_fact',
                              {'query': email}, many=True)

        # For each contributor fact, grab the project it was for
        for c_f in c_fs:
            if 'analysis_id' not in c_f:
                continue # this contributor fact is useless
            eyedee = int(c_f['analysis_id'])
            project_data = self.analysis2projectdata(eyedee)
            this = dict(
                project=project_data['name'],
                project_homepage_url=project_data.get('homepage_url', None),
                primary_language=c_f['primary_language_nice_name'],
                man_months=int(c_f['man_months']))
            ret.append(this)

        return ret

    def get_icon_for_project(self, project):
        try:
            return self.get_icon_for_project_by_id(project)
        except ValueError:
            return self.get_icon_for_project_by_human_name(project)

    def get_icon_for_project_by_human_name(self, project):
        """@param project: the name of a project."""
        # Do a real search to find the project
        try:
            data = self.project_name2projectdata(project)
        except urllib2.HTTPError, e:
            raise ValueError
        try:
            med_logo = data['medium_logo_url']
        except TypeError:
            raise ValueError, "Ohloh gave us back nothing."
        except KeyError:
            raise ValueError, "The project exists, but Ohloh knows no icon."
        # The URL is often something like s3.amazonws.com/bits.ohloh.net/...
        # But sometimes Ohloh has a typo in their URLs.
        if '/bits.ohloh.net/' not in med_logo:
            med_logo = med_logo.replace('attachments/',
                                        'bits.ohloh.net/attachments/')
        b = mechanize_get(med_logo)
        return b.response().read()
        

    def get_icon_for_project_by_id(self, project):
        try:
            data = self.project_id2projectdata(project_name=project)
        except urllib2.HTTPError, e:
            raise ValueError
        try:
            med_logo = data['medium_logo_url']
        except KeyError:
            raise ValueError, "The project exists, but Ohloh knows no icon."
        if '/bits.ohloh.net/' not in med_logo:
            med_logo = med_logo.replace('attachments/',
                                        'bits.ohloh.net/attachments/')
        b = mechanize_get(med_logo)
        return b.response().read()
        
_ohloh = Ohloh()
def get_ohloh():
    return _ohloh

# vim: set nu:
