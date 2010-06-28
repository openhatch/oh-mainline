import csv
import datetime

import lxml.etree

import mysite.base.helpers
from mysite.base.decorators import cached_property
import mysite.customs.ohloh

def find_ctype_xml_form_number(forms):
    for n, form in enumerate(forms):
        try:
            value = form.get_value('ctype')
            if value == 'xml':
                return n
        except:
            pass
    raise ValueError, "Could not find the right form."

def url2bug_data(url):
    # If we are looking at a single bug then get the XML link
    if url.find('show_bug.cgi?id=') >= 0:
        b = mysite.customs.ohloh.mechanize_get(
                url + '&ctype=xml')
    else:
        # We are looking at a page of bugs.

        # Get the page of bugs
        b = mysite.customs.ohloh.mechanize_get(url)

        # Find the one form with ctype XML
        ctype_xml_form_no = find_ctype_xml_form_number(b.forms())

        # Click ze button
        b.select_form(nr=ctype_xml_form_no)
        b.submit()

    # Get a bunch of XML back
    bug_data = lxml.etree.XML(b.response().read())

    # Return bunch of XML
    return bug_data

def tracker_bug2bug_ids(tracker_bug_url):
    b = mysite.customs.ohloh.mechanize_get(tracker_bug_url)
    xml = lxml.etree.XML(b.response().read())
    depends = xml.findall('bug/dependson')
    depends_bug_ids = [int(depend.text) for depend in depends]
    return depends_bug_ids

def get_tag_text_from_xml(xml_doc, tag_name, index = 0):
    """Given an object representing <bug><tag>text</tag></bug>,
    and tag_name = 'tag', returns 'text'."""
    tags = xml_doc.xpath(tag_name)
    try:
        return tags[index].text
    except IndexError:
        return ''
    assert False, "You should not get here."

class BugzillaBug:
    @staticmethod
    def from_url(url):
        base, ending = url.rsplit('/', 1)
        show_bug, num = ending.rsplit('=', 1)
        bug_id = int(num)
        assert show_bug == 'show_bug.cgi?id'
        return BugzillaBug(bug_id=bug_id,
                           BASE_URL=base + '/')

    def __init__(self, BASE_URL, bug_id=None, bug_data=None):
        self._bug_specific_xml_data = bug_data
        # If bug_id is not provided, try to extract it from bug_data
        if bug_id is None:
            if self._bug_specific_xml_data is not None:
                self.bug_id = self._bug_id_from_bug_data()
            else:
                raise ValueError("bug_id must not be None if bug_data is None")
        else:
            self.bug_id = int(bug_id)
        if not BASE_URL.endswith('/'):
            BASE_URL += '/'
        self.BASE_URL = BASE_URL

    def _bug_id_from_bug_data(self):
        return int(get_tag_text_from_xml(self.get_bug_xml_data(), 'bug_id'))

    @staticmethod
    def _who_tag_to_username_and_realname(who_tag):
        username = who_tag.text
        realname = who_tag.attrib.get('name', '')
        return username, realname

    @cached_property
    def product(self):
        return get_tag_text_from_xml(self.get_bug_xml_data(), 'product')

    @cached_property
    def component(self):
        return get_tag_text_from_xml(self.get_bug_xml_data(), 'component')

    def as_bug_specific_url(self):
        return self.BASE_URL + 'show_bug.cgi?id=%d' % self.bug_id

    def get_bug_xml_data(self):
        # BugzillaBug object could have been created with or without data.
        # So if no bug data in object, fill first before returning.
        if self._bug_specific_xml_data is None:
            self._bug_specific_xml_data = url2bug_data(self.as_bug_specific_url()).xpath('bug')[0]
        return self._bug_specific_xml_data

    @staticmethod
    def bugzilla_count_people_involved(xml_doc):
        """Strategy: Create a set of all the listed text values
        inside a <who ...>(text)</who> tag
        Return the length of said set."""
        everyone = [tag.text for tag in xml_doc.xpath('.//who')]
        return len(set(everyone))

    @staticmethod
    def bugzilla_date_to_datetime(date_string):
        return mysite.base.helpers.string2naive_datetime(date_string)

    def as_data_dict_for_bug_object(self, extract_tracker_specific_data):
        xml_data = self.get_bug_xml_data()

        date_reported_text = get_tag_text_from_xml(xml_data, 'creation_ts')
        last_touched_text = get_tag_text_from_xml(xml_data, 'delta_ts')
        u, r = self._who_tag_to_username_and_realname(xml_data.xpath('.//reporter')[0])
        status = get_tag_text_from_xml(xml_data, 'bug_status')
        looks_closed = status in ('RESOLVED', 'WONTFIX', 'CLOSED', 'ASSIGNED')

        ret_dict = {
            'title': get_tag_text_from_xml(xml_data, 'short_desc'),
            'description': (get_tag_text_from_xml(xml_data, 'long_desc/thetext') or
                           '(Empty description)'),
            'status': status,
            'importance': get_tag_text_from_xml(xml_data, 'bug_severity'),
            'people_involved': self.bugzilla_count_people_involved(xml_data),
            'date_reported': self.bugzilla_date_to_datetime(date_reported_text),
            'last_touched': self.bugzilla_date_to_datetime(last_touched_text),
            'submitter_username': u,
            'submitter_realname': r,
            'canonical_bug_link': self.as_bug_specific_url(),
            'looks_closed': looks_closed
            }
        ret_dict = extract_tracker_specific_data(xml_data, ret_dict)
        return ret_dict
