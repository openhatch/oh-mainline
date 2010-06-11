import csv
import datetime
import urlparse
import cgi

import dateutil.parser
import lxml.html
import lxml.html.clean

import mysite.base.helpers
from mysite.base.decorators import cached_property
import mysite.customs.ohloh
import mysite.search.templatetags.search

def csv_of_bugs(url):
    b = mysite.customs.ohloh.mechanize_get(url)
    return b.response()

def sugar_labs_csv_of_easy_bugs():
    b = mysite.customs.ohloh.mechanize_get(
        'http://bugs.sugarlabs.org/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7sugar-love&order=priority')
    return b.response()    

def csv_url2list_of_bug_ids(csv_fd):
    dictreader = csv.DictReader(csv_fd)
    return [int(line['id']) for line in dictreader]

class TracBug:
    @staticmethod
    def page2metadata_table(doc):
        ret = {}
        key_ths = doc.cssselect('table.properties th')
        for key_th in key_ths:
            key = key_th.text
            value = key_th.itersiblings().next().text
            ret[key.strip()] = value.strip()
        return ret
    
    @staticmethod
    def page2description_div(doc):
        div = doc.cssselect('.description .searchable')[0]
        cleaner = lxml.html.clean.Cleaner(javascript=True, scripts=True, meta=True, page_structure=True, embedded=True, frames=True, forms=True, remove_unknown_tags=True, safe_attrs_only=True, add_nofollow=True)
        return cleaner.clean_html(lxml.html.tostring(div))

    @staticmethod
    def page2date_opened(doc):
        span = doc.cssselect(
            '''.date p:contains("Opened") span,
            .date p:contains("Opened") a''')[0]
        return TracBug._span2date(span)

    @staticmethod
    def page2date_modified(doc):
        try:
            span = doc.cssselect(
                '''.date p:contains("Last modified") span,
                .date p:contains("Last modified") a''')[0]
        except IndexError:
            return TracBug.page2date_opened(doc)
        return TracBug._span2date(span)

    @staticmethod
    def _span2date(span):
        date_string = span.attrib['title']
        date_string = date_string.replace('in Timeline', '')
        return mysite.base.helpers.string2naive_datetime(date_string)

    @staticmethod
    def all_people_in_changes(doc):
        people = []
        for change_h3 in doc.cssselect('.change h3'):
            text = change_h3.text_content()
            for line in text.split('\n'):
                if 'changed by' in line:
                    person = line.split('changed by')[1].strip()
                    people.append(person)
        return people

    def __init__(self, bug_id, BASE_URL):
        self._bug_specific_csv_data = None
        self._bug_html_page = None
        self._parsed_bug_html_page = None
        self.bug_id = int(bug_id)
        if not BASE_URL.endswith('/'):
            BASE_URL += '/'
        self.BASE_URL = BASE_URL

    @staticmethod
    def from_url(url):
        base, ticket, num = url.rsplit('/', 2)
        bug_id = int(num)
        assert ticket == 'ticket'
        return TracBug(bug_id=bug_id,
                       BASE_URL=base + '/')

    def as_bug_specific_url(self):
        return urlparse.urljoin(self.BASE_URL,
                                "ticket/%d" % self.bug_id)

    def as_bug_specific_csv_url(self):
        return self.as_bug_specific_url() +"?format=csv"

    @cached_property
    def component(self):
        return self.as_bug_specific_csv_data()['component']

    def as_bug_specific_csv_data(self):
        if self._bug_specific_csv_data is None:
            b = mysite.customs.ohloh.mechanize_get(
                self.as_bug_specific_csv_url())
            dr = csv.DictReader(b.response().readlines())
            self._bug_specific_csv_data = dr.next()
        return self._bug_specific_csv_data

    def get_bug_html_page(self):
        if self._bug_html_page is None:
            b = mysite.customs.ohloh.mechanize_get(
                self.as_bug_specific_url())
            self._bug_html_page = b.response().read()
        return self._bug_html_page

    def get_parsed_bug_html_page(self):
        if self._parsed_bug_html_page is None:
            self._parsed_bug_html_page = lxml.html.fromstring(
                self.get_bug_html_page())
        return self._parsed_bug_html_page

    @staticmethod
    @mysite.base.decorators.unicodify_strings_when_inputted
    def string_un_csv(s):
        s = cgi.escape(s)
        return unicode(s, 'utf-8')

    def as_data_dict_for_bug_object(self):
        trac_data = self.as_bug_specific_csv_data()
        html_data = self.get_parsed_bug_html_page()

        ret = {'title': trac_data['summary'],
               'description': TracBug.string_un_csv(trac_data['description']),
               'status': trac_data['status'],
               'importance': trac_data['priority'],
               'submitter_username': trac_data['reporter'],
               'submitter_realname': '', # can't find this in Trac
               'canonical_bug_link': self.as_bug_specific_url(),
               'good_for_newcomers': ('easy' in trac_data['keywords']),
               'bite_size_tag_name': 'easy',
               'concerns_just_documentation': False,
               'as_appears_in_distribution': '',
               'last_polled': datetime.datetime.utcnow(),
               }
        ret['looks_closed'] = (trac_data['status'] == 'closed')

        page_metadata = TracBug.page2metadata_table(html_data)
        
        all_people = set(TracBug.all_people_in_changes(html_data))
        all_people.add(page_metadata['Reported by:'])
        all_people.update(
            map(lambda x: x.strip(),
                page_metadata.get('Cc', '').split(',')))
        all_people.update(
            map(lambda x: x.strip(),
                page_metadata.get('Cc:', '').split(',')))
        try:
            assignee = page_metadata['Assigned to:']
        except KeyError:
            assignee = page_metadata['Owned by:']

        all_people.add(assignee)
        ret['people_involved'] = len(all_people)

        # FIXME: Need time zone
        ret['date_reported'] = TracBug.page2date_opened(html_data)
        ret['last_touched'] = TracBug.page2date_modified(html_data)
        return ret
