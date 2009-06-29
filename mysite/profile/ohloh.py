import xml.etree.ElementTree as ET
import xml.parsers.expat
import sys, urllib, hashlib
import urllib2
import cStringIO as StringIO

def uni_text(s):
    if type(s) == unicode:
        return s
    return s.decode('utf-8')

import lxml.html
import mechanize
import re

from typecheck import accepts, returns
from typecheck import Any as __

API_KEY='0cWqe4uPw7b8Q5337ybPQ' # "Oman testing"

def mechanize_get(url, referrer=None):
    b = mechanize.Browser()
    b.set_handle_robots(False)
    addheaders = [('User-Agent',
                     'Mozilla/4.0 (compatible; MSIE 5.0; Windows 98; (compatible;))')]
    if referrer is not None:
        b.set_handle_referer(False)
        addheaders.extend([('Referer',
                           referrer)])
    b.addheaders = addheaders
    b.open(url)
    return b

def ohloh_url2data(url, selector, params = {}, many = False):
    my_params = {'api_key': API_KEY}
    my_params.update(params)
    params = my_params ; del my_params

    ret = []
    
    encoded = urllib.urlencode(params)
    url += encoded
    b = mechanize_get(url)
    s = b.response()
    try:
        s = b.response().read()
        tree = ET.parse(StringIO.StringIO(s))
    except xml.parsers.expat.ExpatError:
        # well, I'll be. it doesn't parse.
        return b.geturl(), None
        #import pdb
        #pdb.set_trace()
        
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
        return b.geturl(), ret
    if ret:
        return b.geturl(), ret[0]
    return b.geturl(), None

class Ohloh(object):
    def project_id2projectdata(self, project_id=None, project_name=None):
        if project_name is None:
            project_query = str(int(project_id))
        else:
            project_query = str(project_name)
        url = 'http://www.ohloh.net/projects/%s.xml?' % urllib.quote(
            project_query)
        url, data = ohloh_url2data(url, 'result/project')
        return data
    
    def project_name2projectdata(self, project_name_query):
        url = 'http://www.ohloh.net/projects.xml?'
        args = {'query': project_name_query}
        url, data = ohloh_url2data(url, 'result/project', args)
        return data
    
    @accepts(object, int)
    def analysis2projectdata(self, analysis_id):
        url = 'http://www.ohloh.net/analyses/%d.xml?' % analysis_id
        url, data = ohloh_url2data(url, 'result/analysis')

        # Otherwise, get the project name
        proj_id = data['project_id']
        return self.project_id2projectdata(int(proj_id))
        
    def get_contribution_info_by_username(self, username):
        ret = []
        url = 'http://www.ohloh.net/contributors.xml?'
        url, c_fs = ohloh_url2data(url, 'result/contributor_fact',
                              {'query': username}, many=True)

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
        b.open('https://www.ohloh.net/accounts/%s' % urllib.quote(
            ohloh_username))
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
            url, c_fs = ohloh_url2data(url, 'result/contributor_fact', many=True)
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

    def search_contribution_info_by_email(self, email):
        ret = []
        url = 'http://www.ohloh.net/contributors.xml?'
        url, c_fs = ohloh_url2data(url, 'result/contributor_fact',
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
