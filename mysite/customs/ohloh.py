# This file is part of OpenHatch.
# Copyright (C) 2009, 2010 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
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

# This file is just a wrapper around the Ohloh.net API that helps
# us get icons for projects.

import xml.etree.ElementTree as ET
import xml.parsers.expat
import urllib
import urllib2
import cStringIO as StringIO
from django.conf import settings
import mysite.customs.models
from django.utils import http


def uni_text(s):
    if type(s) == unicode:
        return s
    return s.decode('utf-8')

import mysite.customs.mechanize_helpers


def ohloh_url2data(url, selector, params={}, many=False, API_KEY=None):
    '''Input: A URL to get,
    a bunch of parameters to toss onto the end url-encoded,
    many (a boolean) indicating if we should return a list of just one datum,
    API_KEY suggesting a key to use with Ohloh.

    Output: A list/dictionary of Ohloh data plus a saved WebResponse instance that
    logs information about the request.'''

    if API_KEY is None:
        API_KEY = settings.OHLOH_API_KEY

    my_params = {u'api_key': unicode(API_KEY)}
    my_params.update(params)
    params = my_params
    del my_params

    # FIXME: We return more than just "ret" these days! Rename this variable.
    ret = []

    encoded = http.urlencode(params)
    url += encoded
    try:
        b = mysite.customs.mechanize_helpers.mechanize_get(url)
        web_response = mysite.customs.models.WebResponse.create_from_browser(b)
        # Always save the WebResponse, even if we don't know
        web_response.save()
        # that any other object will store a pointer here.
    except urllib2.HTTPError, e:
        # FIXME: Also return a web_response for error cases
        if str(e.code) == '404':
            if many:
                return [], None
            return {}, None
        else:
            raise

    try:
        s = web_response.text
        tree = ET.parse(StringIO.StringIO(s))
    except xml.parsers.expat.ExpatError:
        # well, I'll be. it doesn't parse.
        return None, web_response

    # Did Ohloh return an error?
    root = tree.getroot()
    if root.find('error') is not None:
        raise ValueError, "Ohloh gave us back an error. Wonder why."

    interestings = root.findall(selector)
    for interesting in interestings:
        this = {}
        for child in interesting.getchildren():
            if child.text:
                this[unicode(child.tag)] = uni_text(child.text)
        ret.append(this)

    if many:
        return ret, web_response
    if ret:
        return ret[0], web_response
    return None, web_response


def process_logo_filename(logo_filename):
    if logo_filename == 'no_logo.png':
        # The Ohloh API used to not provide any data
        # if the logo was missing. Now, it provides this flag value
        # (as perceived by others at e.g. https://github.com/eventh/syte/commit/12f02c3aff6761278d09893e5ff071af55de238f )
        # so we raise KeyError, just like in the good old days,
        # when we see this value.
        raise KeyError, ("Simulating KeyError "
                         "to convince caller the logo is not there.")
    return logo_filename


class Ohloh(object):

    def get_icon_for_project(self, project):
        try:
            return self.get_icon_for_project_by_id(project)
        except ValueError:
            return self.get_icon_for_project_by_human_name(project)

    def get_icon_for_project_by_human_name(self, project):
        """@param project: the name of a project."""
        # Do a real search to find the project
        try:
            data = self.project_name2projectdata(project)
        except urllib2.HTTPError:
            raise ValueError
        try:
            med_logo = process_logo_filename(data['medium_logo_url'])
        except TypeError:
            raise ValueError, "Ohloh gave us back nothing."
        except KeyError:
            raise ValueError, "The project exists, but Ohloh knows no icon."
        b = mysite.customs.mechanize_helpers.mechanize_get(med_logo)
        return b.response().read()

    def get_icon_for_project_by_id(self, project):
        try:
            data = self.project_id2projectdata(project_name=project)
        except urllib2.HTTPError:
            raise ValueError
        try:
            med_logo = process_logo_filename(data['medium_logo_url'])
        except KeyError:
            raise ValueError, "The project exists, but Ohloh knows no icon."
        b = mysite.customs.mechanize_helpers.mechanize_get(med_logo)
        return b.response().read()

    def project_id2projectdata(self, project_id=None, project_name=None):
        if project_name is None:
            project_query = str(int(project_id))
        else:
            project_query = str(project_name)
        url = 'http://www.ohloh.net/projects/%s.xml?' % urllib.quote(
            project_query)
        data, web_response = ohloh_url2data(url=url, selector='result/project')
        return data

    def project_name2projectdata(self, project_name_query):
        url = 'http://www.ohloh.net/projects.xml?'
        args = {u'query': unicode(project_name_query)}
        data, web_response = ohloh_url2data(url=unicode(url),
                                            selector='result/project',
                                            params=args,
                                            many=True)
        # Sometimes when we search Ohloh for e.g. "Debian GNU/Linux", the project it gives
        # us back as the top-ranking hit for full-text relevance is "Ubuntu GNU/Linux." So here
        # we see if the project dicts have an exact match by project name.

        if not data:
            # If there is no matching project possibilit at all, get out now.
            return None

        exact_match_on_project_name = [datum for datum in data
                                       if datum.get('name', None).lower() == project_name_query.lower()]
        if exact_match_on_project_name:
            # If there's an exact match on the project name, return this datum
            return exact_match_on_project_name[0]

        # Otherwise, trust Ohloh's full-text relevance ranking and return the
        # first hit
        return data[0]

_ohloh = Ohloh()


def get_ohloh():
    return _ohloh

# vim: set nu:
