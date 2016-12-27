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

import mysite.profile.view_helpers
import mysite.project.view_helpers
import staticgenerator.middleware


def get_user_ip(request):
#    return request.META['REMOTE_ADDR']
    if request.META['REMOTE_ADDR'] == '127.0.0.1':
        return "98.140.110.121"
    else:
        return request.META['REMOTE_ADDR']


class HandleWannaHelpQueue(object):

    def process_request(self, request):
        if not hasattr(request, 'user') or not hasattr(request, 'session'):
            return None

        if (hasattr(request, 'user') and
            request.user.is_authenticated() and
                'wanna_help_queue_handled' not in request.session):
            mysite.project.view_helpers.flush_session_wanna_help_queue_into_database(
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
            mysite.project.view_helpers.take_control_of_our_answers(
                request.user, request.session)
            request.session['post_login_stuff_run'] = True
        return response


class StaticGeneratorMiddlewareOnlyWhenAnonymous(object):

    '''This is a wrapper around
    staticgenerator.middleware.StaticGeneratorMiddleware that only saves to the
    cache when request.user.is_authenticated() is False.

    We never want to do static generation for when people are logged in.'''

    def process_response(self, request, response):
        # If somehow the request has no 'user' attribute, bail.
        if not hasattr(request, 'user'):
            return response
        # If the request comes from a user that is authenticated, bail.
        if request.user.is_authenticated():
            return response
        # Finally, pass the reponse to StaticGeneratorMiddleware. The middleware
        # there is responsible for checking the settings.STATIC_GENERATOR_URLS
        # to make sure the URL is permitted to be cached.
        m = staticgenerator.middleware.StaticGeneratorMiddleware()
        return m.process_response(request, response)
