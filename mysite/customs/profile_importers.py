import mysite.base.unicode_sanity
import lxml.html
import urllib
import urllib2
import mysite.customs.ohloh
import cStringIO as StringIO
import re

### This section imports package lists from qa.debian.org

SECTION_NAME_AND_NUMBER_SPLITTER = re.compile(r'(.*?) [(](\d+)[)]$')
# FIXME: Migrate this to UltimateDebianDatabase or DebianDatabaseExport

class DebianQA(object):
    def __init__(self, query, dia_id):
        self.query = query
        # dia_id can be None if you don't want to test citation creation
        self.dia_id = dia_id 

    def getUrl(self):
        if '@' in self.query:
            email_address = self.query
        else:
            email_address = self.query + '@debian.org'

        url = 'http://qa.debian.org/developer.php?' + mysite.base.unicode_sanity.urlencode({
            u'login': unicode(email_address)})
        return url

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

        for package_name, package_description in results:
            (project, _) = Project.objects.get_or_create(name=package_name)

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
            (project, _) = Project.objects.get_or_create(name='Debian GNU/Linux')
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
