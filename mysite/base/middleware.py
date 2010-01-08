import mysite.profile.controllers

def get_user_ip(request):
    return request.META['REMOTE_ADDR']

class LocationMiddleware(object):
    # called every time a page is queried
    # guesses a user's ip address, if if necessary, and saves it to the database
    def process_request(self, request):
        the_profile = request.user.get_profile()
        if not the_profile.location_confirmed and not the_profile.dont_guess_my_location:
            the_profile.location_display_name = mysite.profile.controllers.get_geoip_guess_for_ip(get_user_ip(request))[1]
            the_profile.save()
        return None
