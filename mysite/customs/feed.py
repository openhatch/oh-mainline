import lxml.html
import feedparser
from django.core.cache import cache

OPENHATCH_BLOG_FEED_URL='http://openhatch.org/blog/feed/atom/'

def summary2html(html_string):
    decoded = lxml.html.fragment_fromstring('<div>' + html_string + '</div>')
    text = decoded.text_content()
    return unicode(text)

def _blog_entries():
    parsed = feedparser.parse(OPENHATCH_BLOG_FEED_URL)
    for entry in parsed['entries']:
        entry['unicode_text'] = summary2html(entry['summary'])
    return parsed['entries']

def cached_blog_entries():
    key_name = 'blog_entries'
    entries = cache.get(key_name)
    if entries is None:
        entries = _blog_entries()
        # cache it for 30 minutes
        cache.set(key_name, entries, 30 * 60)
    return entries

