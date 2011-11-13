# Copyright (c) 2008 Resolver Systems Ltd
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.


from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from sessionprofile.models import SessionProfile


class SessionProfileMiddleware(object):

    def process_response(self, request, response):
        try:
            # For certain cases (I think 404) the session attribute won't be set
            if hasattr(request, "session"):
                session = Session.objects.get(pk=request.session.session_key)

                sessionProfile, _ = SessionProfile.objects.get_or_create(session=session)

                userID = request.session.get("_auth_user_id")
                if userID:
                    user = User.objects.get(pk=int(userID))
                else:
                    user = None

                sessionProfile.user = user
                sessionProfile.save()

        except Session.DoesNotExist:
            # If there's no session associated with the current request,
            # there's nothing to do.
            pass

        return response