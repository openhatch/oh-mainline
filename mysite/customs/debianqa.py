import lxml.html
import urllib
import mysite.customs.ohloh

# FIXME: Migrate this to UltimateDebianDatabase or DebianDatabaseExport

def source_packages_maintained_by(email_address):
    htmler = lxml.etree.HTMLParser(encoding='utf-8')
    url = 'http://qa.debian.org/developer.php?' + urllib.urlencode(dict(
            login='asheesh@asheesh.org'))
    response = mysite.customs.ohloh.mechanize_get(url).response()
    parsed = lxml.html.parse(response).getroot()

    # for each H3 (Like "main" or "non-free" or "Non-maintainer uploads",
    # grab that H3 to figure out the heading.
    for section in parsed.cssselect('h3'):
        
    # then look for the next sibling which is a table.

    # NOTE
    # this assumes that there are as many H3s

    for relevant_table in parsed.cssselect('h3+table'):
        # First, figure out what the point of this table is.
        # FIXME find the h3!
        
        # Skip non-maintainer uploads.
        

    return parsed

    
                                                                   
