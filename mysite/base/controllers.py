import urllib
import simplejson
from django.core.urlresolvers import reverse
import django.contrib.auth.views
from django.core.cache import cache
from django.conf import settings
import pprint

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

def _geocode(address):
    # This function queries the Google Maps API geocoder with an
    # address. It gets back a csv file, which it then parses and
    # returns a string with the longitude and latitude of the address.

    # This isn't an actual maps key, you'll have to get one yourself.
    # Sign up for one here: http://code.google.com/apis/maps/signup.html
    mapsUrl = 'http://maps.google.com/maps/geo?q='
     
    # This joins the parts of the URL together into one string.
    query_string = urllib.urlencode({'q': address, 'output': 'csv'})
    
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
        traceback.extract_stack()
        settings.applog.debug('An error occorred: %s' % stack)

def cached_geocoding_in_json(address):
    key_name = simplejson.dumps(['function_call', 'cached_geocoding', address])
    geocoded = None
    geocoded_in_json = cache.get(key_name)
    if geocoded_in_json is None:
        geocoded = _geocode(address)
        geocoded_in_json = simplejson.dumps(geocoded)
        cache.set(key_name, geocoded_in_json, 60 * 60 * 24 * 7) # cache for a week, which should be plenty
    return geocoded_in_json
