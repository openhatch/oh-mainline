import csv
import datetime
import hashlib
import logging

import lxml.etree

from mysite.base.decorators import cached_property
import mysite.base.helpers
import mysite.base.models
import mysite.customs.ohloh
import mysite.search.models

############################################################
# Functions and classes for interacting with the tracker

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

############################################################
# General bug importing class

# FIXME: Should have this somewhere else. Maybe a decorator?
# Could take arguments of urls and remove the fresh ones.
def url_is_more_fresh_than_one_day(url):
    # generate the right key to use. This way, even if the URL is super long, we only ever
    # use a short-enough key to represent it.
    key = '_bugzilla_freshness_' + hashlib.sha1(url).hexdigest()

    # First, get a timestamp we can check
    url_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string(key)
    url_age = datetime.datetime.now() - url_timestamp
    # Does that age indicate we GET'd this URL within the past day?
    url_is_fresh = (url_age < datetime.timedelta(days=1))
    # SIDE EFFECT: This function bumps that timestamp!
    mysite.base.models.Timestamp.update_timestamp_for_string(key)
    return url_is_fresh

class BugzillaBugTracker(object):
    def __init__(self, base_url, project_name, bug_project_name_format, bug_id_list_only=False):
        self.base_url = base_url
        self.project_name = project_name
        self.bug_project_name_format = bug_project_name_format
        self.bug_id_list_only = bug_id_list_only

    def generate_bug_xml_from_queries(self, queries):
        # If a dictionary has been passed in, convert it to a list.
        if type(queries) == type({}):
            queries = [queries[query_name] for query_name in queries]
        for query_url in queries:
            # Check if this url has been accessed in the last day
            if url_is_more_fresh_than_one_day(query_url):
                # Sweet, ignore this one and go on.
                logging.info("[Bugzilla] URL %s is fresh, skipping..." % query_url)
                continue
            query_xml = mysite.customs.bugtrackers.bugzilla.url2bug_data(query_url)
            for bug_xml in query_xml.xpath('bug'):
                yield bug_xml

    def get_bug_id_list_from_tracker_bug_urls(self, tracker_bug_urls):
        # If a dictionary has been passed in, convert it to a list.
        if type(tracker_bug_urls) == type({}):
            tracker_bug_urls = [tracker_bug_urls[tracker_bug_name] for tracker_bug_name in tracker_bug_urls]
        bug_ids = []
        for tracker_bug_url in tracker_bug_urls:
            bug_ids += mysite.customs.bugtrackers.bugzilla.tracker_bug2bug_ids(tracker_bug_url)
        return list(set(bug_ids))

    def generate_bug_project_name(self, bb):
        return self.bug_project_name_format.format(
                project = self.project_name,
                product = bb.product,
                component = bb.component)

    def create_or_refresh_one_bugzilla_bug(self, bb):
        bug_id = bb.bug_id
        bug_url = bb.as_bug_specific_url()

        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                    canonical_bug_link=bug_url)
            # Found an existing bug. Does it need refreshing?
            if bug.data_is_more_fresh_than_one_day():
                logging.info("[Bugzilla] Bug %d from %s is fresh. Doing nothing!" % (bug_id, self.project_name))
                return False # sweet
        except mysite.search.models.Bug.DoesNotExist:
            # This is a new bug
            bug = mysite.search.models.Bug(canonical_bug_link = bug_url)

        # Looks like we have some refreshing to do.
        logging.info("[Bugzilla] Refreshing bug %d from %s." % (bug_id, self.project_name))
        # Get the dictionary of data to put into the bug. The function for
        # obtaining tracker-specific data is passed in.
        data = bb.as_data_dict_for_bug_object(self.extract_tracker_specific_data)

        # Fill that bug!
        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # Find or create the project for the bug and save it
        bug_project_name = self.generate_bug_project_name(bb)
        if bug_project_name == '':
            raise ValueError("Can't have bug_project_name as ''")
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=bug_project_name)
        if bug.project_id != project_from_name.id:
            bug.project = project_from_name
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()
        logging.info("[Bugzilla] Finished with %d from %s." % (bug_id, self.project_name))
        return True

    def refresh_all_bugs(self):
        for bug in mysite.search.models.Bug.all_bugs.filter(
                canonical_bug_link__contains=self.base_url):
            bb = mysite.customs.bugtrackers.bugzilla.BugzillaBug.from_url(
                    bug.canonical_bug_link)
            self.create_or_refresh_one_bugzilla_bug(bb=bb)

    def update(self):
        logging.info("[Bugzilla] Started refreshing all %s bugs" % self.project_name)

        # First, go through and create or refresh all the bugs that
        # we are configured to track. This will add new bugs and
        # update current ones. Bugzilla doesn't return a nice
        # CSV list of bug ids, but instead gives an entire XML tree
        # of bug data for the bugs matching the query. To save on
        # network traffic, the bug data will be passed to the refresher.
        if self.bug_id_list_only:
            # If we have a tracking bug, then we can't get an xml tree
            # of bug data. Instead we have to use the bug ids pulled
            # from the dependencies of the tracking bug.
            current_bug_id_list = self.get_current_bug_id_list()
            for bug_id in current_bug_id_list:
                bb = mysite.customs.bugtrackers.bugzilla.BugzillaBug(
                        BASE_URL=self.base_url,
                        bug_id=bug_id)
                self.create_or_refresh_one_bugzilla_bug(bb=bb)
        else:
            logging.info("[Bugzilla] Fetching XML data for bugs in tracker...")
            for bug_data in self.generate_current_bug_xml():
                bb = mysite.customs.bugtrackers.bugzilla.BugzillaBug(
                        BASE_URL=self.base_url,
                        bug_data=bug_data)
                self.create_or_refresh_one_bugzilla_bug(bb=bb)

        # Then refresh all the bugs we have from this tracker. This
        # should skip over all the bugs except the ones that didn't
        # appear in the above query. Usually this is closed bugs.
        self.refresh_all_bugs()

############################################################
# Function that creates classes for individual trackers
def bugzilla_tracker_factory(bt):
    # Create '__init__' method
    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url=bt.base_url,
                                    project_name=bt.project_name
                                    bug_project_name_format=bt.bug_project_name_format

    # Create bug query methods. It doesn't matter what type of query url
    # is stored, since the incorrectly generated method will not be used
    # anyway when bt.query_url_type is checked later.

    # Create 'generate_current_bug_xml' method
    def generate_current_bug_xml(self):
        queries = bt.bugzillaurl_set.all()
        query_urls = [query.url for query in queries]
        return self.generate_bug_xml_from_queries(query_urls)

    # Create 'get_current_bug_id_list' method
    def get_current_bug_id_list(self):
        tracker_bugs = bt.bugzillaurl_set.all()
        tracker_bug_urls = [tb.url for tb in tracker_bugs]
        return self.get_bug_id_list_from_tracker_bugs(tracker_bug_urls)

    # Create 'extract_tracker_specific_data' method
    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Get keywords first since used in multiple checks
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))

        # Bitesized bug checks
        # Check for the bitesized keyword if it exists
        if bt.bitesized_type == 'key'::
            ret_dict['good_for_newcomers'] = (bt.bitesized_text in keywords)
            ret_dict['bite_size_tag_name'] = bt.bitesized_text
        # No keyword. Check for the bitsized whiteboard tag if it exists
        elif bt.bitesized_type == 'wboard':
            whiteboard_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'status_whiteboard')
            ret_dict['good_for_newcomers'] = (whiteboard_text == bt.bitesized_text)
            ret_dict['bite_size_tag_name'] = bt.bitesized_text

        # Documentation bug checks
        # Check for the documentation keyword if it exists
        if bt.documentation_type == 'key':
            ret_dict['concerns_just_documentation'] = (bt.documentation_text in keywords)
        # No keyword. Check for the documentation component if it exists
        elif bt.documentation_type == 'comp':
            component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
            ret_dict['concerns_just_documentation'] = (component == bt.documentation_text)
        # No component. Check for the documentation product if it exists
        elif bt.documentation_type == 'prod':
            product = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'product')
            ret_dict['concerns_just_documentation'] = (product == bt.documentation_text)

        # Distribution tag. We can always set this, as the Bug model uses
        # '' as default anyway, and we default to that for blank answers.
        ret_dict['as_appears_in_distribution'] = bt.as_appears_in_distribution

        # Tracker-specific stuff e.g. stripping 'JJ:' from KDE bug titles.
        # FIXME: How do we efficiently implement this?

        # Then pass ret_dict back
        return ret_dict

    # Create 'generate_bug_project_name' method
    # FIXME: Implement this properly. Until this is done, trackers that overload
    # this function will remain as special cases.
    #def generate_bug_project_name(self, bb):
        #return bt.project_name

    # Generate class dictionary
    # All sub-classes have '__init__' and 'extract_tracker_specific_data' methods
    class_dict = {'__init__': __init__,
                  'extract_tracker_specific_data': extract_tracker_specific_data}

    # A sub-class will have either a 'generate_current_bug_xml' method or
    # a 'get_current_bug_id_list' method.
    if bt.query_url_type = 'xml':
        class_dict['generate_current_bug_xml'] = generate_current_bug_xml
    else:
        class_dict['get_current_bug_id_list'] = get_current_bug_id_list

    # Return the generated sub-class.
    sub-class_name = '%sBugzilla' % bt.project_name.replace(' ', '')
    return type(sub-class_name, (BugzillaBugTracker,), class_dict)

############################################################
# Generator of sub-classes from data

def generate_bugzilla_tracker_classes(tracker_name=None):
    # If a tracker name was passed in then return the
    # specific sub-class for that tracker.
    if tracker_name:
        try:
            bt = customs.models.BugzillaTracker.all_trackers.get(project_name=tracker_name)
            return bugzilla_tracker_factory(bt)
        except mysite.customs.models.BugzillaTracker.DoesNotExist:
            return None
    else:
        # Create a generator that yields all sub-classes.
        for bt in mysite.customs.models.BugzillaTracker.all_trackers.all():
            yield bugzilla_tracker_factory(bt)

############################################################
# Specific sub-classes for individual bug trackers

class MiroBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugzilla.pculture.org/',
                                    project_name='Miro',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                #'Documentation bugs':
                    #''
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided xml data
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('bitesized' in keywords)
        ret_dict['bite_size_tag_name'] = 'bitesized'
        # Then pass ret_dict back
        return ret_dict

class KDEBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugs.kde.org/',
                                    project_name='KDE',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'https://bugs.kde.org/buglist.cgi?query_format=advanced&keywords=junior-jobs&resolution=---',
                'Documentation bugs':
                    'https://bugs.kde.org/buglist.cgi?query_format=advanced&product=docs&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('junior-jobs' in keywords)
        ret_dict['bite_size_tag_name'] = 'junior-jobs'
        # Remove 'JJ:' from title if present
        if ret_dict['title'].startswith("JJ:"):
            ret_dict['title'] = ret_dict['title'][3:].strip()
        # Check whether documentation bug
        product = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'product')
        ret_dict['concerns_just_documentation'] = (product == 'docs')
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        product = bb.product
        reasonable_products = set([
            'Akonadi',
            'Phonon'
            'kmail',
            'Rocs',
            'akregator',
            'amarok',
            'ark',
            'cervisia',
            'k3b',
            'kappfinder',
            'kbabel',
            'kdeprint',
            'kdesktop',
            'kfile',
            'kfourinline',
            'khotkeys',
            'kio',
            'kmail',
            'kmplot',
            'koffice',
            'kompare',
            'konqueror',
            'kopete',
            'kpat',
            'kphotoalbum',
            'krita',
            'ksmserver',
            'kspread',
            'ksysguard',
            'ktimetracker',
            'kwin',
            'kword',
            'marble',
            'okular',
            'plasma',
            'printer-applet',
            'rsibreak',
            'step',
            'systemsettings',
            'kdelibs',
            'kcontrol',
            'korganizer',
            'kipiplugins',
            'Phonon',
            'dolphin',
            'umbrello']
            )
        products_to_be_renamed = {
            'digikamimageplugins': 'digikam image plugins',
            'Network Management': 'KDE Network Management',
            'telepathy': 'telepathy for KDE',
            'docs': 'KDE documentation',
            }
        component = bb.component
        things = (product, component)

        if product in reasonable_products:
            bug_project_name = product
        else:
            if product in products_to_be_renamed:
                bug_project_name = products_to_be_renamed[product]
            else:
                logging.info("Guessing on KDE subproject name. Found %s" %  repr(things))
                bug_project_name = product
        return bug_project_name

class MediaWikiBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.wikimedia.org/',
                                    project_name='MediaWiki',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'https://bugzilla.wikimedia.org/buglist.cgi?keywords=easy&query_format=advanced&resolution=LATER&resolution=---',
                'Documentation bugs':
                    'https://bugzilla.wikimedia.org/buglist.cgi?query_format=advanced&component=Documentation&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('easy' in keywords)
        ret_dict['bite_size_tag_name'] = 'easy'
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        ret_dict['concerns_just_documentation'] = (component == 'Documentation')
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        product = bb.product
        if product == 'MediaWiki extensions':
            bug_project_name = bb.component
            if bug_project_name in ('FCKeditor', 'Gadgets'):
                bug_project_name += ' for MediaWiki'
        else:
            bug_project_name = product
        return bug_project_name

class GnomeBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.gnome.org/',
                                    project_name='Gnome',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        # Get all bugs that contain any of the keywords 'gnome-love'
        # or 'documentation'
        queries = {
                'Easy bugs':
                    'https://bugzilla.gnome.org/buglist.cgi?columnlist=id&keywords=gnome-love&query_format=advanced&resolution=---',
                # FIXME: Query with documentation keyword causes XML syntax errors
                #'Documentation bugs':
                    #'https://bugzilla.gnome.org/buglist.cgi?columnlist=id&keywords=gnome-love%2Cdocumentation&query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('gnome-love' in keywords)
        ret_dict['bite_size_tag_name'] = 'gnome-love'
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('documentation' in keywords)
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        bug_project_name = bb.product
        gnome2openhatch = {'general': 'GNOME (general)',
                           'website': 'GNOME (website)'}
        if bug_project_name in gnome2openhatch:
            bug_project_name=gnome2openhatch[bug_project_name]
        return bug_project_name

class MozillaBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.mozilla.org/',
                                    project_name='Mozilla',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'https://bugzilla.mozilla.org/buglist.cgi?resolution=---;status_whiteboard_type=substring;query_format=advanced;status_whiteboard=[good%20first%20bug]',
                #'Documentation bugs':
                    #''
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        whiteboard_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'status_whiteboard')
        ret_dict['good_for_newcomers'] = (whiteboard_text == '[good first bug]')
        ret_dict['bite_size_tag_name'] = '[good first bug]'
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        ### Special-case the project names we know about
        mozilla2openhatch = {'Core': 'Mozilla Core',
                             'Firefox': 'Firefox',
                             'MailNews Core': 'Mozilla Messaging',
                             'addons.mozilla.org': 'addons.mozilla.org',
                             'Thunderbird': 'Thunderbird',
                             'Testing': 'Mozilla automated testing',
                             'Directory': 'Mozilla LDAP',
                             'mozilla.org': 'mozilla.org',
                             'SeaMonkey': 'SeaMonkey',
                             'Toolkit': 'Mozilla Toolkit',
                             'support.mozilla.com': 'support.mozilla.com',
                             'Camino': 'Camino',
                             'Calendar': 'Mozilla Calendar',
                             'Mozilla Localizations': 'Mozilla Localizations',
                             }
        if bb.product == 'Other Applications':
            bug_project_name = 'Mozilla ' + bb.component
        else:
            bug_project_name = mozilla2openhatch[bb.product]
        return bug_project_name

class FedoraBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.redhat.com/',
                                    project_name='Fedora',
                                    bug_project_name_format='{component}',
                                    bug_id_list_only=True)

    def get_current_bug_id_list(self):
        tracker_bug_urls = [
                'https://bugzilla.redhat.com/show_bug.cgi?ctype=xml&id=509829'
                ]
        return self.get_bug_id_list_from_tracker_bug_urls(tracker_bug_urls)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = True # Since they are 'fit and finish'
        ret_dict['bite_size_tag_name'] = 'fitandfinish'
        # Set the distribution tag
        ret_dict['as_appears_in_distribution'] = 'Fedora'
        # Then pass ret_dict back
        return ret_dict

class SongbirdBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugzilla.songbirdnest.com/',
                                    project_name='Songbird',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        # Query below returns nearly 4000 bugs if we try to index everything.
        # For now, only import bugs with 'helpwanted' tag.
        # (This tag doesn't equate to 'bitesized'.)
        queries = {
                'Helpwanted bugs':
                    'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&resolution=---&keywords=helpwanted',
                'Documentation bugs':
                    'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&component=Documentation&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # 'helpwanted' doesn't just indicate bitesized.
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        ret_dict['concerns_just_documentation'] = (component == 'Documentation')
        # Then pass ret_dict back
        return ret_dict

class ApertiumBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugs.apertium.org/cgi-bin/bugzilla/',
                                    project_name='Apertium',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'http://bugs.apertium.org/cgi-bin/bugzilla/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword.
        # Then pass ret_dict back
        return ret_dict

class RTEMSBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://www.rtems.org/bugzilla/',
                                    project_name='RTEMS',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'https://www.rtems.org/bugzilla/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword.
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        ret_dict['concerns_just_documentation'] = (component == 'doc')
        # Then pass ret_dict back
        return ret_dict

# This tracker could be extended to cover all of FreeDesktop.
# For now, just do X.Org since it is all that was requested.
class XOrgBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugs.freedesktop.org/',
                                    project_name='XOrg',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        # Query below returns over 2500 bugs if we try to index everything.
        # For now just index bitesized bugs - keyword filter added to query.
        queries = {
                'Easy bugs':
                    'https://bugs.freedesktop.org/buglist.cgi?query_format=advanced&keywords=janitor&resolution=---&product=xorg',
                'Documentation bugs':
                    'https://bugs.freedesktop.org/buglist.cgi?query_format=advanced&component=Docs%2Fother&component=Documentation&component=Fonts%2Fdoc&resolution=---&product=xorg'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('janitor' in keywords)
        ret_dict['bite_size_tag_name'] = 'janitor'
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        documentation_components = [
                'Docs/other',
                'Documentation',
                'Fonts/doc']
        ret_dict['concerns_just_documentation'] = (component in documentation_components)
        # Then pass ret_dict back
        return ret_dict

class LocamotionBugzilla(BugzillaBugTracker):
    enabled = False # FIXME: Throws XML encoding error.

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugs.locamotion.org/',
                                    project_name='Locamotion',
                                    bug_project_name_format='{product}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'http://bugs.locamotion.org/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword.
        # Then pass ret_dict back
        return ret_dict

class HypertritonBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://hypertriton.com/bugzilla/',
                                    project_name='Hypertriton',
                                    bug_project_name_format='{product}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'https://hypertriton.com/bugzilla/buglist.cgi?query_format=advanced&resolution=---&product=Agar&product=EDAcious&product=FabBSD&product=FreeSG'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword
        # Then pass ret_dict back
        return ret_dict

class PygameBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://pygame.motherhamster.org/bugzilla/',
                                    project_name='pygame',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'http://pygame.motherhamster.org/bugzilla/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword
        # Then pass ret_dict back
        return ret_dict

# The generic class for Bugzilla trackers. Copy it.
# If the project has a tracker bug for the bugs to be imported,
# set bug_id_list_only=True in BugzillaBugTracker.__init__ and
# replace get_current_xml_bug_tree with get_current_bug_id_list
# bug_project_name_format can contain the tags {project},
# {product} and {component} which will be replaced accordingly.
class GenBugzilla(BugzillaBugTracker):
    enabled = False

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='',
                                    project_name='',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        # Can replace both entries below with an 'All bugs' query.
        queries = {
                'Easy bugs':
                    '',
                'Documentation bugs':
                    ''
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('' in keywords)
        ret_dict['bite_size_tag_name'] = ''
        # Then pass ret_dict back
        return ret_dict

    # The format string method for generating the project name can be
    # overloaded by uncommenting the function below.
    #def generate_bug_project_name(self, bb):
        #return bug_project_name

