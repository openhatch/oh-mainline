API_KEY='JeXHeaQhjXewhdktn4nUw' # "Oman testing"

def ohloh_url2data(url, selector, params = {}, many = False):
    my_params = {'api_key': API_KEY}
    my_params.update(params)
    params = my_params ; del my_params

    ret = []
    
    encoded = urllib.urlencode(params)
    url += encoded
    tree = ET.parse(urllib.urlopen(url))
        
    # Did Ohloh return an error?
    root = tree.getroot()
    if root.find('error') is not None:
        raise ValueError, "Ohloh gave us back an error. Wonder why."

    interestings = root.findall(selector)
    for interesting in interestings:
        this = {}
        for child in interesting.getchildren():
            if child.text:
                this[unicode(child.tag)] = unicode(child.text, 'utf-8')
        ret.append(this)

    if many:
        return ret
    if ret:
        return ret[0]
    return None

from typecheck import accepts, returns
from typecheck import Any as __

import xml.etree.ElementTree as ET
import sys, urllib, hashlib

class Ohloh(object):
    @accepts(object, int)
    def project_id2projectdata(self, project_id):
        url = 'http://www.ohloh.net/projects/%d.xml?' % project_id
        data = ohloh_url2data(url, 'result/project')
        return data
    
    @accepts(object, int)
    def analysis2projectdata(self, analysis_id):
        url = 'http://www.ohloh.net/analyses/%d.xml?' % analysis_id
        data = ohloh_url2data(url, 'result/analysis')

        # Otherwise, get the project name
        proj_id = data['project_id']
        return self.project_id2projectdata(int(proj_id))
        
    def get_contribution_info_by_username(self, username):
        ret = []
        url = 'http://www.ohloh.net/contributors.xml?'
        c_fs = ohloh_url2data(url, 'result/contributor_fact',
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
        url = 'http://www.ohloh.net/contributors.xml?'
        c_fs = ohloh_url2data(url, 'result/contributor_fact',
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

_ohloh = Ohloh()
def get_ohloh():
    return _ohloh
