import mysite.search.controllers
import mysite.profile.models
from itertools import izip, cycle, islice

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
