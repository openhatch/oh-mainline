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


from django.db import models

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


class SessionProfile(models.Model):
    """
    We need to be able to get the username of the current logged-in
    user from PHP.  Our starting point is the sessionid, which
    is send in every request as a cookie.  We cannot go from this to
    the username in PHP, because the session data (for example,
    _auth_user_id) is stored in a pickled dictionary, and I don't
    even want to think about unpickling Python dictionaries from PHP.
    So, we use our own authentication middleware to store a separate
    model object which has the same kind of association with the
    session as the UserProfile does with the user.  Doing this means
    that we're maintaining a DB table from which PHP can read the
    user ID, by going via the Users table.
    """

    session = models.ForeignKey(Session, unique=True)

    user = models.ForeignKey(User, null=True)