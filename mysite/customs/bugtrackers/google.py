import datetime
import hashlib
import logging

import gdata.projecthosting.client

import mysite.search.models

############################################################
# Functins and classes for interacting with the tracker

def get_client(username=None, password=None):
    client = gdata.projecthosting.client.ProjectHostingClient()
    if username is not None and password is not None:
        # Return authenticated client
        return client.client_login(
                username,
                password,
                source='OpenHatch-GoogleBugImporter-1.0',
                service='code')
    else:
        # Return unauthenticated client
        return client

def create_google_query(**kwargs):
    # We only need to be able to search these fields.
    # So ignore any others.
    allowed_keys = [
            'issue_id',
            'label',
            'canned_query',
            'owner',
            'status',
            'text_query',
            'author',
            'max_results']
    temp = kwargs
    for key in temp:
        if key not in allowed_keys:
            del kwargs[key]
    return gdata.projecthosting.client.Query(**kwargs)

def get_google_issue_entries(client, google_name, query=None):
    if query is None:
        feed = client.get_issues(google_name)
    else:
        feed = client.get_issues(google_name, query=query)
    return feed.entry

class GoogleBug(object):
    @staticmethod
    def from_url(url, client):
        a, b, c, d, google_name, e, ending = url.split('/')
        show_bug, num = ending.split('=')
        bug_id = int(num)
        assert show_bug == 'detail?id'
        return GoogleBug(google_name=google_name,
                         client=client,
                         bug_id=bug_id)

    def __init__(self, google_name, client, bug_id=None, bug_data=None):
        self._bug_specific_atom_data = bug_data
        # If bug_id is not provided, try to extract it from bug_data
        if bug_id is None:
            if self._bug_specific_atom_data is not None:
                self.bug_id = self._bug_id_from_bug_data()
            else:
                raise ValueError("bug_id must not be None if bug_data is None")
        else:
            self.bug_id = int(bug_id)
        self.google_name = google_name
        self.client = client

    def _bug_id_from_bug_data(self):
        id_url = self.get_bug_atom_data().id.text
        base, num = id_url.rsplit('/', 1)
        return int(num)

    def as_bug_specific_url(self):
        return 'http://code.google.com/p/%s/issues/detail?id=%d' % (self.google_name, self.bug_id)

    def get_bug_atom_data(self):
        # GoogleBug object could have been created with or without data.
        # So if no bug data in object, fill first before returning.
        if self._bug_specific_atom_data is None:
            query = create_google_query(issue_id = self.bug_id)
            self._bug_specific_atom_data = get_google_issue_entries(self.client, self.google_name, query)[0]
        return self._bug_specific_atom_data

    @staticmethod
    def google_count_people_involved(issue):
        # At present this only gets the author, owner if any and CCers if any.
        # FIXME: We could get absolutely everyone involved using comments,
        # but that would require an extra network call per bug.

        # Add everyone who is on CC: list
        everyone = [cc.username.text for cc in issue.cc]
        # Add author
        if type(issue.author) == type([]):
            for author in issue.author:
                everyone.append(author.name.text)
        else:
            everyone.append(issue.author.name.text)
        # Add owner if there
        if issue.owner:
            if type(issue.owner) == type([]):
                for owner in issue.owner:
                    everyone.append(owner.username.text)
            else:
                everyone.append(issue.owner.username.text)
        # Return length of the unique set of everyone.
        return len(set(everyone))

    @staticmethod
    def google_date_to_datetime(date_string):
        return mysite.base.helpers.string2naive_datetime(date_string)

    @staticmethod
    def google_find_label_type(labels, type_string):
        # This is for labels of format 'type-value'.
        # type is passed in, value is returned.
        for label in labels:
            if type_string in label.text:
                return label.text.split('-', 1)[1]
        return ''

    def as_data_dict_for_bug_object(self, extract_tracker_specific_data):
        issue = self.get_bug_atom_data()
        if issue.status:
            status = issue.status.text
        else:
            status = ''
        if type(issue.author) == type([]):
            author = issue.author[0]
        else:
            author = issue.author

        ret_dict = {
                'title': issue.title.text,
                'description': issue.content.text,
                'status': status,
                'importance': self.google_find_label_type(issue.label, 'Priority'),
                'people_involved': self.google_count_people_involved(issue),
                'date_reported': self.google_date_to_datetime(issue.published.text),
                'last_touched': self.google_date_to_datetime(issue.updated.text),
                'submitter_username': author.name.text,
                'submitter_realname': '', # Can't get this from Google
                'canonical_bug_link': self.as_bug_specific_url(),
                'looks_closed': (issue.state.text == 'closed')
                }
        ret_dict = extract_tracker_specific_data(issue, ret_dict)
        return ret_dict

############################################################
# General bug importing class

def query_is_more_fresh_than_one_day(google_name, query):
    # Generate a key for this particular combination of google_name
    # and query.
    data_string = google_name
    allowed_keys = [
            'issue_id',
            'label',
            'canned_query',
            'owner',
            'status',
            'text_query',
            'author']
    for key in dir(query)[19:]:
        if key in allowed_keys:
            if getattr(query, key):
                for n in getattr(query, key):
                    # This ensures that both objects in query that are lists and
                    # ones that are just strings get appended to the data_string.
                    data_string += n
    key = '_google_freshness_' + hashlib.sha1(data_string).hexdigest()

    # First, get a timestamp we can check
    query_timestamp = mysite.base.models.Timestamp.get_timestamp_for_string(key)
    query_age = datetime.datetime.now() - query_timestamp
    # Does that age indicate we GET'd this query within the past day?
    query_is_fresh = (query_age < datetime.timedelta(days=1))
    # SIDE EFFECT: This function bumps that timestamp!
    mysite.base.models.Timestamp.update_timestamp_for_string(key)
    return query_is_fresh

class GoogleBugTracker(object):
    def __init__(self, project_name, google_name):
        self.project_name = project_name
        self.google_name = google_name
        self.client = get_client()

    def generate_bug_atom_from_queries(self, queries):
        for query in queries:
            # Check if this query has been accessed in the last day
            if query_is_more_fresh_than_one_day(self.google_name, query):
                # Sweet, ignore this one and go on.
                logging.info("[Google] A query for project named %s is fresh, skipping it..." % self.project_name)
                continue
            issues = get_google_issue_entries(self.client, self.google_name, query)
            for issue in issues:
                yield issue

    def create_or_refresh_one_google_bug(self, gb):
        bug_id = gb.bug_id
        bug_url = gb.as_bug_specific_url()

        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                    canonical_bug_link=bug_url)
            # Found an existing bug. Does it need refreshing?
            if bug.data_is_more_fresh_than_one_day():
                logging.info("[Google] Bug %d from project named %s is fresh. Doing nothing!" % (bug_id, self.project_name))
                return False # sweet
        except mysite.search.models.Bug.DoesNotExist:
            # This is a new bug
            bug = mysite.search.models.Bug(canonical_bug_link = bug_url)

        # Looks like we have some refreshing to do.
        logging.info("[Google] Refreshing bug %d from project named %s." % (bug_id, self.project_name))
        # Get the dictionary of data to put into the bug. The function for
        # obtaining tracker-specific data is passed in.
        data = gb.as_data_dict_for_bug_object(self.extract_tracker_specific_data)

        # Fill that bug!
        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # Find or create the project for the bug and save it
        # For now, just use project_name
        bug_project_name = self.project_name
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=bug_project_name)
        if bug.project_id != project_from_name.id:
            bug.project = project_from_name
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()
        logging.info("[Google] Finished with bug %d from project named %s." % (bug_id, self.project_name))
        return True

    def refresh_all_bugs(self):
        for bug in mysite.search.models.Bug.all_bugs.filter(
                canonical_bug_link__contains="http://code.google.com/p/%s/" % self.google_name):
            gb = GoogleBug.from_url(
                    bug.canonical_bug_link, self.client)
            self.create_or_refresh_one_google_bug(gb=gb)

    def update(self):
        logging.info("[Google] Started refreshing all bugs from project named %s." % self.project_name)
        logging.info("[Google] Fetching Atom data for bugs in tracker...")
        for bug_data in self.generate_current_bug_atom():
            gb = GoogleBug(
                    google_name=self.google_name,
                    client=self.client,
                    bug_data=bug_data)
            self.create_or_refresh_one_google_bug(gb=gb)
        # Now refresh any bugs that we missed (i.e. they are
        # not in the current list of inspected bugs.
        self.refresh_all_bugs()

############################################################
# Function that creates classes for individual trackers
def google_tracker_factory(gt):
    # Create '__init__' method
    def __init__(self):
        GoogleBugTracker.__init__(self,
                                  project_name=gt.project_name,
                                  google_name=gt.google_name)

    # Create 'generate_current_bug_atom' method
    def generate_current_bug_atom(self):
        query_objs = gt.googlequery_set.all()
        query_data = []
        for query_obj in query_objs:
            one_query = {
                    'max_results': 10000,
                    'canned_query': 'open',
                    'label': query_obj.label
                    }
            query_data.append(one_query)
        queries = []
        for kwargs in query_data:
            queries.append(create_google_query(**kwargs))
        return self.generate_bug_atom_from_queries(queries)

    # Create 'extract_tracker_specific_data' method
    @staticmethod
    def extract_tracker_specific_data(issue, ret_dict):
        # Make modifications to ret_dict using provided atom data
        labels = [label.text for label in issue.label]
        if gt.bitesized_type == 'label':
            ret_dict['good_for_newcomers'] = (gt.bitesized_text in labels)
            ret_dict['bite_size_tag_name'] = gt.bitesized_label
        # Check whether documentation bug
        if gt.documentation_type == 'label':
            ret_dict['concerns_just_documentation'] = (gt.documentation_text in labels)
        # Then pass ret_dict back
        return ret_dict

    # Generate class dictionary
    # All sub-classes have '__init__', 'generate_current_bug_atom'
    # and 'extract_tracker_specific_data' methods
    class_dict = {'__init__': __init__,
                  'generate_current_bug_atom': generate_current_bug_atom,
                  'extract_tracker_specific_data': extract_tracker_specific_data}

    # Return the generated sub-class.
    subclass_name = '%sGoogle' % gt.project_name.replace(' ', '')
    return type(subclass_name.encode('ascii'), (GoogleBugTracker,), class_dict)

############################################################
# Generator of sub-classes from data

def generate_google_tracker_classes(tracker_name=None):
    # If a tracker name was passed in then return the
    # specific sub-class for that tracker.
    if tracker_name:
        try:
            gt = mysite.customs.models.GoogleTracker.all_trackers.get(project_name=tracker_name)
            gt_class = google_tracker_factory(gt)
        except mysite.customs.models.GoogleTracker.DoesNotExist:
            gt_class = None
        yield gt_class
        return
    else:
        # Create a generator that yields all sub-classes.
        for gt in mysite.customs.models.GoogleTracker.all_trackers.all():
            yield google_tracker_factory(gt)

############################################################
# Specific sub-classes for individual bug trackers

class MelangeGoogle(GoogleBugTracker):
    enabled = True

    def __init__(self):
        GoogleBugTracker.__init__(self,
                                  project_name='Melange',
                                  google_name='soc')

    def generate_current_bug_atom(self):
        query_data = [
                {
                    'max_results': 10000,
                    'canned_query': 'open',
                    'label': 'Effort-Minimal,Easy,Fair'
                }
                ]
        queries = []
        for kwargs in query_data:
            queries.append(create_google_query(**kwargs))
        return self.generate_bug_atom_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(issue, ret_dict):
        # Make modifications to ret_dict using provided atom data
        labels = [label.text for label in issue.label]
        ret_dict['good_for_newcomers'] = (('Effort-Minimal' in labels) or
                                          ('Effort-Easy' in labels) or
                                          ('Effort-Fair' in labels))
        ret_dict['bite_size_tag_name'] = 'Minimal, Easy or Fair effort'
        # Check whether documentation bug
        ret_dict['concerns_just_documentation'] = ('Component-Docs' in labels)
        # Then pass ret_dict back
        return ret_dict

class FiftyStateProjectGoogle(GoogleBugTracker):
    enabled = True

    def __init__(self):
        GoogleBugTracker.__init__(self,
                                  project_name='Fifty State Project',
                                  google_name='fiftystates')

    def generate_current_bug_atom(self):
        query_data = [
                {
                    'max_results': 10000,
                    'canned_query': 'open',
                }
                ]
        queries = []
        for kwargs in query_data:
            queries.append(create_google_query(**kwargs))
        return self.generate_bug_atom_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(issue, ret_dict):
        # Make modifications to ret_dict using provided atom data
        labels = [label.text for label in issue.label]
        ret_dict['good_for_newcomers'] = ('bite-sized' in labels)
        ret_dict['bite_size_tag_name'] = 'bite-sized'
        # Then pass ret_dict back
        return ret_dict

# The generic class for Google trackers.
class GenGoogle(GoogleBugTracker):
    enabled = False

    def __init__(self):
        GoogleBugTracker.__init__(self,
                                  project_name='',
                                  google_name='')

    def generate_current_bug_atom(self):
        query_data = [
                {
                    'max_results': 10000,
                    'canned_query': 'open',
                }
                ]
        queries = []
        for kwargs in query_data:
            queries.append(create_google_query(**kwargs))
        return self.generate_bug_atom_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(issue, ret_dict):
        # Make modifications to ret_dict using provided atom data
        labels = [label.text for label in issue.label]
        ret_dict['good_for_newcomers'] = ('' in labels)
        ret_dict['bite_size_tag_name'] = ''
        # Check whether documentation bug
        ret_dict['concerns_just_documentation'] = ('' in labels)
        # Then pass ret_dict back
        return ret_dict

