# This file is part of OpenHatch.
# Copyright (C) 2009 OpenHatch, Inc.
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

import BeautifulSoup

import feedparser
import requests
from django.core.cache import cache

OPENHATCH_BLOG_FEED_URL = 'http://openhatch.org/blog/feed/atom/'

# How long we're willing to wait for our call to download the blog to complete.
REQUEST_TIMEOUT = 3

# After this number of seconds we consider the blog feed stale and we'll start
# trying to refresh it.
BLOG_ENTRY_CACHE_TIMEOUT = 30 * 60

# The maximum number of seconds we'll keep blog entries in the cache. After
# this length of time the cached blog entries will be deleted even if we can't
# refresh the cache. This should be bigger than BLOG_ENTRY_CACHE_TIMEOUT and by
# an amount that covers blips or small outages in the openhatch blog feed.
STALENESS_TOLERANCE = 3 * 60 * 60

# These are keys that we shove into our cache.
KEY_PREFIX = 'blog_entries'
DATA_KEYNAME = KEY_PREFIX + '-data'
LOCK_KEYNAME = KEY_PREFIX + '-updatelock'
FRESHNESS_KEYNAME = KEY_PREFIX + '-datafresh'


def summary2html(html_string):
    soup = BeautifulSoup.BeautifulSoup(
        html_string, convertEntities=BeautifulSoup.BeautifulSoup.ALL_ENTITIES)
    return u' '.join(soup.findAll(text=True))


def _blog_entries():
    try:
        headers = {'User-Agent': 'OpenHatch oh-mainline blog feed fetcher'}
        text = requests.get(
            OPENHATCH_BLOG_FEED_URL, timeout=REQUEST_TIMEOUT, headers=headers).text
        content = text.encode('utf-8', 'ignore')
    except requests.exceptions.Timeout:
        content = ''

    parsed = feedparser.parse(content)
    for entry in parsed['entries']:
        entry['unicode_text'] = summary2html(entry['summary'])
        entry['title'] = summary2html(entry['title'])
    return parsed['entries']


class CacheLockInUse(Exception):
    pass


class CacheLock(object):
    """A super lame excuse for a lock.

    Provides a context manager for attempting to serialize access to some
    protected resource via operations in a cache. The gist is that if a key
    exists in the cache then that "lock" is taken. To acquire the lock then we
    see if no one else already holds it, and if so we set the key. There's an
    obvious and probable race condition here where two people do this at the
    same time and they both set the lock at the same time. The behavior here is
    that two people do the work we're trying to serialize. Not the end of the
    world.
    """
    def __init__(self, LOCK_KEYNAME):
        self.lock_keyname = LOCK_KEYNAME

    def acquire_lock(self):
        cache.set(self.lock_keyname, 'me', REQUEST_TIMEOUT + 1)

    def release_lock(self):
        cache.delete(self.lock_keyname)

    def __enter__(self):
        if cache.get(self.lock_keyname):
            raise CacheLockInUse()
        self.acquire_lock()

    def __exit__(self, type, value, traceback):
        self.release_lock()


def cached_blog_entries(
        blog_fetcher=_blog_entries,
        key_prefix=KEY_PREFIX):
    """Return a cached copy of blog entries that we've fetched.

    The parameters to this function are used for testing. The defaults are
    correct for actual usage.

    We use three cache keys to control whether or not we need to:

        - refresh our data
        - whether or not someone is already refreshing the copy
        - the actual cached content.

    Nominally we come in here the cache is fresh and the data is present. We do
    two cache reads. First to check that the freshness key hasn't expired.
    Since it hasn't we then issue a second cache read to get the cached blog
    entries.

    The second case we're likely to hit is that the freshness cache key returns
    None, which we use to mean expired. In that case we need to attempt to grab
    the updater lock, update the cache, and then return the freshly cached
    entries.

    Within that second case its possible that the lock will already be taken.
    In that case we simply return the cached data despite it being older than
    we really want.
    """
    blog_lock = CacheLock(key_prefix + LOCK_KEYNAME)

    # nominal case where the data is fresh and in the cache
    if cache.get(key_prefix + FRESHNESS_KEYNAME):
        entries = cache.get(key_prefix + DATA_KEYNAME)
        if entries:
            return entries

    # Data is stale, we'll try to update or just return the stale stuff
    try:
        with blog_lock:
            entries = blog_fetcher()
    except CacheLockInUse:
        return cache.get(key_prefix + DATA_KEYNAME)

    # set_many not used because of varying timeout settings
    cache.set(key_prefix + FRESHNESS_KEYNAME, 'yay', BLOG_ENTRY_CACHE_TIMEOUT)
    cache.set(key_prefix + DATA_KEYNAME, entries, STALENESS_TOLERANCE)
    return entries
