# -*- coding: utf-8 -*-
from __future__ import absolute_import

# This file is part of OpenHatch.
# Copyright (C) 2010, 2011 Jack Grigg
# Copyright (C) 2010 Karen Rustad
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
# Copyright (C) 2010 Mark Freeman
# Copyright (C) 2012 Berry Phillips
# Copyright (C) 2012 John Morrissey
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


from mysite.search.models import Bug, Project
from mysite.base.models import Timestamp
from mysite.profile.models import Person, Tag, TagType, Link_Person_Tag
import mysite.profile.views
from mysite.customs import ohloh
import mysite.customs.views
import mysite.base.depends
import mysite.customs.api
import mysite.customs.core_bugimporters

from django.core.urlresolvers import reverse

import logging
import mock
import os

import django.test
import django.contrib.auth.models
import django.core.serializers
from django.conf import settings
from django.test.client import Client
from django_webtest import WebTest

from StringIO import StringIO
import datetime

import mysite.customs.feed

from django.utils.unittest import skipIf, expectedFailure

import mysite.customs.models
import mysite.customs.management.commands.customs_daily_tasks
import mysite.customs.management.commands.import_bugimporter_data
import mysite.customs.management.commands.snapshot_public_data

logger = logging.getLogger(__name__)

@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class OhlohIconTests(django.test.TestCase):
    '''Test that we can grab icons from Ohloh.'''

    @expectedFailure
    @skipIf(not mysite.base.depends.Image, (
            "Skipping photo-related tests because PIL is missing. Look in "
            "ADVANCED_INSTALLATION.mkd for information."))
    def test_ohloh_gives_us_an_icon(self):
        oh = ohloh.get_ohloh()
        icon = oh.get_icon_for_project('f-spot')
        icon_fd = StringIO(icon)
        image = mysite.base.depends.Image.open(icon_fd)
        self.assertEqual(image.size, (64, 64))

    def test_ohloh_errors_on_nonexistent_project(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'lolnomatxh')

    def test_ohloh_errors_on_project_lacking_icon(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project, 'asdf')

    def test_ohloh_errors_correctly_even_when_we_send_her_spaces(self):
        oh = ohloh.get_ohloh()
        self.assertRaises(ValueError, oh.get_icon_for_project,
                          'surely nothing is called this name')

@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class BlogCrawl(django.test.TestCase):

    def test_summary2html(self):
        yo_eacute = mysite.customs.feed.summary2html('Yo &eacute;')
        self.assertEqual(yo_eacute, u'Yo \xe9')

    @mock.patch("feedparser.parse")
    def test_blog_entries(self, mock_feedparser_parse):
        mock_feedparser_parse.return_value = {
            'entries': [
                {
                    'title': 'Yo &eacute;',
                    'summary': 'Yo &eacute;'
                }]}
        entries = mysite.customs.feed._blog_entries()
        self.assertEqual(entries[0]['title'], u'Yo \xe9')
        self.assertEqual(entries[0]['unicode_text'], u'Yo \xe9')


class BlogCache(django.test.TestCase):
    """Test caching of blog entries.

    Because the cache is reused across tests (Effectively global) we fudge a
    unique key prefix per test so that the key namespace is different for each
    test method. This is pretty lame. But that's why those exist all over in
    the tests.
    """
    def blog_fetcher_version_1(self):
        return 'this-data-is-fake'

    def blog_fetcher_version_2(self):
        return 'this-data-is-also-fake'

    def test_basics(self):
        for i in range(4):
            entries = mysite.customs.feed.cached_blog_entries(
                self.blog_fetcher_version_1, key_prefix='a')
            self.assertEqual(entries, self.blog_fetcher_version_1())

    def test_with_lock_contention(self):
        # Take the lock and then tell our code to go update the entries.
        # It'll fail.

        # Shove in data version 1
        mysite.customs.feed.cached_blog_entries(
            self.blog_fetcher_version_1, key_prefix='b')
        # Delete the freshness key so that it looks like it expired.
        mysite.customs.feed.cache.delete('bblog_entries-datafresh')

        # Take the lock so that the code under test can't get it
        blog_update_lock = mysite.customs.feed.CacheLock(
            'b' + mysite.customs.feed.LOCK_KEYNAME)
        with blog_update_lock:
            entries = mysite.customs.feed.cached_blog_entries(
                self.blog_fetcher_version_2, key_prefix='b')
        # Verify that we still got stale data in return
        self.assertEqual(entries, self.blog_fetcher_version_1())

        # With the lock released, try to update again
        entries = mysite.customs.feed.cached_blog_entries(
            self.blog_fetcher_version_2, key_prefix='b')
        # And ensure that we get data version 2 (Fake)
        self.assertEqual(entries, self.blog_fetcher_version_2())

@skipIf(mysite.base.depends.lxml.html is None, "To run these tests, you must install lxml. See ADVANCED_INSTALLATION.mkd for more.")
class DataExport(django.test.TestCase):

    def test_snapshot_user_table_without_passwords(self):
        # We'll pretend we're running the snapshot_public_data management
        # command. But to avoid JSON data being splatted all over stdout, we
        # create a fake_stdout to capture that data.
        fake_stdout = StringIO()

        # Now, set up the test:
        # Create a user object
        u = django.contrib.auth.models.User.objects.create(username='bob')
        u.set_password('something_secret')
        u.save()

        # snapshot the public version of that user's data into fake stdout
        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # Now, delete the user and see if we can reimport bob
        u.delete()
        # Delete any leftover Persons too
        mysite.profile.models.Person.objects.all().delete()

        # This code re-imports from the snapshot.
        # for more in serializers.deserialize(), read
        # http://docs.djangoproject.com/en/dev/topics/serialization
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        # Now the tests:
        # The user is back
        new_u = django.contrib.auth.models.User.objects.get(username='bob')
        # and the user's password is blank (instead of the real password)
        self.assertEquals(new_u.password, '')

    def test_snapshot_user_table_without_all_email_addresses(self):
        # We'll pretend we're running the snapshot_public_data management
        # command. But to avoid JSON data being splatted all over stdout, we
        # create a fake_stdout to capture that data.
        fake_stdout = StringIO()

        # Now, set up the test:
        # Create two Person objects, with corresponding email addresses
        u1 = django.contrib.auth.models.User.objects.create(
            username='privateguy', email='hidden@example.com')
        Person.create_dummy(user=u1)

        u2 = django.contrib.auth.models.User.objects.create(
            username='publicguy', email='public@example.com')
        Person.create_dummy(user=u2, show_email=True)

        # snapshot the public version of the data into fake stdout
        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # Now, delete the them all and see if they come back
        django.contrib.auth.models.User.objects.all().delete()
        Person.objects.all().delete()

        # This code re-imports from the snapshot.
        # for more in serializers.deserialize(), read
        # http://docs.djangoproject.com/en/dev/topics/serialization
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        # Now the tests:
        # Django user objects really should have an email address
        # so, if we hid it, we make one up based on the user ID
        new_p1 = Person.objects.get(user__username='privateguy')
        self.assertEquals(
            new_p1.user.email,
            'user_id_%d_has_hidden_email_address@example.com' % new_p1.user.id)

        new_p2 = Person.objects.get(user__username='publicguy')
        self.assertEquals(new_p2.user.email, 'public@example.com')

    def test_snapshot_bug(self):
        # data capture, woo
        fake_stdout = StringIO()
        # make fake bug
        b = Bug.create_dummy_with_project()
        b.title = 'fire-ant'
        b.save()

        # snapshot fake bug into fake stdout
        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # now, delete bug...
        b.delete()

        # let's see if we can re-import fire-ant!
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        # testing to see if there are ANY bugs
        self.assertTrue(Bug.all_bugs.all())
        # testing to see if fire-ant is there
        mysite.search.models.Bug.all_bugs.get(title='fire-ant')

    def test_snapshot_timestamp(self):
        # data capture, woo
        fake_stdout = StringIO()

        # Create local constants that refer to values we will insert and check
        TIMESTAMP_KEY_TO_USE = 'birthday of Asheesh with arbitrary time'
        TIMESTAMP_DATE_TO_USE = datetime.datetime(1985, 10, 20, 3, 21, 20)

        # make fake Timestamp
        t = Timestamp()
        t.key = TIMESTAMP_KEY_TO_USE
        t.timestamp = TIMESTAMP_DATE_TO_USE
        t.save()

        # snapshot fake timestamp into fake stdout
        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # now, delete the timestamp...
        t.delete()

        # let's see if we can re-import the timestamp
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        # testing to see if there are ANY
        self.assertTrue(Timestamp.objects.all())
        # testing to see if ours is there
        reincarnated_t = mysite.base.models.Timestamp.objects.get(
            key=TIMESTAMP_KEY_TO_USE)
        self.assertEquals(reincarnated_t.timestamp, TIMESTAMP_DATE_TO_USE)

    def test_snapshot_project(self):
        fake_stdout = StringIO()
        # make fake Project
        proj = Project.create_dummy_no_icon(
            name="karens-awesome-project", language="Python")

        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # now delete fake Project...
        proj.delete()

        # let's see if we can reincarnate it!
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        # test: are there ANY projects?
        self.assertTrue(Project.objects.all())
        # test: is our lovely fake project there?
        mysite.search.models.Project.objects.get(name="karens-awesome-project")

    def test_not_explode_when_user_has_no_person(self):
        fake_stdout = StringIO()
        # make a User
        django.contrib.auth.models.User.objects.create(username='x')
        # but slyly remove the Person objects
        Person.objects.get(user__username='x').delete()

        # do a snapshot...
        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # delete the User
        django.contrib.auth.models.User.objects.all().delete()

        # let's see if we can reincarnate it!
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        django.contrib.auth.models.User.objects.get(username='x')

    @mock.patch('mysite.customs.ohloh.Ohloh.get_icon_for_project')
    def test_snapshot_project_with_icon(self, fake_icon):
        fake_icon_data = open(
            os.path.join(settings.MEDIA_ROOT, 'no-project-icon.png')).read()
        fake_icon.return_value = fake_icon_data

        fake_stdout = StringIO()
        # make fake Project
        proj = Project.create_dummy(
            name="karens-awesome-project", language="Python")
        proj.save()

        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # now delete fake Project...
        proj.delete()

        # let's see if we can reincarnate it!
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        # test: are there ANY projects?
        self.assertTrue(Project.objects.all())
        # test: is our lovely fake project there?
        mysite.search.models.Project.objects.get(name="karens-awesome-project")
        # self.assertEquals(icon_raw_path,
        # reincarnated_proj.icon_raw.path)

    def test_snapshot_person(self):

        fake_stdout = StringIO()
        # make fake Person who doesn't care if people know where he is
        zuckerberg = Person.create_dummy(
            first_name="mark",
            location_confirmed=True,
            location_display_name='Palo Alto',
            latitude=0,
            longitude=0)
        self.assertEquals(
            zuckerberg.get_public_location_or_default(), 'Palo Alto')

        # make a fake Person who REALLY cares about location being private
        munroe = Person.create_dummy(first_name="randall",
                                     location_confirmed=False,
                                     location_display_name='Cambridge',
                                     latitude=0,
                                     longitude=0)
        self.assertEquals(munroe.get_public_location_or_default(),
                          'Inaccessible Island')

        # Creating dummy tags, tags_persons and tagtypes
        # Dummy TagTypes
        tagtype_understands = TagType(name="understands")
        tagtype_understands.save()
        tagtype_can_mentor = TagType(name="can_mentor")
        tagtype_can_mentor.save()

        # Dummy Tags
        tag_facebook_development = Tag(
            text="Facebook development", tag_type=tagtype_understands)
        tag_facebook_development.save()
        tag_something_interesting = Tag(
            text="Something interesting", tag_type=tagtype_can_mentor)
        tag_something_interesting.save()

        # Dummy Links
        link_zuckerberg = Link_Person_Tag(
            person=zuckerberg, tag=tag_facebook_development)
        link_zuckerberg.save()
        link_munroe = Link_Person_Tag(
            person=munroe, tag=tag_something_interesting)
        link_munroe.save()

        command = (
            mysite.customs.management.commands.snapshot_public_data.Command())
        command.handle(output=fake_stdout)

        # now, delete fake people
        zuckerberg.delete()
        munroe.delete()
        # ...and tags, tagtypes, and links too
        tag_facebook_development.delete()
        tag_something_interesting.delete()
        tagtype_understands.delete()
        tagtype_can_mentor.delete()
        link_zuckerberg.delete()
        link_munroe.delete()

        # and delete any User objects too
        django.contrib.auth.models.User.objects.all().delete()
        mysite.profile.models.Tag.objects.all().delete()
        mysite.profile.models.TagType.objects.all().delete()
        mysite.profile.models.Link_Person_Tag.objects.all().delete()
        # go go reincarnation gadget
        for obj in django.core.serializers.deserialize('json',
                                                       fake_stdout.getvalue()):
            obj.save()

        # did we snapshot/save ANY Persons?
        self.assertTrue(Person.objects.all())

        # did our fake Persons get saved?
        new_zuckerberg = mysite.profile.models.Person.objects.get(
            user__first_name="mark")
        new_munroe = mysite.profile.models.Person.objects.get(
            user__first_name="randall")

        # check that location_confirmed was saved accurately
        self.assertEquals(new_zuckerberg.location_confirmed, True)
        self.assertEquals(new_munroe.location_confirmed, False)

        # check that location_display_name is appropriate
        self.assertEquals(new_zuckerberg.location_display_name, 'Palo Alto')
        self.assertEquals(new_munroe.location_display_name,
                          'Inaccessible Island')

        # Check that Zuckerburg has a real lat/long
        self.assertNotEqual(mysite.profile.models.DEFAULT_LATITUDE,
                            new_zuckerberg.latitude)
        self.assertNotEqual(mysite.profile.models.DEFAULT_LONGITUDE,
                            new_zuckerberg.longitude)

        # Check that Randall has no lat/long
        self.assertEquals(mysite.profile.models.DEFAULT_LATITUDE,
                          new_munroe.latitude)
        self.assertEquals(mysite.profile.models.DEFAULT_LONGITUDE,
                          new_munroe.longitude)

        # check that we display both as appropriate
        self.assertEquals(
            new_zuckerberg.get_public_location_or_default(), 'Palo Alto')
        self.assertEquals(
            new_munroe.get_public_location_or_default(), 'Inaccessible Island')

        # get tags linked to our two dummy users...
        new_link_zuckerberg = (
            mysite.profile.models.Link_Person_Tag.objects.get(
                id=new_zuckerberg.user_id))
        new_link_munroe = (
            mysite.profile.models.Link_Person_Tag.objects.get(
                id=new_munroe.user_id))

        new_tag_facebook_development = mysite.profile.models.Tag.objects.get(
            link_person_tag__person=new_zuckerberg)
        new_tag_something_interesting = mysite.profile.models.Tag.objects.get(
            link_person_tag__person=new_munroe)

        # ...and tagtypes for the tags
        new_tagtype_understands = mysite.profile.models.TagType.objects.get(
            tag__tag_type=new_tag_facebook_development.tag_type)
        new_tagtype_can_mentor = mysite.profile.models.TagType.objects.get(
            tag__tag_type=new_tag_something_interesting.tag_type)

        # finally, check values
        self.assertEquals(new_link_zuckerberg.person, new_zuckerberg)
        self.assertEquals(new_link_munroe.person, new_munroe)

        self.assertEquals(new_tag_facebook_development.text,
                          'Facebook development')
        self.assertEquals(new_tag_something_interesting.text,
                          'Something interesting')

        self.assertEquals(new_tagtype_understands.name, 'understands')
        self.assertEquals(new_tagtype_can_mentor.name, 'can_mentor')

    def test_load_persons_and_profiles1(self):
        self.load_snapshot_file('snapshot1.json')

    def test_load_persons_and_profiles2(self):
        self.load_snapshot_file('snapshot2.json')

    def load_snapshot_file(self, snapshot_file_name):
        snapshot_file_path = os.path.join(
            settings.MEDIA_ROOT, 'sample-data', 'snapshots', snapshot_file_name
        )
        with open(snapshot_file_path) as snapshot_file:
            for obj in django.core.serializers.deserialize('json',
                                                           snapshot_file,
                                                           using='default'):
                obj.save()


@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class BugTrackerEditingViews(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(BugTrackerEditingViews, self).setUp()
        self.twisted = mysite.search.models.Project.create_dummy(
            name='Twisted System')
        self.tm = mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            base_url='http://twistedmatrix.com/trac/',
            bug_project_name_format='{tracker_name}',
            bitesized_type='keywords',
            bitesized_text='easy',
            documentation_type='keywords',
            documentation_text='documentation')
        for url in (
                ['http://twistedmatrix.com/trac/query?status=new&'
                 'status=assigned&status=reopened&format=csv&keywords=%7Eeasy'
                 '&order=priority',
                 'http://twistedmatrix.com/trac/query?status=assigned&'
                 'status=new&status=reopened&format=csv&order=priority&'
                 'keywords=~documentation']):
            mysite.customs.models.TracQueryModel.objects.create(
                url=url, tracker=self.tm)

    def login_with_client(self, username='paulproteus',
                          password="paulproteus's unbreakable password"):
        client = Client()
        success = client.login(username=username,
                               password=password)
        self.assert_(success)
        return client

    def test_slash_does_not_crash_tracker_editor(self):
        mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name="something/or other")
        client = self.login_with_client()
        url = reverse(mysite.customs.views.list_trackers)
        response = client.post(url, {'list_trackers-tracker_type': 'trac'})
        self.assertEqual(200, response.status_code)

    def test_bug_tracker_edit_form_fills_in_hidden_field(self):
        client = self.login_with_client()
        url = (reverse(
            mysite.customs.views.add_tracker,
            kwargs={'tracker_type': 'trac'})
            + '?project_id=%d' % (self.twisted.id, ))
        response = client.get(url)
        self.assertEqual(
            self.twisted,
            response.context['tracker_form'].initial['created_for_project'])

    def test_bug_tracker_edit_url_missing_url_id_302s(self):
        client = self.login_with_client()
        url = reverse(mysite.customs.views.edit_tracker_url,
                      kwargs={'tracker_id': '101',
                              'tracker_type': 'trac',
                              'tracker_name': 'whatever',
                              'url_id': '000'})

        # reverse won't work without a url_id so we need to add one
        # then remove it once the url has been generated.
        url = url.replace('000', '')

        response = client.get(url)
        # This should redirect to what amounts to a not-found page
        assert response.status_code == 302

    def test_edit_tracker_url(self):
        client = self.login_with_client()
        # get url_id
        url_id = mysite.customs.models.TracQueryModel.objects.all()[0].id
        url = reverse(mysite.customs.views.edit_tracker_url_do,
                      kwargs={'tracker_id': self.twisted.id,
                              'tracker_type': 'trac',
                              'tracker_name': 'twisted',
                              'url_id': url_id})
        r = client.get(url)
        self.assertEquals(r.status_code, 200)


@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class BugzillaTrackerEditingViews(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(BugzillaTrackerEditingViews, self).setUp()
        self.kde = mysite.search.models.Project.create_dummy(name='KDE')

    def test_form_create_bugzilla_tracker(self):
        # We start with no BugzillaTrackerModel objects in the DB
        self.assertEqual(
            0,
            mysite.customs.models.BugzillaTrackerModel.objects.all().
            select_subclasses().count())
        form = mysite.customs.forms.BugzillaTrackerForm({
            'tracker_name': 'KDE Bugzilla',
            'base_url': 'https://bugs.kde.org/',
            'created_for_project': self.kde.id,
            'query_url_type': 'xml',
            'max_connections': '8',
            'bug_project_name_format': 'format'})
        if form.errors:
            logger.debug(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(
            1,
            mysite.customs.models.BugzillaTrackerModel.objects.all().
            select_subclasses().count())

    def test_form_create_bugzilla_tracker_with_custom_parser(self):
        # We start with no BugzillaTrackerModel objects in the DB
        self.assertEqual(
            0,
            mysite.customs.models.BugzillaTrackerModel.objects.all().
            select_subclasses().count())
        form = mysite.customs.forms.BugzillaTrackerForm({
            'tracker_name': 'KDE Bugzilla',
            'base_url': 'https://bugs.kde.org/',
            'created_for_project': self.kde.id,
            'query_url_type': 'xml',
            'max_connections': '8',
            'custom_parser': 'bugzilla.KDEBugzilla',
            'bug_project_name_format': 'format'})
        if form.errors:
            logger.debug(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(
            1,
            mysite.customs.models.BugzillaTrackerModel.objects.all().
            select_subclasses().count())
        btm = (
            mysite.customs.models.BugzillaTrackerModel.objects.all().
            select_subclasses().get())
        self.assertTrue('bugzilla.KDEBugzilla', btm.custom_parser)


@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class BugzillaTrackerListing(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(BugzillaTrackerListing, self).setUp()
        self.kde = mysite.search.models.Project.create_dummy(name='KDE')

    def login_with_client(self, username='paulproteus',
                          password="paulproteus's unbreakable password"):
        client = Client()
        success = client.login(username=username,
                               password=password)
        self.assert_(success)
        return client

    def test_view_url_form(self):
        self.assertEqual(
            0,
            mysite.customs.models.BugzillaTrackerModel.objects.all().
            select_subclasses().count())

        client = self.login_with_client()

        form = mysite.customs.forms.BugzillaTrackerForm({
            'tracker_name': 'KDE',
            'base_url': 'https://bugs.kde.org/',
            'created_for_project': self.kde.id,
            'query_url_type': 'xml',
            'max_connections': '8',
            'custom_parser': 'bugzilla.KDEBugzilla',
            'bug_project_name_format': 'format'})

        if form.errors:
            logger.debug(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        btm = (
            mysite.customs.models.BugzillaTrackerModel.objects.all().
            select_subclasses().get())

        resp = client.get(
            '/customs/add/bugzilla/' + str(btm.id) + '/KDE/url/do')
        self.assertEqual(resp.status_code, 200)


@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class LaunchpadTrackerEditingViews(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(LaunchpadTrackerEditingViews, self).setUp()
        self.kde = mysite.search.models.Project.create_dummy(name='KDE')

    def test_form_create_launchpad_tracker(self):
        # We start with no LaunchpadTrackerModel objects in the DB
        self.assertEqual(
            0,
            mysite.customs.models.LaunchpadTrackerModel.objects.all().
            select_subclasses().count())
        form = mysite.customs.forms.LaunchpadTrackerForm({
            'tracker_name': 'KDE Bugzill',
            'launchpad_name': 'https://bugs.kde.org/',
            'created_for_project': self.kde.id,
            'bitsized_tag': 'easy',
            'max_connections': '8',
            'documentation_tag': 'doc',
            'bug_project_name_format': 'format'})
        if form.errors:
            logger.debug(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(
            1,
            mysite.customs.models.LaunchpadTrackerModel.objects.all().
            select_subclasses().count())
        self.assertEqual(
            1,
            mysite.customs.models.LaunchpadQueryModel.objects.all().count())


@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class GitHubTrackerEditingViews(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(GitHubTrackerEditingViews, self).setUp()
        self.kde = mysite.search.models.Project.create_dummy(name='KDE')

    def test_form_create_github_tracker(self):
        # We start with no GitHubTrackerModel objects in the DB
        self.assertEqual(
            0,
            mysite.customs.models.GitHubTrackerModel.objects.all().
            select_subclasses().count())
        form = mysite.customs.forms.GitHubTrackerForm({
            'tracker_name': 'KDE Github',
            'github_url': 'https://github.com/kde/Super-cool_project.1',
            'created_for_project': self.kde.id,
            'bitsized_tag': 'easy',
            'max_connections': '8',
            'documentation_tag': 'doc'})
        if form.errors:
            logger.debug(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(
            1,
            mysite.customs.models.GitHubTrackerModel.objects.all().
            select_subclasses().count())
        # We test for 2 GitHubQueryModel.objects since we must create
        # QueryModels (one for 'open' bugs, another for 'closed'
        # bugs), since GitHub's v2 API doesn't let us list all bugs
        # regardless of status.
        self.assertEqual(
            2,
            mysite.customs.models.GitHubQueryModel.objects.all().count())


@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class GitHubTrackerListing(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def login_with_client(self, username='paulproteus',
                          password="paulproteus's unbreakable password"):
        client = Client()
        success = client.login(username=username,
                               password=password)
        self.assert_(success)
        return client

    def test_view_github_trackers(self):
        self.assertEqual(
            0,
            mysite.customs.models.GitHubTrackerModel.objects.all().
            select_subclasses().count())
        client = self.login_with_client()
        resp = client.post('/customs/', {'list_trackers-tracker_type':
                                         'github'})
        self.assertEqual(resp.status_code, 200)

    def test_create_github_tracker(self):
        self.assertEqual(
            0,
            mysite.customs.models.GitHubTrackerModel.objects.all().
            select_subclasses().count())
        client = self.login_with_client()
        resp = client.get('/customs/add/github')
        self.assertEqual(resp.status_code, 200)


@skipIf(mysite.base.depends.lxml.html is None, (
        "To run these tests, you must install lxml. See "
        "ADVANCED_INSTALLATION.mkd for more information."))
class JiraTrackerEditingViews(WebTest):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def setUp(self):
        super(JiraTrackerEditingViews, self).setUp()
        self.kde = mysite.search.models.Project.create_dummy(name='kde')

    def test_form_create_jira_tracker(self):
        self.assertEqual(
            0,
            mysite.customs.models.JiraTrackerModel.objects.all().
            select_subclasses().count())

        form = mysite.customs.forms.JiraTrackerForm({
            'tracker_name': 'KDE Jira',
            'base_url': 'https://jira.kde.org/',
            'created_for_project': self.kde.id,
            'bitesized_tag': 'easy',
            'bitesized_type': 'label',
            'max_connections': '8',
            'bug_project_name_format': 'KDE',
            'documentation_tag': 'doc'})
        if form.errors:
            logger.debug(form.errors)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(
            1,
            mysite.customs.models.JiraTrackerModel.objects.all().
            select_subclasses().count())
        self.assertEqual(
            1,
            mysite.customs.models.JiraQueryModel.objects.all().count())

# Tests for importing bug data from YAML files, as emitted by oh-bugimporters


class ExportTrackerAsDict(django.test.TestCase):

    def setUp(self, *args, **kwargs):
        # Set up the Twisted TrackerModel that will be used here.
        self.tm = mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            base_url='http://twistedmatrix.com/trac/',
            bug_project_name_format='{tracker_name}',
            bitesized_type='keywords',
            bitesized_text='easy',
            documentation_type='keywords',
            documentation_text='documentation')
        for url in (
                ['http://twistedmatrix.com/trac/query?status=new&'
                 'status=assigned&status=reopened&format=csv&keywords=%7Eeasy'
                 '&order=priority', 'http://twistedmatrix.com/trac/query?'
                                    'status=assigned&status=new&'
                                    'status=reopened&format=csv&'
                                    'order=priority&keywords=~documentation']):
            mysite.customs.models.TracQueryModel.objects.create(
                url=url, tracker=self.tm)

    def test_export(self):
        exported = self.tm.as_dict()
        golden = {'documentation_text': 'documentation',
                  'documentation_type': 'keywords',
                  'queries': ([u'http://twistedmatrix.com/trac/query?'
                               u'status=new&status=assigned&status=reopened'
                               u'&format=csv&keywords=%7Eeasy&order=priority',
                               u'http://twistedmatrix.com/trac/query?'
                               u'status=assigned&status=new&status=reopened&'
                               u'format=csv&order=priority&'
                               u'keywords=~documentation']),
                  'base_url': 'http://twistedmatrix.com/trac/',
                  'bitesized_text': 'easy',
                  'bitesized_type': 'keywords',
                  'bug_project_name_format': '{tracker_name}',
                  'tracker_name': 'Twisted',
                  'as_appears_in_distribution': '',
                  'custom_parser': '',
                  'bugimporter': 'trac',
                  'existing_bug_urls': [],
                  'get_older_bug_data': None,
                  }
        self.assertEqual(golden, exported)

    def test_export_includes_existing_bugs(self):
        # Create the list of Bug objects we'll create
        expected_bug_urls = sorted([
            'http://twistedmatrix.com/trac/ticket/5858',
            'http://twistedmatrix.com/trac/ticket/4298',
        ])
        # Make sure there is a corresponding Twisted project
        mysite.search.models.Project.create_dummy(name='Twisted')
        for expected_bug_url in expected_bug_urls:
            b = mysite.search.models.Bug.create_dummy(
                canonical_bug_link=expected_bug_url)
            b.tracker_id = self.tm.id
            b.save()
        exported = self.tm.as_dict()
        sorted_bug_urls = sorted(exported.get('existing_bug_urls', []))
        self.assertEqual(expected_bug_urls,
                         sorted_bug_urls)


class ExportOldBugDataLinks(django.test.TestCase):

    def test_google_tracker(self):
        # Set up the Twisted TrackerModel that will be used here.
        # Note that we use Twisted here as an example, even though they're
        # not on Google Code. It just makes the test look more similar to
        # the other tests.
        tm = mysite.customs.models.GoogleTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            google_name='twisted',
        )

        # Create the list of Bug objects we'll create
        expected_bug_urls = sorted([
            'http://twistedmatrix.com/trac/ticket/5858',
            'http://twistedmatrix.com/trac/ticket/4298',
        ])
        # Make sure there is a corresponding Twisted project
        mysite.search.models.Project.create_dummy(name='Twisted')
        for expected_bug_url in expected_bug_urls:
            b = mysite.search.models.Bug.create_dummy(
                canonical_bug_link=expected_bug_url)
            b.tracker_id = tm.id
            b.last_polled = datetime.datetime(2012, 9, 15, 0, 0, 0)
            b.save()
        exported = tm.as_dict()
        url = exported['get_older_bug_data']

        expected_url = 'https://code.google.com/p/twisted/issues/csv'
        colspec = ('colspec=ID+Status+Priority+Owner+Summary+Stars+Opened+'
                   'Closed+Reporter+Cc+Difficulty+Modified+Type')

        root, querystr = url.split('?')

        # If you want to sanity-check this, just replace 'twisted' in the
        # above URL with e.g. 'sympy' or some other valid Google Code project.
        assert expected_url == root
        assert 'can=1' in querystr  # All issues
        assert 'num=1000' in querystr  # Maximum issues we can retrieve
        assert colspec in querystr

    def test_github_tracker(self):
        # Set up the Twisted TrackerModel that will be used here.
        # Note that we use Twisted here as an example, even though they're
        # not on Github. It just makes the test look more similar to
        # the other tests.
        tm = mysite.customs.models.GitHubTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            github_name='twisted',
            github_repo='mainline',
        )

        # Create the list of Bug objects we'll create
        expected_bug_urls = sorted([
            'http://twistedmatrix.com/trac/ticket/5858',
            'http://twistedmatrix.com/trac/ticket/4298',
        ])
        # Make sure there is a corresponding Twisted project
        mysite.search.models.Project.create_dummy(name='Twisted')
        for expected_bug_url in expected_bug_urls:
            b = mysite.search.models.Bug.create_dummy(
                canonical_bug_link=expected_bug_url)
            b.tracker_id = tm.id
            b.last_polled = datetime.datetime(2012, 9, 15, 0, 0, 0)
            b.save()
        exported = tm.as_dict()
        url = exported['get_older_bug_data']
        expected_url = (
            'https://api.github.com/repos/twisted/mainline/issues?'
            'since=2012-09-15T00%3A00%3A00')
        # If you want to sanity-check this, just replace 'twisted' in the
        # above URL with e.g. 'acm-uiuc' or some other valid Github user,
        # and 'mainline' with 'mango-django' or some other valid repo owned by
        # that user with issues enabled.
        self.assertEqual(expected_url, url)

    def test_jira_tracker(self):
        # Set up the Twisted TrackerModel that will be used here.
        # Note that we use Twisted here as an example, even though they're
        # not on Jira. It just makes the test look more similar to
        # the other tests.
        tm = mysite.customs.models.JiraTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            base_url='http://jira.twistedmatrix.com',
            bitesized_type='label',
            bitesized_text='bitesize',
            documentation_text='doc'
        )

        # Create the list of Bug objects we'll create
        expected_bug_urls = sorted([
            'http://twistedmatrix.com/trac/ticket/5858',
            'http://twistedmatrix.com/trac/ticket/4298',
        ])
        # Make sure there is a corresponding Twisted project
        mysite.search.models.Project.create_dummy(name='Twisted')
        for expected_bug_url in expected_bug_urls:
            b = mysite.search.models.Bug.create_dummy(
                canonical_bug_link=expected_bug_url)
            b.tracker_id = tm.id
            b.last_polled = datetime.datetime(2012, 9, 15, 0, 0, 0)
            b.save()
        exported = tm.as_dict()
        url = exported['get_older_bug_data']
        expected_url = (
            'http://jira.twistedmatrix.com/rest/api/2/search?'
            'maxResults=1000&jql=created>=2012-09-15T00:00:00')

        # If you want to sanity-check this, just replace 'twisted' in the
        # above URL with e.g. 'cyanogenmod' or some other valid Jira project.
        self.assertEqual(expected_url, url)


class DuplicateNames(django.test.TestCase):

    def test_two_trackers_of_same_name(self):
        # Set up two trackers with the same name.
        gh = mysite.customs.models.GitHubTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            github_name='twisted',
            github_repo='mainline',
        )

        trac = mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            base_url='http://twistedmatrix.com/trac/',
            bug_project_name_format='{tracker_name}',
            bitesized_type='keywords',
            bitesized_text='easy',
            documentation_type='keywords',
            documentation_text='documentation')

        # Make sure this doesn't crash
        gh.get_edit_url()
        trac.get_edit_url()


class TrackerAPI(WebTest):

    def test_trac_instance_shows_up(self):
        # Create the Twisted project object
        mysite.search.models.Project.objects.create(name='Twisted')

        # Set up the Twisted TrackerModel that will be used here.
        self.tm = mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            base_url='http://twistedmatrix.com/trac/',
            bug_project_name_format='{tracker_name}',
            bitesized_type='keywords',
            bitesized_text='easy',
            documentation_type='keywords',
            documentation_text='documentation')

        api = mysite.customs.api.TrackerModelResource()
        request = django.test.client.RequestFactory().get(
            '/+api/v1/customs/tracker_model/')
        objs = api.get_object_list(request)
        obj = objs[0]
        self.assertEqual(self.tm, obj)

    def test_get_trac_instance_by_id(self):
        # Create the Twisted project object
        mysite.search.models.Project.objects.create(name='Twisted')

        # Set up the Twisted TrackerModel that will be used here.
        self.tm = mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            base_url='http://twistedmatrix.com/trac/',
            bug_project_name_format='{tracker_name}',
            bitesized_type='keywords',
            bitesized_text='easy',
            documentation_type='keywords',
            documentation_text='documentation')

        # Query for ourselves with the tracker_id parameter that is not == us
        api = mysite.customs.api.TrackerModelResource()
        request = django.test.client.RequestFactory().get(
            '/+api/v1/customs/tracker_model/?tracker_id=%d' % (
                self.tm.pk - 1,))
        objs = api.get_object_list(request)
        self.assertFalse(objs)

        # Query for ourselves properly
        api = mysite.customs.api.TrackerModelResource()
        request = django.test.client.RequestFactory().get(
            '/+api/v1/customs/tracker_model/?tracker_id=%d' % (
                self.tm.pk,))
        objs = api.get_object_list(request)
        self.assertEqual(1, len(objs))
        obj = objs[0]
        self.assertEqual(self.tm, obj)


class ImportBugsFromFiles(django.test.TestCase):

    def setUp(self, *args, **kwargs):
        # Create the Twisted project object
        mysite.search.models.Project.objects.create(name='Twisted')

        # Set up the Twisted TrackerModel that will be used here.
        self.tm = mysite.customs.models.TracTrackerModel.all_trackers.create(
            tracker_name='Twisted',
            base_url='http://twistedmatrix.com/trac/',
            bug_project_name_format='{tracker_name}',
            bitesized_type='keywords',
            bitesized_text='easy',
            documentation_type='keywords',
            documentation_text='documentation')

    def test_import_bails_if_missing_project_name(self):
        # If the sample data contains exactly one item,
        # and that item does not contain any data, do we crash?
        sample_data = [{'canonical_bug_link': 'http://example.com/ticket1',
                        'last_polled': '2013-08-02T07:47:11.307599',
                        '_tracker_name': 'Twisted'},]
        # Make sure we start out empty
        self.assertFalse(Bug.all_bugs.all())
        # Try the import, and watch us not crash
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        # but also import no data.
        self.assertFalse(Bug.all_bugs.all())

    @mock.patch('mysite.customs.core_bugimporters.import_one_bug_item')
    def test_mgmt_command_doesnt_crash_if_import_one_crashes(self, mock_import_one):
        # This test simulates a situation where import_one_bug_item crashes.
        #
        # Given that situation, does the management command called
        # import_bugimporter_data crash with it? The idea is that it
        # shouldn't crash.
        #
        # Given _that_, the management command calls a helper
        # function, _import_one(), which calls import_one_bug_item()
        # but logs exceptions rather than crashing outright.  This
        # allows the nightly bug crawl to mostly work even in the face
        # of crashy code or crazy inputs.

        # Rig up the import_one_bug_item to crash.
        mock_import_one.side_effect = Exception("Sample error from test suite.")

        # Call the handler from the management command, and make sure
        # that it doesn't actually crash.
        #
        # (You'll see some logging.error() stuff printed out on the
        # command line when running the tests; that's not a big deal.)
        mysite.customs.management.commands.import_bugimporter_data._import_one(
            {}  # dummy input
        )

    def test_import_bails_if_missing_last_polled(self):
        # If the sample data contains exactly one item,
        # and that item does not say when it was downloaded, we
        # should refuse to import the bug.
        sample_data = [{'canonical_bug_link': 'http://example.com/ticket1',
                        'last_polled': '2013-08-02T07:47:11.307599',
                        'date_reported': '2013-08-02T07:47:11.307599',
                        'last_touched': '2013-08-02T07:47:11.307599',
                        'status': 'new',
                        '_project_name': 'Twisted',
                        '_tracker_name': 'Twisted'}]
        # Make sure we start out empty
        self.assertFalse(Bug.all_bugs.all())
        # Try the import, and watch us succeed.
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertTrue(Bug.all_bugs.all())

        # Now, delete all bugs, and re-do the import without
        # last_polled. This time, we reject the datum.
        Bug.all_bugs.all().delete()
        self.assertFalse(Bug.all_bugs.all())
        sample_datum = sample_data[0]
        del sample_datum['last_polled']
        mysite.customs.core_bugimporters.import_one_bug_item(sample_datum)
        self.assertFalse(Bug.all_bugs.all())

    def test_import_from_data_dict(self):
        sample_data = [
            {'status': 'new', 'as_appears_in_distribution': '',
             'description': (
                 "This test method sets the mode of sub1 such that it cannot "
                 "be deleted in the usual way:\r\r    [Error 5] Access is "
                 "denied: '_trial_temp\\\\twisted.test.test_paths\\\\"
                 "FilePathTestCase\\\\test_getPermissions_Windows\\\\"
                 "bvk9lu\\\\temp\\\\sub1'\r\rThe test should ensure that "
                 "regardless of the test outcome, this file ends up "
                 "deletable, or it should delete it itself.\r"),
             'importance': 'high',
             'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/5228',
             'date_reported': datetime.datetime(2011, 8, 9, 16, 22, 34),
             '_tracker_name': 'Twisted',
             'submitter_realname': '',
             'last_touched': datetime.datetime(2012, 4, 12, 17, 44, 14),
             'people_involved': 3,
             'title': ('twisted.test.test_paths.FilePathTestCase.'
                       'test_getPermissions_Windows creates undeleteable '
                       'file'),
             '_project_name': 'Twisted',
             'submitter_username': 'exarkun',
             'last_polled': datetime.datetime(2012, 9, 2, 22, 18, 56, 240068),
             'looks_closed': False,
             'good_for_newcomers': True,
             'concerns_just_documentation': False}]
        self.assertFalse(Bug.all_bugs.all())
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertTrue(Bug.all_bugs.all())

    def test_bug_can_delete_itself(self):
        # The purpose of this test is to make sure that if the ParsedBug
        # has ._deleted set to True, then we delete the corresponding bug
        # from the database.
        #
        # So, we need a bug like that in the DB first. To get that, we first do
        # an import

        # Show that, before that, we have an empty database of bugs
        self.assertFalse(Bug.all_bugs.all())

        # Import one...
        sample_data = [
            {'status': 'new', 'as_appears_in_distribution': '',
             'description': (
                 "This test method sets the mode of sub1 such that it cannot "
                 "be deleted in the usual way:\r\r    [Error 5] Access is "
                 "denied: '_trial_temp\\\\twisted.test.test_paths\\\\"
                 "FilePathTestCase\\\\test_getPermissions_Windows\\\\"
                 "bvk9lu\\\\temp\\\\sub1'\r\rThe test should ensure that "
                 "regardless of the test outcome, this file ends up "
                 "deletable, or it should delete it itself.\r"),
             'importance': 'high',
             'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/5228',
             'date_reported': datetime.datetime(2011, 8, 9, 16, 22, 34),
             '_tracker_name': 'Twisted',
             'submitter_realname': '',
             'last_touched': datetime.datetime(2012, 4, 12, 17, 44, 14),
             'people_involved': 3,
             'title': (
                 'twisted.test.test_paths.FilePathTestCase.'
                 'test_getPermissions_Windows creates undeletable file'),
             '_project_name': 'Twisted',
             'submitter_username': 'exarkun',
             'last_polled': datetime.datetime(2012, 9, 2, 22, 18, 56, 240068),
             'looks_closed': False,
             'good_for_newcomers': True,
             'concerns_just_documentation': False,
             }]
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertTrue(Bug.all_bugs.all())

        # Now that we have one, modify the input data to have _deleted to be
        # True
        sample_data[0]['_deleted'] = True
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertFalse(Bug.all_bugs.all())

        # Import the same thing, with _deleted=True, and make sure we don't
        # accidentally create it somehow, nor crash.
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertFalse(Bug.all_bugs.all())

    def test_import_from_data_dict_with_isoformat_date(self):
        sample_data = [
            {'status': 'new', 'as_appears_in_distribution': '',
             'description': (
                 "This test method sets the mode of sub1 such that it cannot "
                 "be deleted in the usual way:\r\r    [Error 5] Access is "
                 "denied: '_trial_temp\\\\twisted.test.test_paths\\\\"
                 "FilePathTestCase\\\\test_getPermissions_Windows\\\\"
                 "bvk9lu\\\\temp\\\\sub1'\r\rThe test should ensure that "
                 "regardless of the test outcome, this file ends up "
                 "deletable, or it should delete it itself.\r"),
             'importance': 'high',
             'canonical_bug_link': 'http://twistedmatrix.com/trac/ticket/5228',
             'date_reported': (
                 datetime.datetime(2011, 8, 9, 16, 22, 34).isoformat()),
             '_tracker_name': 'Twisted',
             'submitter_realname': '',
             'last_touched': (
                 datetime.datetime(2012, 4, 12, 17, 44, 14).isoformat()),
             'people_involved': 3,
             'title': (
                 'twisted.test.test_paths.FilePathTestCase.'
                 'test_getPermissions_Windows creates undeleteable file'),
             '_project_name': 'Twisted',
             'submitter_username': 'exarkun',
             'last_polled': (
                 datetime.datetime(2012, 9, 2, 22, 18, 56, 240068).isoformat()
             ),
             'looks_closed': False,
             'good_for_newcomers': True,
             'concerns_just_documentation': False}]
        self.assertFalse(Bug.all_bugs.all())
        mysite.customs.core_bugimporters.import_one_bug_item(sample_data[0])
        self.assertTrue(Bug.all_bugs.all())


class GoogleQueryUrlTestCase(django.test.TestCase):

    def test_google_query_url(self):
        url = mysite.customs.models.google_query_url('myproj')
        root, querystr = url.split('?')

        # Expected colspec
        colspec = ('colspec=ID+Status+Priority+Owner+Summary+Stars+Opened+'
                   'Closed+Reporter+Cc+Difficulty+Modified+Type')

        assert root == 'https://code.google.com/p/myproj/issues/csv'
        assert 'num=1000' in querystr
        assert 'can=2' in querystr
        assert colspec in querystr

    def test_google_query_url_accepts_overrides(self):
        url = mysite.customs.models.google_query_url('myproj', can='foo')
        _, querystr = url.split('?')

        assert 'can=foo' in querystr
