# This file is part of OpenHatch.
# Copyright (C) 2010 Jack Grigg
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

from django.utils import simplejson
import urllib
import os
import os.path
import shutil
import tempfile
import datetime
import dateutil.parser
import subprocess
import json

from django.http import HttpResponse
import django.shortcuts
from django.template import RequestContext
import django.conf

def json_response(python_object):
    json = simplejson.dumps(python_object)
    return HttpResponse(json, mimetype="application/json")

class ObjectFromDict(object):
    def __init__(self, data, recursive = False):
        for key in data:
            if recursive:
                if type(data[key]) == type({}):
                    data[key] = ObjectFromDict(data[key], recursive=recursive)
                elif type(data[key]) == type([]):
                    data[key] = [ObjectFromDict(item, recursive=recursive) for item in data[key]]
            setattr(self, key, data[key])

def sanitize_wide_unicode(data):
    # Recurse on dicts and lists.
    if type(data) == type({}):
        for key in data:
            data[key] = sanitize_wide_unicode(data[key])
    elif type(data) == type([]):
        data = [sanitize_wide_unicode(item) for item in data]
    elif type(data) == type(u''):
        # Replace any wide unicode or surrogate code points with a unicode question mark.
        data = u''.join(c if not (0xD800 <= ord(c) <= 0xDFFF or ord(c) >= 0x10000) else u'\ufffd' for c in data)
    return data

def assert_or_pdb(expression):
    if expression:
        pass
    else:
        if 'LOTSA_PDB' in os.environ:
            import pdb
            pdb.set_trace()
        else:
            raise ValueError, "eek"

def string2naive_datetime(s):
    time_zoned = dateutil.parser.parse(s)
    if time_zoned.tzinfo:
        d_aware = time_zoned.astimezone(dateutil.tz.tzutc())
        d = d_aware.replace(tzinfo=None)
    else:
        d = time_zoned # best we can do
    return d

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return django.shortcuts.render_to_response(*args, **kwargs)

def clear_static_cache(path):
    '''Atomically destroy the static file cache for a certain path.'''
    # Steps:
    fully_qualified_path = os.path.join(django.conf.settings.WEB_ROOT, path)

    # 0. Create new temp dir
    try:
        new_temp_path = tempfile.mkdtemp(dir=django.conf.settings.WEB_ROOT + '/')
    except OSError, e:
        if e.errno == 28: # No space left on device
           # Aww shucks, we can't do it the smart way.
           # We just set new_temp_path to the old path, then
           # and let shutil remove it.
           shutil.rmtree(fully_qualified_path)
           return # We are done.

    # 1. Atomically move the path that we want to expire into the new directory
    try:
        os.rename(fully_qualified_path, os.path.join(new_temp_path, 'old'))
    except OSError, e:
        if e.errno == 2: # No such file or directory
            # Well, that means the cache is already clear.
            # We still have to nuke new_temp_path though!
            pass
        else:
            raise

    # 2. shutil.rmtree() the new path
    shutil.rmtree(new_temp_path)

# Implementation of something like subprocess.check_output, which didn't
# get added to the Python standard library until 2.7.
def subproc_check_output(*args, **kw):
    if 'stdout' in kw:
        raise ValueError, 'stdout must not be specified'
    kw['stdout'] = subprocess.PIPE
    subproc = subprocess.Popen(*args, **kw)
    output = subproc.stdout.read()
    if subproc.wait() != 0:
        raise RuntimeError, 'subprocess failed with return code %d' % subproc.returncode
    return output

def int_list2ranges(int_list):
    ### Based on code here: http://stackoverflow.com/questions/4628333/converting-a-list-of-integers-into-range-in-python
    q = sorted(int_list)
    if q:
        i = 0
        for j in xrange(1,len(q)):
            if q[j] > 1+q[j-1]:
                yield (q[i],q[j-1])
                i = j
        yield (q[i], q[-1])


def get_object_or_none(klass, *args, **kwargs):
    queryset = django.shortcuts_get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None
# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
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

import mysite.base.unicode_sanity
import mysite.base.disk_cache
from django.utils import simplejson
from django.core.cache import cache
from django.conf import settings
import hashlib
import re
import traceback
import logging
import mysite.base.decorators
import datetime
import base64
import os
import random

notifications_dictionary = {
        "edit_password_done":
        "Your password has been changed.",

        "oops":
        """Couldn't find that pair of username and password. """
        "<a href='/account/forgot_pass/'>"
        "Click here if you forgot your password.</a>",

        "next":
        "You've got to be logged in to do that!",
        }

def put_forwarder_in_contact_blurb_if_they_want(string, user):
    forwarder_regex= r'\$fwd\b'
    # if they want a forwarder
    if re.search(forwarder_regex, string):
        visible_forwarders_matching_user = mysite.profile.models.Forwarder.objects.filter(
                user=user, stops_being_listed_on__gt=datetime.datetime.utcnow())
        # "we can trust that" they already have a forwarder created if they
        # want one (we make it at edit-time and then at garbage collection time
        # (nightly), if necessary)
        # we'd hope that this list only contains one element, but if not oh well
        if not visible_forwarders_matching_user:
            forwarder = generate_forwarder(user).get_email_address()
        else:
            forwarder = visible_forwarders_matching_user[0].get_email_address()
        forwarder += u" " # Put a space afterwards, to ensure that it gets urlizetrunc'd properly
        string = re.sub(forwarder_regex, forwarder, string)
    return string

def generate_forwarder(user):
    Forwarder = mysite.profile.models.Forwarder
    random_str = "%s.%s" % (user.username, base64.b64encode(os.urandom(6), altchars='_.'))
    our_new_forwarder = Forwarder(address=random_str, user=user, expires_on=datetime.datetime.utcnow() + settings.FORWARDER_LIFETIME_TIMEDELTA, stops_being_listed_on=datetime.datetime.utcnow() + settings.FORWARDER_LISTINGTIME_TIMEDELTA)
    our_new_forwarder.save()
    return our_new_forwarder

def get_notification_from_request(request):
    notification_id = request.GET.get('msg', None)
    if notification_id:
        try:
            notification_text = notifications_dictionary[notification_id]
        except KeyError:
            notification_text = ("Couldn't find notification text "
                    + "for id = `%s`" % notification_id)
        return [ {
            'id': notification_id,
            'text': notification_text
            } ]
    else:
        return []

def mysql_regex_escape(s):
    ret = ''
    for letter in s:
        if letter == ']':
            ret += letter
        else:
            ret += '[' + letter + ']'
    return ret

## source: http://code.google.com/apis/kml/articles/geocodingforkml.html
import urllib

def _geocode(address=None, response_data=None):
    # This function queries the Google Maps API geocoder with an
    # address. It gets back json, which it then parses and
    # returns a string with the longitude and latitude of the address.

    logging.info('Geocoding address: %s' % address)

    mapsUrl = 'https://maps.googleapis.com/maps/api/geocode/json?'

    # This joins the parts of the URL together into one string.
    query_string = mysite.base.unicode_sanity.urlencode(
                                    {u'address': address, u'sensor': u'false'})
    # This retrieves the URL from Google, parses out the longitude and latitude,
    # and then returns them as a string.
    try:
        if response_data:
            coordinates = json.loads(response_data)
        else:
            coordinates = json.loads(urllib.urlopen(mapsUrl + query_string).read())
        status = coordinates['status']

        # For more info on status,
        # https://developers.google.com/maps/documentation/geocoding/#StatusCodes
        if status == 'OK':
            latitude = float(
                coordinates['results'][0]['geometry']['location']['lat'])
            longitude = float(
                coordinates['results'][0]['geometry']['location']['lng'])
            return {'latitude': latitude,
                    'longitude': longitude}
        return None
    except IOError:
        logging.exception("While attempting to geocode, got an error.")
        logging.warning("If you are online and still get this message, something is wrong.")
    except Exception:
        stack = traceback.extract_stack()
        logging.debug('An error occurred: %s' % stack)
        raise

def object_to_key(python_thing):
    as_string = simplejson.dumps(python_thing)
    return hashlib.sha1(as_string).hexdigest()

def address2cache_key_name(address):
    return object_to_key(['function_call', 'cached_geocoding', address])

def cached_geocoding_in_json(address):
    A_LONG_TIME_IN_SECONDS = 60 * 60 * 24 * 7
    JUST_FIVE_MINUTES_IN_SECONDS = 5 * 60
    if address == 'Inaccessible Island':
        is_inaccessible = True
    else:
        is_inaccessible = False
    key_name = address2cache_key_name(address)
    geocoded = None
    if settings.DEBUG:
        geocoded_in_json = mysite.base.disk_cache.get(key_name)
    else:
        geocoded_in_json = cache.get(key_name)

    if geocoded_in_json is None:
        geocoded = _geocode(address) or {}
        geocoded_and_inaccessible = {'is_inaccessible': is_inaccessible}
        geocoded_and_inaccessible.update(geocoded)
        geocoded_in_json = simplejson.dumps(geocoded_and_inaccessible)
        if geocoded:
            cache_duration = A_LONG_TIME_IN_SECONDS + random.randrange(0, JUST_FIVE_MINUTES_IN_SECONDS) # cache for a week, which should be plenty
        else:
            cache_duration = random.randrange(0, JUST_FIVE_MINUTES_IN_SECONDS)
        if settings.DEBUG:
            mysite.base.disk_cache.set(key_name, geocoded_in_json)
        else:
            cache.set(key_name, geocoded_in_json, cache_duration)
    return geocoded_in_json

def get_uri_metadata_for_generating_absolute_links(request):
    data = {}
    colon_and_port_number = ':' + request.META['SERVER_PORT']
    host_name = request.META['SERVER_NAME']

    uri_scheme = 'http'
    if request.is_secure():
        uri_scheme = 'https'

    uri_scheme2colon_number_to_drop = {
        'http': ':80',
        'https': ':443'}

    url_prefix = host_name
    if colon_and_port_number not in uri_scheme2colon_number_to_drop[
        uri_scheme]:
        url_prefix += colon_and_port_number

    data['url_prefix'] = url_prefix
    data['uri_scheme'] = uri_scheme
    return data

