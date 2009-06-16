API_KEY='JeXHeaQhjXewhdktn4nUw' # "Oman testing"

def ohloh_url2data(url, selector, params = {}):
    my_params = {'api_key': API_KEY}
    my_params.update(params)
    params = my_params ; del my_params
    
    ret = {}
    
    encoded = urllib.urlencode(params)
    url += encoded
    tree = ET.parse(urllib.urlopen(url))
        
    # Did Ohloh return an error?
    root = tree.getroot()
    if root.find('error') is not None:
        raise ValueError, "Ohloh gave us back an error. Wonder why."

    interesting = root.find(selector)
    for child in interesting.getchildren():
        if child.text:
            ret[unicode(child.tag)] = unicode(child.text, 'utf-8')
    return ret

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
    @returns(unicode)
    def analysis2projectname(self, analysis_id):
        url = 'http://www.ohloh.net/analyses/%d.xml?' % analysis_id
        data = ohloh_url2data(url, 'result/analysis')

        # Otherwise, get the project name
        proj_id = data['project_id']
        return self.project_id2projectdata(int(proj_id))['name']
        
    def get_contribution_info_by_username(self, username):
        ret = []
        
        params = urllib.urlencode({'api_key': API_KEY, 'query': username})
        url = 'http://www.ohloh.net/contributors.xml?' + params
        tree = ET.parse(urllib.urlopen(url))

        # Did Ohloh return an error?
        root = tree.getroot()
        if root.find('error') is not None:
            raise ValueError, "Ohloh gave us back an error. Wonder why."

        # For each contributor fact, grab the project it was for
        for c_f in root.findall('result/contributor_fact'):
            eyedee_elt = c_f.find('analysis_id')
            if eyedee_elt is None:
                continue # this contributor fact is useless
            eyedee = int(eyedee_elt.text)
            this = dict(
                project=self.analysis2projectname(eyedee),
                primary_language=c_f.find('primary_language_nice_name').text,
                man_months=int(c_f.find('man_months').text))
            ret.append(this)

        return ret

_ohloh = Ohloh()
def get_ohloh():
    return _ohloh
