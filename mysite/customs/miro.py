# vim: set columns=80:
import os
import datetime
import csv
import urllib2

import mysite.base.helpers

import simplejson
import datetime
import glob
import lxml
from ..search.models import Project, Bug
import codecs
import dateutil.parser

def get_tag_text_from_xml(xml_doc, tag_name, index = 0):
    """Given an object representing <bug><tag>text</tag></bug>,
    and tag_name = 'tag', returns 'text'."""
    tags = xml_doc.xpath(tag_name)
    try:
        return tags[index].text
    except IndexError:
        return ''
    assert False, "You should not get here."

def count_people_involved(xml_doc):
    """Strategy: Create a set of all the listed text values
    inside a <who ...>(text)</who> tag
    Return the length of said set."""
    everyone = [tag.text for tag in xml_doc.xpath('.//who')]
    return len(set(everyone))

def bugzilla_date_to_datetime(date_string):
    return mysite.base.helpers.string2naive_datetime(date_string)

def who_tag_to_username_and_realname(who_tag):
    username = who_tag.text
    realname = who_tag.attrib.get('name', '')
    return username, realname

def xml2bug_object(xml_fd,
                   canonical_bug_link_format_string=
                   'http://bugzilla.pculture.org/show_bug.cgi?id=%d'):
    """xml fd: xml file descriptor 'containing' information about one bug"""
    parsed = lxml.etree.parse(xml_fd)
    gen_miro_project = lambda x: Project.objects.get_or_create(name='Miro')[0]
    bug_elt, = parsed.xpath('bug') # The comma asserts that the xpath() returns a list of length 1
    return bug_elt2bug_object(bug_elt, canonical_bug_link_format_string, gen_miro_project)

def bug_elt2bug_dict(parsed, canonical_bug_link_format_string,
                       gen_project):
    date_reported_text = get_tag_text_from_xml(parsed, 'creation_ts')
    last_touched_text = get_tag_text_from_xml(parsed, 'delta_ts')
    u, r = who_tag_to_username_and_realname(parsed.xpath('.//reporter')[0])
    bug_id = int(get_tag_text_from_xml(parsed, 'bug_id'))
    keywords_text = get_tag_text_from_xml(parsed, 'keywords')
    keywords = map(lambda s: s.strip(),
                   keywords_text.split(','))
    project = gen_project(parsed)
    status = get_tag_text_from_xml(parsed, 'bug_status')
    looks_closed = status in ('RESOLVED', 'WONTFIX', 'CLOSED', 'ASSIGNED')

    ret = dict(
        project = project,
        title = get_tag_text_from_xml(parsed, 'short_desc'),
        description = (get_tag_text_from_xml(parsed, 'long_desc/thetext') or
                       '(Empty description)'),
        status = status,
        importance = get_tag_text_from_xml(parsed, 'bug_severity'),
        people_involved = count_people_involved(parsed),
        date_reported = bugzilla_date_to_datetime(date_reported_text),
        last_touched = bugzilla_date_to_datetime(last_touched_text),
        last_polled = datetime.datetime.now(),
        submitter_username = u,
        submitter_realname = r,
        canonical_bug_link = canonical_bug_link_format_string % bug_id,
        good_for_newcomers = ('bitesized' in keywords),
        looks_closed=looks_closed)
    return ret

def bug_elt2bug_object(parsed, canonical_bug_link_format_string,
                       gen_project):
    ret = Bug()
    data = bug_elt2bug_dict(parsed, canonical_bug_link_format_string, gen_project)
    for key in data:
        setattr(ret, key, data[key])
    return ret

def bugzilla_query_to_bug_ids(csv_fd):
    doc = csv.reader(csv_fd)
    try:
        doc.next() # throw away header row
    except StopIteration:
        return []

    bug_ids = []
    
    for row in doc:
        bug_ids.append(int(row[0]))

    return bug_ids

def link2bug_id(url):
    first, rest = url.split('?id=')
    return int(rest)

def bitesized_bugs_csv_fd():
    csv_url = 'http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized&ctype=csv'
    csv_fd = urllib2.urlopen(csv_url)
    return csv_fd

def open_xml_url(xml_url):
    return urllib2.urlopen(xml_url)
    
def grab_miro_bugs():
    '''Input: Nothing.

    Side-effect: Loops over the Miro bitesized bugs (in the Miro bug tracker) and stores/updates them in our DB.'''
    csv_fd = bitesized_bugs_csv_fd()

    old_bitesized_bugs = Bug.all_bugs.filter(canonical_bug_link__startswith='http://bugzilla.pculture.org/')
    old_bitesized_bug_ids = [link2bug_id(k.canonical_bug_link) for k in old_bitesized_bugs]
    
    current_bitesized_bug_ids  = bugzilla_query_to_bug_ids(csv_fd)

    bug_ids = current_bitesized_bug_ids + old_bitesized_bug_ids

    for bug_id in bug_ids:
        xml_url = 'http://bugzilla.pculture.org/show_bug.cgi?ctype=xml&id=%d' % bug_id
        xml_fd = open_xml_url(xml_url)
        bug = xml2bug_object(xml_fd)

        # If there is already a bug with this canonical_bug_link in the DB, just delete it.
        bugs_this_one_replaces = Bug.all_bugs.filter(canonical_bug_link=
                                                    bug.canonical_bug_link)
        for delete_me in bugs_this_one_replaces:
            delete_me.delete()

        # With the coast clear, we save the bug we just extracted from the Miro tracker.
        bug.save()
