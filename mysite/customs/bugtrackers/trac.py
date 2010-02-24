import csv
import datetime
import mysite.customs.ohloh
import lxml.html
import lxml.html.clean
import urlparse

def twisted_csv_of_easy_bugs():
    b = mysite.customs.ohloh.mechanize_get(
        'http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority')
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
        span = doc.cssselect ('.date p:contains("Opened") span')[0]
        return TracBug._span2date(span)

    @staticmethod
    def page2date_modified(doc):
        span = doc.cssselect ('.date p:contains("Last modified") span')[0]
        return TracBug._span2date(span)

    @staticmethod
    def _span2date(span):
        date_string = span.attrib['title']
        d = datetime.datetime.strptime(
            date_string, '%m/%d/%Y %H:%M:%S %p')
        # %p does not seem to affect interpretation of
        # the hours value. strptime blows.

        # for most PM hours, +12 adjustment
        if 'PM' in date_string:
            # but 12 PM remains 12 PM
            if d.hour != 12:
                d += datetime.timedelta(hours=12)

        # For 12 AM, subtract 12
        if 'AM' in date_string:
            if d.hour == 12:
                d -= datetime.timedelta(hours=12)

        return d

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

    def as_bug_specific_csv_data(self):
        b = mysite.customs.ohloh.mechanize_get(
            self.as_bug_specific_csv_url())
        dr = csv.DictReader(b.response().readlines())
        return dr.next()

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
    def string_un_csv(s):
        s = s.replace("'", '\\' + "'")
        s = eval("'''" + s + "'''")
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
               }
        ret['looks_closed'] = (trac_data['status'] == 'closed')

        page_metadata = TracBug.page2metadata_table(html_data)
        
        all_people = set(TracBug.all_people_in_changes(html_data))
        all_people.add(page_metadata['Reported by:'])
        all_people.update(
            map(lambda x: x.strip(),
                page_metadata.get('Cc', '').split(',')))
        all_people.add(page_metadata['Assigned to:'])
        ret['people_involved'] = len(all_people)

        # FIXME: Need time zone
        ret['date_reported'] = TracBug.page2date_opened(html_data)
        ret['last_touched'] = TracBug.page2date_modified(html_data)
        return ret
