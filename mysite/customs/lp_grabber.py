import lxml.html # scraper library
from ohloh import mechanize_get
import urllib
import urllib2
import urlparse
import time
import random

def project2languages(project_name):
    """Find the Launchpad URL for the given project. Scrape launchpad page for languages."""
    if project_name.startswith('http://') or project_name.startswith('https://'):
        project_url = project_name
    else:
        # Normalize project name to be lowercase
        project_name = project_name.lower()
        project_url = 'https://launchpad.net/%s' % (
            urllib.quote(project_name))

    # Now grab the project page and parse it
    b = mechanize_get(project_url)
    doc = b.response().read()
    doc_u = unicode(doc, 'utf-8')
    tree = lxml.html.document_fromstring(doc_u)
    try:
        langs_text = tree.cssselect('#programminglang')[0].text_content()
        return map(lambda s: s.strip(), langs_text.split(','))
    except IndexError:
        return []

def get_info_for_launchpad_username(username):
    """This figures out what the named person has been involved with.
    It returns a dictionary like this:
    {
        'F-Spot': {
            'url': 'http://launchpad.net/f-spot',
            'involvement_types': ['Bug Management', 'Bazaar Branches'],
            'languages' : ['python', 'shell script']
        }
    }
    """
    try:
        b = mechanize_get('https://launchpad.net/~%s' % 
                          urllib.quote(username))
    except urllib2.HTTPError, e:
        if str(e.code) == '404':
            return {}
        else:
            raise # not a 404? Bubble-up the explosion.
    doc = b.response().read()
    doc_u = unicode(doc, 'utf-8')
    tree = lxml.html.document_fromstring(doc_u)
    ret = {}
    # Expecting html like this:
    # <table class='contributions'>
    #   <tr>
    #       ...
    #       <img title='Bug Management' />
    for row in tree.cssselect('.contributions tr'):
        project_link = row.cssselect('a')[0]
        project_name = project_link.text_content().strip()
        project_url_relative = project_link.attrib['href']
        project_url = urlparse.urljoin(b.geturl(), project_url_relative)
        
        involvement_types = [i.attrib.get('title', '').strip()
                             for i in row.cssselect('img')]
        languages = project2languages(project_url)
        ret[project_name] = {
                'involvement_types': set([k for k in involvement_types if k]),
                'url': project_url,
                'languages': languages
                }
    return ret

def person_to_bazaar_branch_languages(username):
    user_info = get_info_for_launchpad_username(username)

    langs = []
    for project in user_info:
        if project.endswith('.url'):
            continue
        involvement_types = user_info[project]['involvement_types']
        if 'Bazaar Branches' in involvement_types:
            project_url = user_info[project]['url']
            langs.extend(project2languages(project_url))
    return langs
