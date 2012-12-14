# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import mysite.base.unicode_sanity

import urllib
import cStringIO as StringIO
import re
from django.utils import simplejson
import datetime
import collections
import logging
import urlparse
import hashlib
import xml.etree.ElementTree as ET
import xml.parsers.expat

from django.utils.encoding import force_unicode

import mysite.search.models
import mysite.profile.models
import mysite.base.helpers

import twisted.web

from mysite.base.depends import lxml

### Generic error handler
class ProfileImporter(object):
    SQUASH_THESE_HTTP_CODES = []

    def errbackOfLastResort(self, error):
        # So the error is something intense -- probably, an actual code bug.
        #
        # The important thing to do is to log the error somewhere in an attempt to make
        # it easier to debug.
        #
        # Twisted errors have a printDetailedTraceback() method
        message = """Uh oh. Asynchronous code hit an unhandled exception.

Here is the details:

"""
        buf = StringIO.StringIO()
        error.printDetailedTraceback(file=buf)
        message += buf.getvalue()

        # Send an email to the admins
        from django.core.mail import mail_admins
        mail_admins(subject="Async error on the site",
                    message=message,
                    fail_silently=True)
        # fail_silently since exceptions here would be bad.

    def squashIrrelevantErrors(self, error):
        ### The way we set up the callbacks and errbacks, this function should process any
        ### exceptions raised by the actual callback.
        ###
        ### It's important that this function never raise an error.
        ###
        ### Once it returns successfully, the DIA processing will continue, and the DIA will
        ### get marked as "completed". So if this function raises an exception, then the DIA
        ### will never get marked as "completed", and then users would be staring at progress
        ### bars for ever and ever!
        squash_it = False

        if error.type == twisted.web.error.Error:
            if error.value.status in self.SQUASH_THESE_HTTP_CODES:
                # The username doesn't exist. That's okay. It just means we have gleaned no profile information
                # from this query.
                squash_it = True

            if squash_it:
                pass
            else:
                # This is low-quality logging for now!
                logging.warn("EEK: " + error.value.status + " " + error.value.response)
        else:
            self.errbackOfLastResort(error)

    def __init__(self, query, dia_id, command):
        ## First, store the data we are passed in.
        self.query = query
        self.dia_id = dia_id
        self.command = command
        ## Then, create a mapping for storing the URLs we are waiting on.
        self.urls_we_are_waiting_on = collections.defaultdict(int)

    def get_dia(self):
        """We have this method so to avoid holding on to any objects from
        the database for a long time.

        Event handler methods should use a fresh database object while they
        run, rather than using some old object that got created when the class
        was instantiated.
        """
        return mysite.profile.models.DataImportAttempt.objects.get(
            id=self.dia_id)

    def markThatTheDeferredFinished(self, url):
        self.urls_we_are_waiting_on[url] -= 1
        # If we just made the state totally insane, then log a warning to that effect.
        if self.urls_we_are_waiting_on[url] < 0:
            logging.error("Eeek, " + url + " went negative.")
        if self.seems_finished():
            # Grab the DataImportAttempt object, and mark it as completed.
            dia = self.get_dia()
            dia.completed = True
            dia.save()
        # Finally, if there is more work to do, enqueue it.
        self.command.create_tasks_from_dias(max=1)

    def seems_finished(self):
        if sum(self.urls_we_are_waiting_on.values()) == 0:
            return True
        return False

    def handleError(self, failure):
        # FIXME: Use Django default exception logic to make an email get sent.
        import logging
        logging.warn(failure)

### This section imports projects from github.com
class ImportActionWrapper(object):
    # This class serves to hold three things:
    # * the URL we requested, and
    # * the ProfileImporter object that caused the URL to be requested.
    # * Function to call.
    #
    # The point of this wrapper is that we call that function for you, and
    # afterward, we call .markThatTheDeferredFinished() on the ProfileImporter.
    #
    # That way, the ProfileImporter can update its records of which URLs have finished
    # being processed.
    def __init__(self, url, pi, fn):
        self.url = url
        self.pi = pi
        self.fn = fn

    def __call__(self, *args, **kwargs):
        # Okay, so we call fn and pass in arguments to it.
        value = self.fn(*args, **kwargs)

        # Then we tell the ProfileImporter that we have handled the URL.
        self.pi.markThatTheDeferredFinished(self.url)
        return value

class GithubImporter(ProfileImporter):

    def squashIrrelevantErrors(self, error):
        squash_it = False

        if error.type == twisted.web.error.Error:
            if error.value.status == '404':
                # The username doesn't exist. That's okay. It just means we have gleaned no profile information
                # from this query.
                squash_it = True
            if error.value.status == '401' and error.value.response == '{"error":"api route not recognized"}':
                # This is what we get when we query e.g. http://github.com/api/v2/json/repos/show/asheesh%40asheesh.org
                # It just means that Github decided that asheesh@asheesh.org is not a valid username.
                # Just like above -- no data to return.
                squash_it = True

            if squash_it:
                pass
            else:
                # This is low-quality logging for now!
                logging.warn("EEK: " + error.value.status + " " + error.value.response)
        else:
            raise error.value

    # This method takes a repository dict as returned by Github
    # and creates a Citation, also creating the relevant
    # PortfolioEntry if necessary.
    def addCitationFromRepoDict(self, repo_dict, override_contrib=None):
        # Get the DIA whose ID we stored
        dia = self.get_dia()
        person = dia.person

        # Get or create a project by this name
        (project, _) = mysite.search.models.Project.objects.get_or_create(
            name=repo_dict['name'])

        # Look and see if we have a PortfolioEntry. If not, create
        # one.
        if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
            portfolio_entry = mysite.profile.models.PortfolioEntry(person=person,
                                             project=project,
                                             project_description=repo_dict['description'] or '')
            portfolio_entry.save()

        # Either way, it is now safe to get it.
        portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]

        citation = mysite.profile.models.Citation()
        citation.languages = "" # FIXME ", ".join(result['languages'])

        # Fill out the "contributor role", either by data we got
        # from the network, or by special arguments to this
        # function.
        if repo_dict['fork']:
            citation.contributor_role = 'Forked'
        else:
            citation.contributor_role = 'Started'
        if override_contrib:
            citation.contributor_role = override_contrib
        citation.portfolio_entry = portfolio_entry
        citation.data_import_attempt = dia
        citation.url = 'http://github.com/%s/%s/' % (urllib.quote_plus(repo_dict['owner']),
                                                     urllib.quote_plus(repo_dict['name']))
        citation.save_and_check_for_duplicates()

    def handleUserRepositoryJson(self, json_string):
        data = simplejson.loads(json_string)
        if 'repositories' not in data:
            return

        repos = data['repositories']
        # for every repository, we need to get its primary
        # programming language. FIXME.
        # For now we skip that.
        for repo in repos:
            self.addCitationFromRepoDict(repo)

        person = self.get_dia().person

        person.last_polled = datetime.datetime.now()
        person.save()


    def getUrlsAndCallbacks(self):
        urls_and_callbacks = []

        # Well, one thing we can do is get the repositories the user owns.
        this_one = {'errback': self.squashIrrelevantErrors}
        this_one['url'] = ('http://github.com/api/v2/json/repos/show/' +
            mysite.base.unicode_sanity.quote(self.query))
        this_one['callback'] = self.handleUserRepositoryJson
        urls_and_callbacks.append(this_one)

        # Another is look at the user's activity feed.
        this_one = {'errback': self.squashIrrelevantErrors}
        this_one['url'] = ('http://github.com/%s.json' %
            mysite.base.unicode_sanity.quote(self.query))
        this_one['callback'] = self.handleUserActivityFeedJson
        urls_and_callbacks.append(this_one)

        # Another is look at the watched list for repos the user collaborates on
        # FIXME

        return urls_and_callbacks

    def handleUserActivityFeedJson(self, json_string):
        # first, decode it
        data = simplejson.loads(json_string)

        # create a set that we add URLs to. This way, we can avoid
        # returning duplicate URLs.
        repo_urls_found = set()

        for event in data:
            if 'repository' not in event:
                print 'weird, okay'
                continue
            repo = event['repository']
            # Find "collaborated on..."
            if event['type'] == 'PushEvent':
                if repo['owner'] != self.query:
                    ## In that case, we need to find out if the given user is in the list of collaborators
                    ## for the repository. Normally I would call out to a different URL, but I'm supposed to
                    ## not block.
                    ## FIXME: return a Deferred I guess.
                    continue # skip the event for now
            # Find "forked..."
            elif event['type'] == 'ForkEvent':
                if repo['owner'] != self.query:
                    self.addCitationFromRepoDict(repo, override_contrib='Collaborated on')
            elif event['type'] == 'WatchEvent':
                continue # Skip this event.
            else:
                logging.info("When looking in the Github user feed, I found a Github event of unknown type.")

class LaunchpadProfilePageScraper(ProfileImporter):
    SQUASH_THESE_HTTP_CODES = ['404',]

    def getUrlsAndCallbacks(self):
        # If the query has an '@' in it, enqueue a task to
        # find the username.
        if '@' in self.query:
            return [self.getUrlAndCallbackForEmailLookup()]
        else:
            return [self.getUrlAndCallbackForProfilePage()]

    def getUrlAndCallbackForEmailLookup(self, query=None):
        if query is None:
            query = self.query

        this_one = {}
        this_one['url'] = ('https://api.launchpad.net/1.0/people?' +
                           'ws.op=find&text=' +
                           mysite.base.unicode_sanity.quote(
                               query))
        this_one['callback'] = self.parseAndProcessUserSearch
        this_one['errback'] = self.squashIrrelevantErrors
        return this_one

    def getUrlAndCallbackForProfilePage(self, query=None):
        if query is None:
            query = self.query
        # Enqueue a task to actually get the user page
        this_one = {}
        this_one['url'] = ('https://launchpad.net/~' +
                           mysite.base.unicode_sanity.quote(query))
        this_one['callback'] = self.parseAndProcessProfilePage
        this_one['errback'] = self.squashIrrelevantErrors
        return this_one
    
    def parseAndProcessProfilePage(self, profile_html):
        PROJECT_NAME_FIXUPS = {
            'Launchpad itself': 'Launchpad',
            'Debian': 'Debian GNU/Linux'}

        doc_u = unicode(profile_html, 'utf-8')
        tree = lxml.html.document_fromstring(doc_u)
        
        contributions = {}
        # Expecting html like this:
        # <table class='contributions'>
        #   <tr>
        #       ...
        #       <img title='Bug Management' />
        #
        # It generates a list of dictionaries like this:
## {
##         'F-Spot': {
##             'url': 'http://launchpad.net/f-spot',
##             'involvement_types': ['Bug Management', 'Bazaar Branches'],
##             'languages' : ['python', 'shell script']
##         }
##        }
        # Extract Launchpad username from page
        if not tree.cssselect('#launchpad-id dd'):
            return # Well, there's no launchpad ID here, so that's that.
        username = tree.cssselect('#launchpad-id dd')[0].text_content().strip()
        for row in tree.cssselect('.contributions tr'):
            project_link = row.cssselect('a')[0]
            project_name = project_link.text_content().strip()
            # FIXUPs: Launchpad uses some weird project names:
            project_name = PROJECT_NAME_FIXUPS.get(project_name,
                                                   project_name)

            project_url_relative = project_link.attrib['href']
            project_url = urlparse.urljoin('https://launchpad.net/',
                                           project_url_relative)
        
            involvement_types = [
                i.attrib.get('title', '').strip()
                for i in row.cssselect('img')]
            contributions[project_name] = {
                'involvement_types': set([k for k in involvement_types if k]),
                'url': project_url,
                'citation_url': "https://launchpad.net/~" + username,
                }

        # Now create Citations for those facts
        for project_name in contributions:
            self._save_parsed_launchpad_data_in_database(
                project_name, contributions[project_name])

    def _save_parsed_launchpad_data_in_database(self, project_name, result):
        dia = self.get_dia()
        person = dia.person
        
        for involvement_type in result['involvement_types']:

            (project, _) = mysite.search.models.Project.objects.get_or_create(name=project_name)

            # This works like a 'get_first_or_create'.
            # Sometimes there are more than one existing PortfolioEntry
            # with the details in question.
            # FIXME: This is untested.
            if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
                portfolio_entry = mysite.profile.models.PortfolioEntry(person=person, project=project)
                portfolio_entry.save()
            portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]

            citation = mysite.profile.models.Citation()
            citation.contributor_role = involvement_type
            citation.portfolio_entry = portfolio_entry
            citation.data_import_attempt = dia
            citation.url = result['citation_url']
            citation.save_and_check_for_duplicates()

    def parseAndProcessUserSearch(self, user_search_json):
        data = simplejson.loads(user_search_json)
        if data['total_size']:
            entry = data['entries'][0]
        else:
            # No matches. How sad.
            return

        username = entry['name']
        # Now enqueue a task to do the real work.
        self.command.call_getPage_on_data_dict(self,
            self.getUrlAndCallbackForProfilePage(query=username))

class BitbucketImporter(ProfileImporter):
    ROOT_URL = 'http://api.bitbucket.org/1.0/'
    SQUASH_THESE_HTTP_CODES = ['404',]

    def getUrlsAndCallbacks(self):
        return [{
            'errback': self.squashIrrelevantErrors,
            'url': self.url_for_query(self.query),
            'callback': self.processUserJson,
            }]

    def url_for_query(self, query):
        url = self.ROOT_URL
        url += 'users/%s/' % (mysite.base.unicode_sanity.quote(self.query))
        return url

    def url_for_project(self, user_name, project_name):
        return 'http://bitbucket.org/%s/%s/' % (
            mysite.base.unicode_sanity.quote(user_name),
            mysite.base.unicode_sanity.quote(project_name))

    def processUserJson(self, json_string):
        person = self.get_dia().person

        json_data = simplejson.loads(json_string)

        bitbucket_username = json_data['user']['username']
        repositories = json_data['repositories']
        ### The repositories list contains a sequence of dictionaries.
        ### The keys are:
        # slug: The url slug for the project
        # name: The name of the project
        # website: The website associated wit the project, defined by the user
        # followers_count: Number of followers
        # description: The project description
        
        for repo in repositories:
            # The project name and description we pull out of the data
            # provided by Bitbucket.
            project_name = repo['name']
            slug = repo['slug']
            description = repo['description']

            # Get the corresponding project object, if it exists.
            (project, _) = mysite.search.models.Project.objects.get_or_create(
                name=repo['slug'])

            # Get the most recent PortfolioEntry for this person and that
            # project.
            #
            # If there is no such PortfolioEntry, then set its project
            # description to the one provided by Bitbucket.
            portfolio_entry, _ = mysite.profile.models.PortfolioEntry.objects.get_or_create(
                person=person,
                project=project,
                defaults={'project_description':
                          description.rstrip() or project_name})
            # Create a Citation that links to the Bitbucket page
            citation, _ = mysite.profile.models.Citation.objects.get_or_create(
                url = self.url_for_project(bitbucket_username,
                                           slug),
                portfolio_entry = portfolio_entry,
                defaults = dict(
                    contributor_role='Contributed to a repository on Bitbucket.',
                    data_import_attempt = self.get_dia(),
                    languages=''))
            citation.languages = ''
            citation.save_and_check_for_duplicates()

class AbstractOhlohAccountImporter(ProfileImporter):
    SQUASH_THESE_HTTP_CODES = ['404',]

    def convert_ohloh_contributor_fact_to_citation(self, ohloh_contrib_info, project_data):
        """Create a new Citation from a dictionary roughly representing an Ohloh ContributionFact."""
        # {{{
        # FIXME: Enforce uniqueness on (source, vcs_committer_identifier, project)
        # Which is to say, overwrite the previous citation with the same source,
        # vcs_committer_identifier and project.
        # FIXME: Also store ohloh_contrib_info somewhere so we can parse it later.
        # FIXME: Also store the launchpad HttpResponse object somewhere so we can parse it l8r.
        # "We'll just pickle the sucker and throw it into a database column. This is going to be
        # very exciting. just Hhhomphf." -- Asheesh.
        permalink = self.generate_contributor_url(
            project_data['url_name'],
            int(ohloh_contrib_info['contributor_id']))
        self.command.call_getPage_on_data_dict(
            self,
            {'url': permalink,
             'callback': lambda _ignored:
                 self.convert_ohloh_contributor_fact_and_contributor_url_to_citation(ohloh_contrib_info, project_data, permalink),
             'errback': lambda _ignored:
                 self.convert_ohloh_contributor_fact_and_contributor_url_to_citation(ohloh_contrib_info, project_data, None)})
        
    def convert_ohloh_contributor_fact_and_contributor_url_to_citation(self, ohloh_contrib_info, project_data, contributor_url):
        (project, _) = mysite.search.models.Project.objects.get_or_create(
            name__iexact=project_data['name'],
            defaults={'name': project_data['name']})
        (portfolio_entry, _) = mysite.profile.models.PortfolioEntry.objects.get_or_create(
                person=self.get_dia().person, project=project)

        citation = mysite.profile.models.Citation()
        citation.distinct_months = int(ohloh_contrib_info.get('man_months', 0)) or None
        citation.languages = project_data.get('primary_language_nice_name', '')
        citation.url = contributor_url
        citation.data_import_attempt = self.get_dia()
        citation.portfolio_entry = portfolio_entry
        citation.save_and_check_for_duplicates()
        return citation

    def url_for_ohloh_query(self, url, params=None, API_KEY=None):
        if API_KEY is None:
            from django.conf import settings
            API_KEY = settings.OHLOH_API_KEY

        my_params = {u'api_key': unicode(API_KEY)}
        if params:
            my_params.update(params)
        params = my_params ; del my_params

        encoded = mysite.base.unicode_sanity.urlencode(params)
        if url[-1] != '?':
            url += u'?'

        url += encoded
        return url

    def parse_ohloh_xml(self, xml_string):
        try:
            s = xml_string
            tree = ET.parse(StringIO.StringIO(s))
        except (xml.parsers.expat.ExpatError, SyntaxError):
            # well, I'll be. it doesn't parse.
            # There's nothing to do.
            return None

        # Did Ohloh return an error?
        root = tree.getroot()
        if root.find('error') is not None:
            # FIXME: We could log this, but for now, we'll just eat it.
            return None # The callback chain is over.

        return tree

    def xml_tag_to_dict(self, tag):
        '''This method turns the input tag into a dictionary of
        Unicode strings.

        We use this across the Ohloh import code because I feel more
        comfortable passing native Python dictionaries around, rather
        than thick, heavy XML things.

        (That, and dictionaries are easier to use in the test suite.'''
        this = {}
        for child in tag.getchildren():
            if child.text:
                this[unicode(child.tag)] = force_unicode(child.text)
        return this

    def filter_ohloh_xml(self, root, selector, many=False):
        relevant_tag_dicts = []
        interestings = root.findall(selector)
        for interesting in interestings:
            this = self.xml_tag_to_dict(interesting)
            # Good, now we have a dictionary version of the XML tag.
            if many:
                relevant_tag_dicts.append(this)
            else:
                return this

        if many:
            return relevant_tag_dicts

    def generate_contributor_url(self, project_name, contributor_id):
        '''Returns either a nice, deep link into Ohloh for data on the contribution,
        or None if such a link could not be made.'''
        nice_url = 'https://www.ohloh.net/p/%s/contributors/%d' % (
            project_name.lower(), contributor_id)
        return nice_url

    def filter_out_irrelevant_ohloh_dicts(self, data_dicts):
        out = []
        for data_dict in data_dicts:
            if data_dict.get('contributor_name', '').lower() != self.query.lower():
                continue # If we were asked-to, we can skip data dicts that are irrelevant.
            out.append(data_dict)
        return out

    def parse_then_filter_then_interpret_ohloh_xml(self, xml_string, filter_out_based_on_query=True):
        tree = self.parse_ohloh_xml(xml_string)
        if tree is None:
            return

        list_of_dicts = self.filter_ohloh_xml(tree, 'result/contributor_fact', many=True)
        if not list_of_dicts:
            return

        if filter_out_based_on_query:
            list_of_dicts = self.filter_out_irrelevant_ohloh_dicts(list_of_dicts)

        ### Now that we have as much information as we do, we pass each dictionary
        ### individually to a function that creates a Citation.
        ###
        ### To do that, it might have to make some more web requests.
        for data_dict in list_of_dicts:
            self.get_analysis_data_then_convert(data_dict)

    def get_analysis_data_then_convert(self, c_f):
        url = self.url_for_ohloh_query('http://www.ohloh.net/analyses/%d.xml' % int(c_f['analysis_id']))
        callback = lambda xml_string: self.parse_analysis_data_and_get_project_data_then_convert(xml_string, c_f)
        errback = self.squashIrrelevantErrors
        self.command.call_getPage_on_data_dict(
            self,
            {'url': url,
             'callback': callback,
             'errback': errback})

    def parse_analysis_data_and_get_project_data_then_convert(self, analysis_data_xml_string, c_f):
        # We are interested in grabbing the Ohloh project ID out of the project analysis
        # data dump.
        tree = self.parse_ohloh_xml(analysis_data_xml_string)
        if tree is None:
            return
        
        analysis_data = self.filter_ohloh_xml(tree, 'result/analysis', many=False)
        # Now we go look for the project data XML blob.
        return self.get_project_data_then_continue(int(analysis_data['project_id']), c_f)

    def get_project_data_then_continue(self, project_id, c_f):
        url = self.url_for_ohloh_query('http://www.ohloh.net/projects/%d.xml' % project_id)
        callback = lambda xml_string: self.parse_project_data_then_convert(xml_string, c_f)
        errback = self.squashIrrelevantErrors # No error recovery available to us
        self.command.call_getPage_on_data_dict(
            self,
            {'url': url,
             'callback': callback,
             'errback': errback})

    def parse_project_data_then_convert(self, project_data_xml_string, c_f):
        tree = self.parse_ohloh_xml(project_data_xml_string)
        if tree is None:
            return
        
        project_data = self.filter_ohloh_xml(tree, 'result/project', many=False)
        if not project_data:
            return

        self.convert_ohloh_contributor_fact_to_citation(c_f, project_data)
        
class RepositorySearchOhlohImporter(AbstractOhlohAccountImporter):
    BASE_URL = 'http://www.ohloh.net/contributors.xml'

    def getUrlsAndCallbacks(self):
        url = self.url_for_ohloh_query(url=self.BASE_URL,
                                       params={u'query': self.query})

        return [{
                'url': url,
                'errback': self.squashIrrelevantErrors,
                'callback': self.parse_then_filter_then_interpret_ohloh_xml}]

###

class OhlohUsernameImporter(AbstractOhlohAccountImporter):

    def getUrlsAndCallbacksForUsername(self, username):
        # First, we load download the user's profile page and look for
        # (project, contributor_id) pairs.
        #
        # Then, eventually, we will ask the Ohloh API about each of
        # those projects.
        #
        # It would be nice if there were a way to do this using only
        # the Ohloh API, but I don't think there is.

        # FIXME: Handle unicode input for username

        return [{
                'url': ('https://www.ohloh.net/accounts/%s' %
                        urllib.quote(username)),
                'callback': self.process_user_page,
                'errback': self.squashIrrelevantErrors}]

    def getUrlsAndCallbacks(self):
        # First, we load download the user's profile page and look for
        # (project, contributor_id) pairs.
        #
        # Then, eventually, we will ask the Ohloh API about each of
        # those projects.
        #
        # It would be nice if there were a way to do this using only
        # the Ohloh API, but I don't think there is.
        if '@' in self.query:
            # To handle email addresses with Ohloh, all we have to do
            # is turn them into their MD5 hashes.
            #
            # If an account with that username exists, then Ohloh will redirect
            # us to the actual account page.
            #
            # If not, we will probably get a 404.
            hasher = hashlib.md5(); hasher.update(self.query)
            hashed = hasher.hexdigest()
            query = hashed
        else:
            # If it is not an email address, we can just pass it straight through.
            query = self.query

        return self.getUrlsAndCallbacksForUsername(query)

    def getUrlAndCallbackForProjectAndContributor(self, project_name,
                                                  contributor_id):
        base_url = 'https://www.ohloh.net/p/%s/contributors/%d.xml' % (
            urllib.quote(project_name), contributor_id)

        # Since we know that the contributor ID truly does correspond
        # to this OpenHatch user, we pass in filter_out_based_on_query=False.
        #
        # The parse_then_... method typically checks each Ohloh contributor_fact
        # to make sure it is relevant. Since we know they are all relevant,
        # we can skip that check.
        callback = lambda data: self.parse_then_filter_then_interpret_ohloh_xml(data, filter_out_based_on_query=False)

        return {'url': self.url_for_ohloh_query(base_url),
                'callback': callback,
                'errback': self.squashIrrelevantErrors}

    def process_user_page(self, html_string):
        root = lxml.html.parse(StringIO.StringIO(html_string)).getroot()
        relevant_links = root.cssselect('a.position')
        relevant_hrefs = [link.attrib['href'] for link in relevant_links if '/contributors/' in link.attrib['href']]
        relevant_project_and_contributor_id_pairs = []

        for href in relevant_hrefs:
            url_name, contributor_id = re.split('[/][a-z]+[/]', href, 1
                                               )[1].split('/contributors/')
            self.process_url_name_and_contributor_id(
                url_name, int(contributor_id))

    def process_url_name_and_contributor_id(self, url_name, contributor_id):
        # The Ohloh url_name that we get back is not actually enough to get the project information
        # we need. So we have to first convert it into an Ohloh project id.
        #
        # The only way I can see to do that is to load up the project page, and look
        # for the badge image URL. It contains the project ID.
        #
        # FIXME: Maybe if we use the "position" ID (also available through an image, namely the
        # activity chart), we skip a scraping step. Who knows.
        url = 'https://www.ohloh.net/p/%s' % url_name
        callback = lambda page_text: self.get_project_id_then_continue(page_text, contributor_id)
        errback = self.squashIrrelevantErrors # There is no going back.
        self.command.call_getPage_on_data_dict(
            self,
            {'url': url,
             'callback': callback,
             'errback': errback})

    def get_project_id_then_continue(self, project_page_text, contributor_id):
        # First, extract the project ID from the page text
        file_descriptor_wrapping_contents = StringIO.StringIO(project_page_text)
        parsed = lxml.html.parse(file_descriptor_wrapping_contents).getroot()
        badge_images = parsed.cssselect('.badge_preview img')
        if not badge_images:
            return # Oh, well.
        badge_image_link = badge_images[0].attrib['src']
        badge_image_link_parsed = [x for x in badge_image_link.split('/') if x]
        project_id = int(badge_image_link_parsed[1])

        ### We'll need to get the the ContributorFact XML blob before anything else goes on
        self.command.call_getPage_on_data_dict(
            self,
            {'url': self.url_for_ohloh_query(
                    'https://www.ohloh.net/p/%d/contributors/%d.xml' %
                    (project_id, contributor_id)),
             'callback': lambda xml_string: self.parse_contributor_facts_then_continue(xml_string, project_id),
             'errback': self.squashIrrelevantErrors})

    def parse_contributor_facts_then_continue(self, xml_string, project_id):
        tree = self.parse_ohloh_xml(xml_string)
        if tree is None:
            return
        
        c_f = self.filter_ohloh_xml(tree, 'result/contributor_fact', many=False)
        if not c_f:
            return

        # Now we go look for the project data XML blob.
        return self.get_project_data_then_continue(project_id, c_f)
###

SOURCE_TO_CLASS = {
    'bb': BitbucketImporter,
    'gh': GithubImporter,
    'lp': LaunchpadProfilePageScraper,
    'rs': RepositorySearchOhlohImporter,
    'oh': OhlohUsernameImporter,
}
