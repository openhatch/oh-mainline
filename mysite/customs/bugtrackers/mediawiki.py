import urllib2
import logging
import mechanize
import lxml.etree

import mysite.customs.miro
import mysite.customs.ohloh
import mysite.customs.models
import mysite.search.models
import mysite.customs.bugtrackers.bugzilla_general

QUERY='https://bugzilla.wikimedia.org/buglist.cgi?keywords=easy&query_format=advanced&keywords_type=allwords&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=VERIFIED&resolution=LATER&resolution=---'
BUG_URL_PREFIX = 'https://bugzilla.wikimedia.org/show_bug.cgi?id='

def project_finder_plugin(bug_xml_elt):
    import pdb
    pdb.set_trace()
    import mysite.search.models
    project, _ = mysite.search.models.Project.objects.get_or_create(
        name='Mediawiki whatever')
    return project

def detect_if_good_for_newcomers_plugin(bug_xml_elt, bug_object):
    pass

def get_current_bug_id2bug_objs():
    mysite.customs.bugtrackers.bugzilla_general.query_url2bug_objects(
        BUG_URL_PREFIX=BUG_URL_PREFIX,
        QUERY=QUERY,
        project_finder_plugin=project_finder_plugin,
        detect_if_good_for_newcomers_plugin=detect_if_good_for_newcomers_plugin)

def grab():
    current_bug_id2bug_objs = get_current_bug_id2bug_objs()
    mysite.customs.bugzilla_general.grab(current_bug_id2bug_objs,
                                         BUG_URL_PREFIX=BUG_URL_PREFIX)
                                         
                                         


