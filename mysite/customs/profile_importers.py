import mysite.base.unicode_sanity
import lxml.html
import urllib
import urllib2
import mysite.customs.ohloh
import cStringIO as StringIO
import re
import simplejson
import datetime

import mysite.search.models
import mysite.profile.models
import mysite.base.helpers

import twisted.web

### Generic error handler
class ProfileImporter(object):
    def __init__(self, query, dia_id):
        raise NotImplementedException

    def handleError(self, failure):
        import logging
        logging.warn(failure)

### This section imports projects from github.com
class GithubImporter(ProfileImporter):
    def __init__(self, query, dia_id):
        self.query = query
        self.dia_id = dia_id

    @staticmethod
    def squashIrrelevantErrors(error):
        squash_it = False

        if error.type == twisted.web.error.Error:
            if error.value.status == '404':
                # It's cool.
                squash_it = True
            if error.value.response == '{"error":"api route not recognized"}':
                # also cool.
                squash_it = True

        if squash_it:
            return None
        return error

    # This method takes a repository dict as returned by Github
    # and creates a Citation, also creating the relevant
    # PortfolioEntry if necessary.
    def addCitationFromRepoDict(self, repo_dict, override_contrib=None):
        # Get the DIA whose ID we stored
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=self.dia_id)
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
        repos = data['repositories']
        # for every repository, we need to get its primary
        # programming language. FIXME.
        # For now we skip that.
        for repo in repos:
            self.addCitationFromRepoDict(repo)

        dia = mysite.profile.models.DataImportAttempt.objects.get(id=self.dia_id)
        person = dia.person

        person.last_polled = datetime.datetime.now()
        person.save()

        dia.completed = True
        dia.save()

    def getUrlsAndCallbacks(self):
        urls_and_callbacks = []

        # Well, one thing we can do is get the repositories the user owns.
        this_one = {'errback': GithubImporter.squashIrrelevantErrors}
        this_one['url'] = ('http://github.com/api/v2/json/repos/show/' +
            mysite.base.unicode_sanity.quote(self.query))
        this_one['callback'] = self.handleUserRepositoryJson
        urls_and_callbacks.append(this_one)

        # Another is look at the user's activity feed.
        this_one = {'errback': GithubImporter.squashIrrelevantErrors}
        this_one['url'] = ('http://github.com/%s.json' %
            mysite.base.unicode_sanity.quote(self.query))
        this_one['callback'] = self.handleUserActivityFeedJson
        urls_and_callbacks.append(this_one)

        # Another is look at the watched list for repos the user collaborates on
        # FIXME

        return urls_and_callbacks

    def handleUserActivityFeedJson(self, json_string):
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=self.dia_id)
        # first, decode it
        data = simplejson.loads(json_string)

        # create a set that we add URLs to. This way, we can avoid
        # returning duplicate URLs.
        repo_urls_found = set()

        for event in data:
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

### This section imports package lists from qa.debian.org

SECTION_NAME_AND_NUMBER_SPLITTER = re.compile(r'(.*?) [(](\d+)[)]$')
# FIXME: Migrate this to UltimateDebianDatabase or DebianDatabaseExport

class DebianQA(ProfileImporter):
    def __init__(self, query, dia_id):
        self.query = query
        # dia_id can be None if you don't want to test citation creation
        self.dia_id = dia_id 

    def getUrlsAndCallbacks(self):
        if '@' in self.query:
            email_address = self.query
        else:
            email_address = self.query + '@debian.org'

        url = 'http://qa.debian.org/developer.php?' + mysite.base.unicode_sanity.urlencode({
            u'login': unicode(email_address)})
        return [ {
            'url': url,
            'callback': self.handlePageContents } ]

    def handlePageContents(self, contents):
        '''contents is a string containing the data the web page contained.
        '''
        file_descriptor_wrapping_contents = StringIO.StringIO(contents)

        parsed = lxml.html.parse(file_descriptor_wrapping_contents).getroot()
        
        package_names = self._package_names_from_parsed_document(parsed)
        self._create_citations_from_package_names(package_names)

    def _package_names_from_parsed_document(self, parsed):
        # for each H3 (Like "main" or "non-free" or "Non-maintainer uploads",
        # grab that H3 to figure out the heading. These h3s have a table right next
        # to them in the DOM.
        package_names = []

        for relevant_table in parsed.cssselect('h3+table'):
            num_added = 0
        
            h3 = relevant_table.getprevious()
            table = relevant_table

            h3_text = h3.text_content()
            # this looks something like "main (5)"
            section, number_of_packages = SECTION_NAME_AND_NUMBER_SPLITTER.match(h3_text).groups()

            # Trim trailing whitespace
            section = section.strip()

            # If the section is "Non-maintainer uploads", skip it for now.
            # That's because, for now, this importer is interested only in
            # what packages the person maintains.
            if section == 'Non-maintainer uploads':
                continue

            for package_bold_name in table.cssselect('tr b'):
                package_name = package_bold_name.text_content()
                package_description = package_bold_name.cssselect('span')[0].attrib['title']
                num_added += 1
                package_names.append( (package_name, package_description) )

            assert num_added == int(number_of_packages)

        return package_names

    def _create_citations_from_package_names(self, package_names):
        dia = mysite.profile.models.DataImportAttempt.objects.get(id=self.dia_id)
        person = dia.person

        for package_name, package_description in package_names:
            (project, _) = mysite.search.models.Project.objects.get_or_create(name=package_name)

            package_link = 'http://packages.debian.org/src:' + urllib.quote(
                package_name)

            if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
                portfolio_entry = mysite.profile.models.PortfolioEntry(person=person,
                                                 project=project,
                                                 project_description=package_description)
                portfolio_entry.save()
            portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]
    
            citation = mysite.profile.models.Citation()
            citation.languages = "" # FIXME ", ".join(result['languages'])
            citation.contributor_role='Maintainer'
            citation.portfolio_entry = portfolio_entry
            citation.data_import_attempt = dia
            citation.url = package_link
            citation.save_and_check_for_duplicates()

            # And add a citation to the Debian portfolio entry
            (project, _) = mysite.search.models.Project.objects.get_or_create(name='Debian GNU/Linux')
            if mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project).count() == 0:
                portfolio_entry = mysite.profile.models.PortfolioEntry(person=person,
                                                 project=project,
                                                 project_description=
                                                 'The universal operating system')
                portfolio_entry.save()
            portfolio_entry = mysite.profile.models.PortfolioEntry.objects.filter(person=person, project=project)[0]
            citation = mysite.profile.models.Citation()
            citation.languages = '' # FIXME: ?
            citation.contributor_role='Maintainer of %s' % package_name
            citation.portfolio_entry = portfolio_entry
            citation.data_import_attempt = dia
            citation.url = package_link
            citation.save_and_check_for_duplicates()

        person.last_polled = datetime.datetime.now()
        person.save()

        dia.completed = True
        dia.save()

###

SOURCE_TO_CLASS = {
    'db': DebianQA,
    'gh': GithubImporter,
}

