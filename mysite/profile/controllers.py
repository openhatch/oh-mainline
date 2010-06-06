import os.path
import sha
from itertools import izip, cycle, islice

import pygeoip

from django.conf import settings

import mysite.search.controllers
import mysite.search.models
import mysite.profile.models
import mysite.base.decorators

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

class RecommendBugs(object):
    def __init__(self, terms, n):
        self.terms = terms
        self.n = n

    def get_cache_key(self):
        prefix = 'bug_recommendation_cache_'
        bug_epoch = mysite.search.models.Epoch.get_for_model(
            mysite.search.models.Bug)
        suffix_input = [self.terms, self.n, bug_epoch]
        return prefix + '_' + sha.sha(repr(suffix_input)).hexdigest()

    def recommend(self):
        ret = []
        for bug_id in self._recommend_as_list():
            try:
                bug = mysite.search.models.Bug.all_bugs.get(pk=bug_id)
            except mysite.search.models.Bug.DoesNotExist:
                logging.info("WTF, bug missing. Whatever.")
                continue
            ret.append(bug)
        return ret

    @mysite.base.decorators.cache_method('get_cache_key')
    def _recommend_as_list(self):
        return list(self._recommend_as_generator())
    
    def _recommend_as_generator(self):
        '''Input: A list of terms, like ['Python', 'C#'], designed for use in the search engine.

        I am a generator that yields Bug objects.
        I yield up to n Bugs in a round-robin fashion.
        I don't yield a Bug more than once.'''
        
        distinct_ids = set()

        lists_of_bugs = [
            mysite.search.controllers.order_bugs(
                mysite.search.controllers.Query(terms=[t]).get_bugs_unordered())
            for t in self.terms]
        number_emitted = 0

        for bug in roundrobin(*lists_of_bugs):
            if number_emitted >= self.n:
                raise StopIteration
            if bug.id in distinct_ids:
                continue
            # otherwise...
            number_emitted += 1
            distinct_ids.add(bug.id)
            yield bug.id

class PeopleMatcher(object):
    def get_cache_key(self, *args, **kwargs):
        keys = (mysite.search.models.Epoch.get_for_model(
            mysite.profile.models.Link_Person_Tag),
                args)
        return sha.sha(repr(keys)).hexdigest()

    def people_matching(self, property, value):
        return mysite.profile.models.Person.objects.filter(
            pk__in=self._people_matching_ids(property, value))

    @mysite.base.decorators.cache_method('get_cache_key')
    def _people_matching_ids(self, property, value):
        links = mysite.profile.models.Link_Person_Tag.objects.filter(
            tag__tag_type__name=property, tag__text__iexact=value)
        peeps = [l.person for l in links]
        sorted_peeps = sorted(set(peeps), key = lambda thing: (thing.user.first_name, thing.user.last_name))
        return [person.id for person in sorted_peeps]

_pm = PeopleMatcher()
people_matching = _pm.people_matching

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

    gimme = lambda x: all_data_about_this_ip.get(x, '')

    pieces = [gimme('city')]

    # Only add the region name if it's a string. Otherwise we add numbers to
    # the location, which can be confusing.
    region_name = gimme('region_name'),
    try:
        int(region_name)
    except ValueError:
        pieces.append(region_name)

    pieces.append(gimme('country_name'))

    as_string = ', '.join([p for p in pieces if p])
    as_unicode = unicode(as_string, 'Latin-1')

    if as_unicode:
        return True, as_unicode
    return False, u''

def parse_string_query(s):
    parsed = {}
    valid_prefixes = ['project', 'icanhelp']
    valid_prefixes.extend(mysite.profile.models.TagType.short_name2long_name.keys())

    pieces_from_splitting_on_first_colon = s.split(':', 1)
    if (len(pieces_from_splitting_on_first_colon) > 1 and
        pieces_from_splitting_on_first_colon[0] in valid_prefixes):
        first, rest = pieces_from_splitting_on_first_colon
        parsed['query_type'], parsed['q'] = first, rest
    else:
        parsed['query_type'] = 'all_tags'
        parsed['q'] = s

    # Now, clean up the q to parse out qutiation marks
    parsed['q'] = parsed['q'].strip() # trim whitespace
    if len(parsed['q']) >= 2 and (
        parsed['q'][0] == '"' == parsed['q'][-1]):
        parsed['q'] = parsed['q'][1:-1]

    return parsed
