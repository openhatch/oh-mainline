API_KEY='JeXHeaQhjXewhdktn4nUw' # "Oman testing"

from typecheck import accepts, returns
from typecheck import Any as __

import xml.etree.ElementTree as ET
import sys, urllib, hashlib

class Ohloh(object):
    @accepts(object, int)
    @returns(unicode)
    def project_id2projectname(self, project_id):
        pass
        params = urllib.urlencode({'api_key': API_KEY})
        url = 'http://www.ohloh.net/projects/%d.xml?' % project_id
        url += params
        print url
        tree = ET.parse(urllib.urlopen(url))
        
        # Did Ohloh return an error?
        root = tree.getroot()
        if root.find('error') is not None:
            raise ValueError, "Ohloh gave us back an error. Wonder why."

        # Otherwise, get the project name
        return unicode(root.find('result/project/name').text)
    
    @accepts(object, int)
    @returns(unicode)
    def analysis2projectname(self, analysis_id):
        params = urllib.urlencode({'api_key': API_KEY})
        url = 'http://www.ohloh.net/analyses/%d.xml?' % analysis_id
        url += params
        tree = ET.parse(urllib.urlopen(url))

        # Did Ohloh return an error?
        root = tree.getroot()
        if root.find('error') is not None:
            raise ValueError, "Ohloh gave us back an error. Wonder why."

        # Otherwise, get the project name
        proj_id = tree.find('project_id')[0].text
        return self.project_id2projectname(int(proj_id))
        
    def get_project_set_by_username(self, username):
        ret = set()
        
        params = urllib.urlencode({'api_key': API_KEY, 'query': username})
        url = 'http://www.ohloh.net/contributors.xml?' + params
        tree = ET.parse(urllib.urlopen(url))

        # Did Ohloh return an error?
        root = tree.getroot()
        if root.find('error') is not None:
            raise ValueError, "Ohloh gave us back an error. Wonder why."

        # For each contributor fact, grab the project it was for
        for c_f in root.find('contributor_fact'):
            analysis_id = c_f.find('analysis_id')[0].text
            ret.add(self.analysis2projectname(analysis_id))
        return ret

_ohloh = Ohloh()
def get_ohloh():
    return _ohloh
