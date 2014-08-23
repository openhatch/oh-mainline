# -*- coding: utf-8 -*-
from __future__ import absolute_import
# vim: set ai et ts=4 sw=4:

# This file is part of OpenHatch.
# Copyright (C) 2014 Elana Hashman
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


# Imports {{{
import mysite.bugsets.views
import mysite.bugsets.models

from mysite.base.tests import TwillTests

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlencode
# }}}


class BasicBugsetMainViewTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_bugset_names_load(self):
        mysite.bugsets.models.BugSet.objects.create(name="best event")
        mysite.bugsets.models.BugSet.objects.create(name="bestest event")
        url = reverse(mysite.bugsets.views.main_index)
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "best event")
        self.assertContains(response, "bestest event")

    def test_bugset_view_link(self):
        s = mysite.bugsets.models.BugSet.objects.create(name="best event")
        url = reverse(mysite.bugsets.views.main_index)
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, s.get_absolute_url())

    def test_user_not_logged_in(self):
        s = mysite.bugsets.models.BugSet.objects.create(name="best event")
        url = reverse(mysite.bugsets.views.main_index)
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, s.get_edit_url())
        self.assertContains(response,
                            'if you want to create or edit a bug set.')

    def test_user_logged_in(self):
        client = self.login_with_client()

        s = mysite.bugsets.models.BugSet.objects.create(name="best event")
        url = reverse(mysite.bugsets.views.main_index)
        response = client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, s.get_edit_url())
        self.assertNotContains(response,
                               'if you want to create or edit a bug set.')


class BasicBugsetListViewTests(TwillTests):
    def test_bugset_listview_load(self):
        s = mysite.bugsets.models.BugSet.objects.create(name="test event")
        b = mysite.bugsets.models.AnnotatedBug.objects.create(
            url="http://openhatch.org/bugs/issue995",
        )
        s.bugs.add(b)
        url = reverse(mysite.bugsets.views.list_index, kwargs={
            'pk': s.pk,
            'slug': '',
        })
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "test event")
        self.assertContains(response, "http://openhatch.org/bugs/issue995")

    def test_bugset_listview_load_with_custom_name(self):
        s = mysite.bugsets.models.BugSet.objects.create(name="test event")
        b = mysite.bugsets.models.AnnotatedBug.objects.create(
            url="http://openhatch.org/bugs/issue995",
        )
        s.bugs.add(b)
        url = reverse(mysite.bugsets.views.list_index, kwargs={
            'pk': s.pk,
            'slug': 'best-event',  # this can be anything!
        })
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "test event")
        self.assertContains(response, "http://openhatch.org/bugs/issue995")

    def test_bugset_listview_load_empty(self):
        # Create set with no bugs
        mysite.bugsets.models.BugSet.objects.create(name="test event")
        url = reverse(mysite.bugsets.views.list_index, kwargs={
            'pk': 1,
            'slug': '',
        })
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "test event")
        self.assertContains(response, "No bugs!")

    def test_bugset_listview_load_no_project(self):
        # Create set with no bugs
        s = mysite.bugsets.models.BugSet.objects.create(name="test event")
        b = mysite.bugsets.models.AnnotatedBug.objects.create(
            url="http://openhatch.org/bugs/issue995",
        )
        s.bugs.add(b)

        url = reverse(mysite.bugsets.views.list_index, kwargs={
            'pk': 1,
            'slug': '',
        })
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "test event")
        self.assertContains(response, "http://openhatch.org/bugs/issue995")
        self.assertContains(response, "�")  # the no project character

    def test_bugset_listview_load_with_annotated_bug(self):
        # Create set and a bug for it
        s = mysite.bugsets.models.BugSet.objects.create(name="test event")
        b = mysite.bugsets.models.AnnotatedBug.objects.create(
            url="http://openhatch.org/bugs/issue995",
        )

        # Annotate the bug
        b.title = "Add bug set view screen"
        b.description = ("Use your Django and HTML/CSS skills to make a nice "
                         "UI for the bug sets")
        b.assigned_to = "Jesse"
        b.mentor = "Elana"
        b.time_estimate = "2 hours"
        b.status = "c"
        b.skill_list = "python, html"

        # Make a project
        p = mysite.search.models.Project.objects.create(
            name='openhatch',
            display_name='OpenHatch DisplayName',
            homepage='http://openhatch.org',
            language='Python',
        )
        p.save()
        b.project = p

        # Save and associate with bugset
        b.save()
        s.bugs.add(b)

        url = reverse(mysite.bugsets.views.list_index, kwargs={
            'pk': 1,
            'slug': '',
        })
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "test event")
        self.assertContains(response, "http://openhatch.org/bugs/issue995")
        self.assertContains(response, "OpenHatch DisplayName")
        self.assertContains(response, "Add bug set view screen")
        self.assertContains(response, ("Use your Django and HTML/CSS skills "
                                       "to make a nice UI for the bug sets"))
        self.assertContains(response, "Jesse")
        self.assertContains(response, "Elana")
        self.assertContains(response, "2 hours")
        self.assertContains(response, "claimed")
        self.assertContains(response, "python, html")


class SecurityBugsetListViewTests(TwillTests):
    def test_will_inplaceedit_allow_us_to_pwn_ourselves(self):
        # Asheesh: "total cost of pwnership: 1 test"
        # note: user paulproteus has poor password hygiene
        u = User.objects.create(username='paulproteus', password='password')
        u.save()

        self.client.post(
            '/inplaceeditform/save/',
            {
                "app_label": "auth",       # the django app
                "module_name": "user",     # the django table
                "field_name": "username",  # the field name
                "obj_id": u.pk,            # the pk
                "value": '"LOLPWNED"'      # new value
            })

        self.assertEqual(User.objects.get(pk=u.pk).username, u'paulproteus')

    def test_modify_annotatedbug_object(self):
        b = mysite.bugsets.models.AnnotatedBug.objects.create(
            url="http://openhatch.org/bugs/issue995",
            mentor="Elana",
        )
        b.save()

        self.client.post(
            '/inplaceeditform/save/',
            {
                "app_label": "bugsets",
                "module_name": "annotatedbug",
                "field_name": "mentor",
                "obj_id": b.pk,
                "value": '"Asheesh"'
            })

        self.assertEqual(mysite.bugsets.models.AnnotatedBug.objects.get(
            pk=b.pk).mentor, 'Asheesh')


# Constants for the Create and Edit view tests

EVENT_NAME = "Party at Asheesh's Place"
BUGSET = """
    http://openhatch.org/bugs/issue978
    http://openhatch.org/bugs/issue994
    http://openhatch.org/bugs/issue995
    http://openhatch.org/bugs/issue1003
"""
BUGSET_REDUCED = """
    http://openhatch.org/bugs/issue978
    http://openhatch.org/bugs/issue994
    http://openhatch.org/bugs/issue995
"""
REMOVED_BUG = "http://openhatch.org/bugs/issue1003"
BUGSET_EXPANDED = """
    http://openhatch.org/bugs/issue978
    http://openhatch.org/bugs/issue994
    http://openhatch.org/bugs/issue995
    http://openhatch.org/bugs/issue1003
    http://openhatch.org/bugs/issue1020
"""
ADDED_BUG = "http://openhatch.org/bugs/issue1020"
BUGSET_CHANGED = """
    http://openhatch.org/bugs/issue978
    http://openhatch.org/bugs/issue994
    http://openhatch.org/bugs/issue995
    http://openhatch.org/bugs/issue1020
"""


class BasicBugsetCreateViewTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_create_view_load(self):
        url = reverse(mysite.bugsets.views.create_index)
        response = self.login_with_client().get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Create a Bug Set")

    def test_create_view_redirect(self):
        client = self.login_with_client()
        url = reverse(mysite.bugsets.views.create_index)
        response = client.post(
            url,
            {
                'event_name': EVENT_NAME,
                'buglist': BUGSET,
            })

        self.assertEqual(302, response.status_code)

        s = mysite.bugsets.models.BugSet.objects.get()
        self.assertEqual(
            'http://testserver' + s.get_edit_url(),
            response['location'])

        response = client.get(response['location'])

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Party at Asheesh&#39;s Place')
        self.assertContains(response, 'http://openhatch.org/bugs/issue978')

    def test_evil_urls(self):
        evil_urls = [
            # 'ftp://pr1v8.warex0z.s3rv3r.net/',  Django 1.7+ only
            'wiefjoiefoaehroaherhaevo',
            'javascript:alert("hi")',
        ]

        for url in evil_urls:
            self.assertFalse(
                mysite.bugsets.forms.BugsForm({
                    'event_name': EVENT_NAME,
                    'buglist': url,
                }).is_valid())

    def test_create_form(self):
        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': BUGSET,
        })

        self.assertTrue(f.is_valid())
        f.save()

        s = mysite.bugsets.models.BugSet.objects.get(name=EVENT_NAME)
        l = mysite.bugsets.models.AnnotatedBug.objects.filter(
            url__in=[url.strip() for url in BUGSET.split("\n")]
        )

        # Use set equality test rather than test framework's equality test
        self.assertTrue(set(s.bugs.all()) == set(l))

    def test_create_form_with_empty_name(self):
        url = reverse(mysite.bugsets.views.create_index)
        response = self.login_with_client().post(
            url,
            {
                'event_name': '',
                'buglist': BUGSET,
            })

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'This field is required.')

    def test_create_view_add_existing_bug(self):
        b = mysite.bugsets.models.AnnotatedBug.objects.create(url=ADDED_BUG)

        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': ADDED_BUG,
        })

        self.assertTrue(f.is_valid())
        f.save()

        self.assertTrue(f.object.bugs.get(pk=b.pk))

    def test_edit_view_add_existing_bug(self):
        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': REMOVED_BUG,
        })

        self.assertTrue(f.is_valid())
        f.save()

        b = mysite.bugsets.models.AnnotatedBug.objects.create(url=ADDED_BUG,
            title='title')
        g = mysite.bugsets.forms.BugsForm(data={
                'event_name': EVENT_NAME,
                'buglist': REMOVED_BUG + "\n" + ADDED_BUG,
            },
            pk=f.object.pk)

        self.assertTrue(g.is_valid())
        g.update()

        self.assertEqual(g.object.bugs.get(pk=b.pk).title, 'title')

class BasicBugsetCreateFormTests(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_edit_view_modify_name(self):
        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': BUGSET,
        })

        self.assertTrue(f.is_valid())
        f.save()

        client = self.login_with_client()
        response = client.post(
            f.object.get_edit_url(),
            {
                'event_name': 'New event name',
                'buglist': BUGSET,
            })

        self.assertEqual(302, response.status_code)
        response = client.get(response['location'])

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'New event name')

    def test_edit_view_remove_bugs(self):
        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': BUGSET,
        })

        self.assertTrue(f.is_valid())
        f.save()

        s = mysite.bugsets.models.BugSet.objects.get(pk=f.object.pk)
        self.assertTrue(s.bugs.get(url=REMOVED_BUG))

        client = self.login_with_client()
        response = client.post(
            f.object.get_edit_url(),
            {
                'event_name': EVENT_NAME,
                'buglist': BUGSET_REDUCED,
            })

        self.assertEqual(302, response.status_code)
        response = client.get(response['location'])

        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, REMOVED_BUG)

    def test_edit_view_add_bugs(self):
        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': BUGSET,
        })

        self.assertTrue(f.is_valid())
        f.save()

        s = mysite.bugsets.models.BugSet.objects.get(pk=f.object.pk)
        self.assertRaises(ObjectDoesNotExist, s.bugs.get, url=ADDED_BUG)

        client = self.login_with_client()
        response = client.post(
            f.object.get_edit_url(),
            {
                'event_name': EVENT_NAME,
                'buglist': BUGSET_EXPANDED,
            })

        self.assertEqual(302, response.status_code)
        response = client.get(response['location'])

        self.assertEqual(200, response.status_code)
        self.assertContains(response, ADDED_BUG)

    def test_edit_view_change_bugs(self):
        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': BUGSET,
        })

        self.assertTrue(f.is_valid())
        f.save()

        s = mysite.bugsets.models.BugSet.objects.get(pk=f.object.pk)
        self.assertTrue(s.bugs.get(url=REMOVED_BUG))
        self.assertRaises(ObjectDoesNotExist, s.bugs.get, url=ADDED_BUG)

        client = self.login_with_client()
        response = client.post(
            f.object.get_edit_url(),
            {
                'event_name': EVENT_NAME,
                'buglist': BUGSET_CHANGED,
            })

        self.assertEqual(302, response.status_code)
        response = client.get(response['location'])

        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, REMOVED_BUG)
        self.assertContains(response, ADDED_BUG)

    def test_create_with_smart_completion(self):
        # Make a project
        p = mysite.search.models.Project.objects.create(
            name='openhatch',
            display_name='OpenHatch DisplayName',
            homepage='http://openhatch.org',
            language='Python',
        )
        p.save()

        # Make a traditional Bug
        o = mysite.search.models.Bug.create_dummy(
            canonical_bug_link=ADDED_BUG,
            title=('django-inplaceedit probably introduces some security '
                   'holes'),
            description='''
Asheesh and I are concerned about the POST handler django-inplaceedit provides.
It is possible that it provides arbitrary edit access to the database given the
software's authentication mechanism. See this request sequence:

[19/Jul/2014 16:45:22] "GET
/inplaceeditform/get_field/?field_name=status&module_name=annotatedbug&app_label=bugsets&can_auto_save=1&obj_id=4&font_size=12.95px&__widget_height=16px&__widget_width=71px
HTTP/1.1" 200 1072
[19/Jul/2014 16:45:26] "POST /inplaceeditform/save/ HTTP/1.1" 200 37

We should make sure that this new egg doesn't allow an attacker to, for
instance, change everyone's username to 'octamarine12345...'
''',
        )

        f = mysite.bugsets.forms.BugsForm({
            'event_name': EVENT_NAME,
            'buglist': ADDED_BUG,
        })

        self.assertTrue(f.is_valid())
        f.save()

        s = mysite.bugsets.models.BugSet.objects.get(pk=f.object.pk)
        b = s.bugs.all()[0]  # the only bug in the set

        self.assertEqual(b.title, o.title)
        self.assertEqual(b.description, o.description)
        self.assertEqual(b.project, o.project)
        self.assertEqual(b.skill_list, o.project.language)


class BasicAPIViewTests(TwillTests):
    def test_return_value_in_db(self):
        b = mysite.bugsets.models.AnnotatedBug.objects.create(
            url='http://openhatch.org/bugs/issue1021',
            title='Concurrent users UX',
        )

        url = reverse(mysite.bugsets.views.api_index) + '?' + urlencode({
            'obj_id': b.pk,
            'field_name': 'title',
        })
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Concurrent users UX')

    def test_handle_value_not_in_db(self):
        url = reverse(mysite.bugsets.views.api_index) + '?' + urlencode({
            'obj_id': '42',
            'field_name': 'title',
        })
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Object does not exist!')

    def test_handle_bad_api_call(self):
        url = reverse(mysite.bugsets.views.api_index)
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Unknown error')
