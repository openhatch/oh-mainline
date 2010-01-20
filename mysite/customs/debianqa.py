import lxml.html
import urllib
import mysite.customs.ohloh
import re

SECTION_NAME_AND_NUMBER_SPLITTER = re.compile(r'(.*?) [(](\d+)[)]$')
# FIXME: Migrate this to UltimateDebianDatabase or DebianDatabaseExport

def source_packages_maintained_by(email_address):
    htmler = lxml.etree.HTMLParser(encoding='utf-8')
    url = 'http://qa.debian.org/developer.php?' + urllib.urlencode(dict(
            login='asheesh@asheesh.org'))
    response = mysite.customs.ohloh.mechanize_get(url).response()
    parsed = lxml.html.parse(response).getroot()

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
            num_added += 1
            package_names.append(package_name)

        assert num_added == int(number_of_packages)

    return package_names
