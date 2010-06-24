import mysite.base.unicode_sanity
import simplejson
from django.core.urlresolvers import reverse
import django.contrib.auth.views
from django.core.cache import cache
from django.conf import settings
import pprint
import sha
import re
import traceback
import logging
import mysite.base.decorators
import datetime
import base64
import os
import string
import random

class HaystackIsDown(Exception):
    pass

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

@mysite.base.decorators.unicodify_strings_when_inputted
def _geocode(address):
    # This function queries the Google Maps API geocoder with an
    # address. It gets back a csv file, which it then parses and
    # returns a string with the longitude and latitude of the address.

    logging.info('Geocoding address: %s' % address)

    # This isn't an actual maps key, you'll have to get one yourself.
    # Sign up for one here: http://code.google.com/apis/maps/signup.html
    mapsUrl = 'http://maps.google.com/maps/geo?q='
     
    # This joins the parts of the URL together into one string.
    query_string = mysite.base.unicode_sanity.urlencode({u'q': address, u'output': u'csv'})
    
    # This retrieves the URL from Google, parses out the longitude and latitude,
    # and then returns them as a string.
    try:
        coordinates = urllib.urlopen(mapsUrl + query_string).read().split(',')
        status, accuracy, latitude, longitude = map(float, coordinates)
        # For more info on status,
        # http://code.google.com/apis/maps/documentation/geocoding/#GeocodingAccuracy
        if status == 200:
            return {'suggested_zoom_level': max(6, int(accuracy)),
                    'latitude': latitude,
                    'longitude': longitude}
        return None
    except Exception, e:
        stack = traceback.extract_stack()
        logging.debug('An error occurred: %s' % stack)
        raise

def object_to_key(python_thing):
    as_string = simplejson.dumps(python_thing)
    return sha.sha(as_string).hexdigest()

def address2cache_key_name(address):
    return object_to_key(['function_call', 'cached_geocoding', address])

@mysite.base.decorators.unicodify_strings_when_inputted
def cached_geocoding_in_json(address):
    A_LONG_TIME_IN_SECONDS = 60 * 60 * 24 * 7
    JUST_FIVE_MINUTES_IN_SECONDS = 5 * 60
    if address == 'Inaccessible Island':
        is_inaccessible = True
    else:
        is_inaccessible = False
    key_name = address2cache_key_name(address)
    geocoded = None
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

def haystack_results2db_objects(things):
    try:
        things.load_all()
        return [x.object for x in things if x.object is not None]
    except AttributeError:
        raise HaystackIsDown()
