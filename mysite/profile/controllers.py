import mysite.search.controllers
import mysite.profile.models
from itertools import izip, cycle, islice
import pygeoip
from django.conf import settings
import os.path

## roundrobin() taken from http://docs.python.org/library/itertools.html

def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))

def recommend_bugs(terms, n):
    '''Input: A list of terms, like ['Python', 'C#'], designed for use in the search engine.

    I am a generator that yields Bug objects.
    I yield up to n Bugs in a round-robin fashion.
    I don't yield a Bug more than once.'''

    distinct_ids = set()

    lists_of_bugs = [
        mysite.search.controllers.order_bugs(
            mysite.search.controllers.Query(terms=[t]).get_bugs_unordered())
        for t in terms]
    number_emitted = 0
        
    for bug in roundrobin(*lists_of_bugs):
        if number_emitted >= n:
            raise StopIteration
        if bug.id not in distinct_ids:
            number_emitted += 1
            distinct_ids.add(bug.id)
            yield bug

def people_matching(property, value):
    links = mysite.profile.models.Link_Person_Tag.objects.filter(
        tag__tag_type__name=property, tag__text__iexact=value)
    peeps = [l.person for l in links]
    sorted_peeps = sorted(set(peeps), key = lambda thing: (thing.user.first_name, thing.user.last_name))
    return sorted_peeps

geoip_database = None
def get_geoip_guess_for_ip(ip_as_string):
    # initialize database
    global geoip_database
    if geoip_database is None:
        # FIXME come up with reliable path place
        try:
            geoip_database = pygeoip.GeoIP(os.path.join(settings.MEDIA_ROOT,
                                                        '../../downloads/GeoLiteCity.dat'))
        except IOError:
            return False, u'' # maybe log this?
    
    all_data_about_this_ip = geoip_database.record_by_addr(ip_as_string)

    if all_data_about_this_ip is None:
        return False, ''

    things_we_like = all_data_about_this_ip.get('city', ''), all_data_about_this_ip.get('region_name', ''), all_data_about_this_ip.get('country_name', '')

    as_string = ', '.join([portion for portion in things_we_like if portion])
    as_unicode = unicode(as_string, 'Latin-1')

    if as_unicode:
        return True, as_unicode
    return False, u''

def parse_string_query(s):
    parsed = {}
    if s.startswith('project:'):
        parsed['query_type'] = 'project'
        parsed['q'] = s.split(':',1)[1]
    else:
        parsed['query_type'] = 'all_tags'
        parsed['q'] = s

    # Now, clean up the q to parse out qutiation marks
    parsed['q'] = parsed['q'].strip() # trim whitespace
    if len(parsed['q']) >= 2 and (
        parsed['q'][0] == '"' == parsed['q'][-1]):
        parsed['q'] = parsed['q'][1:-1]

    return parsed
