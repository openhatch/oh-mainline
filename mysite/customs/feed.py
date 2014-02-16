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


def summary2html(html_string):
    soup = BeautifulSoup.BeautifulSoup(
        html_string, convertEntities=BeautifulSoup.BeautifulSoup.ALL_ENTITIES)
    return u' '.join(soup.findAll(text=True))


def _blog_entries():
    try:
        text = requests.get(OPENHATCH_BLOG_FEED_URL, timeout=3).text
        content = text.encode('utf-8', 'ignore')
    except requests.exceptions.Timeout:
        content = ''

    parsed = feedparser.parse(content)
    for entry in parsed['entries']:
        entry['unicode_text'] = summary2html(entry['summary'])
        entry['title'] = summary2html(entry['title'])
    return parsed['entries']


def cached_blog_entries():
    key_name = 'blog_entries'
    entries = cache.get(key_name)
    if entries is None:
        entries = _blog_entries()
        # cache it for 30 minutes
        cache.set(key_name, entries, 30 * 60)
    return entries
