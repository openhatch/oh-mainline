# vim: set columns=80:
import os
import datetime
import csv

import simplejson
import datetime
import glob
import lxml
from .search.models import Project, Bug
import codecs

def get_tag_text_from_xml(xml_doc, tag_name, index = 0):
    tags = xml_doc.xpath('//' + tag_name)
    try:
        return tags[index].text
    except IndexError:
        return ''
    assert False, "You should not get here."

def count_people_involved(xml_doc):
    # Strategy: Create a set of all the listed text values
    # inside a <who ...>(text)</who> tag
    # Return the length of said set.
    everyone = [tag.text for tag in xml_doc.xpath('//who')]
    return len(set(everyone))

def bugzilla_date_to_datetime(date_string):
    # FIXME: I make guesses as to the timezone.
    try:
        ret = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M')
    except ValueError:
        ret = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    return ret

def who_tag_to_username_and_realname(who_tag):
    username = who_tag.text
    realname = who_tag.attrib['name']
    return username, realname

def xml2bug_object(xml_fd):
    parsed = lxml.etree.parse(xml_fd)
    date_reported_text = get_tag_text_from_xml(parsed, 'creation_ts')
    last_touched_text = get_tag_text_from_xml(parsed, 'delta_ts')
    u, r = who_tag_to_username_and_realname(parsed.xpath('//who')[0])
    bug_id = int(get_tag_text_from_xml(parsed, 'bug_id'))
    keywords_text = get_tag_text_from_xml(parsed, 'keywords')
    keywords = map(lambda s: s.strip(),
                   keywords_text.split(','))
    project, _ = Project.objects.get_or_create(name='Miro')

    ret = Bug(
        project = project,
        title = get_tag_text_from_xml(parsed, 'short_desc'),
        description = get_tag_text_from_xml(parsed, 'long_desc/thetext'),
        status = get_tag_text_from_xml(parsed, 'bug_status'),
        importance = get_tag_text_from_xml(parsed, 'bug_severity'),
        people_involved = count_people_involved(parsed),
        date_reported = bugzilla_date_to_datetime(date_reported_text),
        last_touched = bugzilla_date_to_datetime(last_touched_text),
        last_polled = datetime.datetime.now(),
        submitter_username = u,
        submitter_realname = r,
        canonical_bug_link = 'http://bugzilla.pculture.org/show_bug.cgi?id=%d' % bug_id,
        good_for_newcomers = ('bitesized' in keywords))
    return ret

def bugzilla_query_to_bug_ids(csv_fd):
    doc = csv.reader(csv_fd)
    doc.next() # throw away header row

    bugs = []
    
    for row in doc:
        bugs.append(int(row[0]))

    return bugs
