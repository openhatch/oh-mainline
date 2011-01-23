# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 OpenHatch, Inc.
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

import mysite.profile.controllers
import mysite.project.controllers

def get_user_ip(request):
#    return request.META['REMOTE_ADDR']
    if request.META['REMOTE_ADDR'] == '127.0.0.1':
        return "98.140.110.121"
    else:
        return request.META['REMOTE_ADDR'] 

class LocationMiddleware(object):
    # called every time a page is queried
    # guesses a user's ip address, if if necessary, and saves it to the database
    def process_request(self, request):
        if request.user.is_authenticated():
            the_profile = request.user.get_profile()
            if not the_profile.location_display_name and not the_profile.location_confirmed and not the_profile.dont_guess_my_location:
                the_profile.location_display_name = mysite.profile.controllers.get_geoip_guess_for_ip(get_user_ip(request))[1]
                the_profile.save()
        return None

class HandleWannaHelpQueue(object):
    def process_request(self, request):
        if not hasattr(request, 'user') or not hasattr(request, 'session'):
            return None

        if request.user.is_authenticated() and 'wanna_help_queue_handled' not in request.session:
            mysite.project.controllers.flush_session_wanna_help_queue_into_database(
                request.user, request.session)
            request.session['wanna_help_queue_handled'] = True
        return None
        

class DetectLogin(object):
    # called every time a page is gotten
    # Checks for work that should be done at login time
    def process_response(self, request, response):
        if not hasattr(request, 'user') or not hasattr(request, 'session'):
            return response

        if request.user.is_authenticated() and 'post_login_stuff_run' not in request.session:
            mysite.project.controllers.take_control_of_our_answers(request.user, request.session)
            request.session['post_login_stuff_run'] = True
        return response
