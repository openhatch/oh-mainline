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


from django.core import mail
from django.test import TestCase

from django.contrib.auth.models import User

from sessionprofile.models import SessionProfile


class TestSessionProfileMaintained(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()

        self.user = User.objects.create_user(
            "harold",
            "harold@example.com",
            "p455w0rd"
        )


    def assertLoggedIn(self):
        self.assertNotEqual(self.client.session.get("_auth_user_id"), None)

    def assertNotLoggedIn(self):
        self.assertEquals(self.client.session.get("_auth_user_id"), None)


    def testProfileCreatedAndMaintained(self):
        def GetSessionID():
            return self.client.cookies["sessionid"].value

        # Harold is not logged in.
        page = self.client.get("/admin/")
        self.assertNotLoggedIn()

        # There is no username associated with his session in the django_session table.
        sessionProfile = SessionProfile.objects.get(session__session_key=GetSessionID())
        self.assertEqual(sessionProfile.user, None)

        # He logs in.
        self.client.login(username="harold", password="p455w0rd")
        page = self.client.get("/admin/")

        # His username is now associated with his session.
        sessionProfile = SessionProfile.objects.get(session__session_key=GetSessionID())
        self.assertEqual(sessionProfile.user, self.user)

        # He logs out
        self.client.logout()
        page = self.client.get("/admin/")

        # The session is disassociated.
        sessionProfile = SessionProfile.objects.get(session__session_key=GetSessionID())
        self.assertEqual(sessionProfile.user, None)
