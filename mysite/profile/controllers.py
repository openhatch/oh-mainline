from mysite.search.views import get_bugs_by_query_words
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

def recommend_bugs(list_of_independent_terms, n):
    '''Search for each term in list_of_independent_terms.
    Return up to n results in a round-robin fashion.'''
    # FIXME: Add bug ID-based de-duplication.
    various_queries = [get_bugs_by_query_words([t]) for t in list_of_independent_terms]
    number_emitted = 0
        
    for bug in roundrobin(*various_queries):
        if number_emitted >= n:
            raise StopIteration
        number_emitted += 1
        yield bug
