# This file is part of OpenHatch.
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
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
import logging
from httplib import BadStatusLine
from urllib2 import HTTPError
from urlparse import urlparse
import urllib2

import mechanize

import mysite.base.unicode_sanity
import mysite.customs.models


def mechanize_get(url, referrer=None, attempts_remaining=6, person=None):
    """Input: Some stuff regarding a web URL to request.
    Output: A browser instance that just open()'d that, plus an unsaved
    WebResponse object representing that browser's final state."""
    # if url is a Unicode object, make it utf-8 bytestring
    if type(url) == unicode:
        url = url.encode('utf-8')

    web_response = mysite.customs.models.WebResponse()

    b = mechanize.Browser()
    b.set_handle_robots(False)
    addheaders = [('User-Agent',
                   'Mozilla/4.0 (compatible; MSIE 5.0; Windows 98; (compatible;))')]
    if referrer is not None:
        b.set_handle_referer(False)
        addheaders.extend([('Referer',
                           referrer)])
    b.addheaders = addheaders

    retry = False
    reason = None

    try:
        b.open(url)
    except BadStatusLine, e:
        retry = True
        reason = 'BadStatusLine'
    except HTTPError, e:
        if (e.code == 504 or e.code == 502) and attempts_remaining > 0:
            retry = True
            reason = str(e.code)
        else:
            raise

    # Okay, so sometimes we should retry:
    if retry and attempts_remaining > 0:
        # FIXME: Test with mock object.
        message_schema = "Tried to talk to %s, got %s, retrying %d more times..."
        long_message = message_schema % (url, reason, attempts_remaining)
        logging.warn(long_message)

        if person:
            short_message = message_schema % (urlparse(url).hostname,
                                              reason, attempts_remaining)
            person.user.message_set.create(message=short_message)
        return mechanize_get(url, referrer, attempts_remaining - 1, person)

    return b


def link_works(url):
    try:
        req = mechanize_get(url)
    except urllib2.URLError, e:
        return False
    return True
