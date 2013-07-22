# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010 OpenHatch, Inc.
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

from mysite.base.tests import TwillTests
import mysite.project.view_helpers
import mysite.account.tests

from mysite.search.models import Project
from mysite.profile.models import Person, PortfolioEntry
import mysite.project.views

import mysite.profile.views
import mysite.profile.models
import mysite.profile.view_helpers

from mysite.base.tests import better_make_twill_url

import mock
import urlparse
import datetime

from django.core.urlresolvers import reverse

from twill import commands as tc

class ProjectNameSearch(TwillTests):
    def test_search_for_similar_project_names_backend(self):
        # Create one relevant, one irrelevant project
        mysite.search.models.Project.create_dummy(name='Twisted System')
        mysite.search.models.Project.create_dummy(name='Irrelevant')

        # Call out function, hoping to find Twisted System
        starts_with_twisted = mysite.project.view_helpers.similar_project_names(
            'Twisted')
        self.assertEqual(['Twisted System'], [p.name for p in starts_with_twisted])

        # Same with lowercase name
        starts_with_twisted = mysite.project.view_helpers.similar_project_names(
            'twistEd')
        self.assertEqual(['Twisted System'], [p.name for p in starts_with_twisted])

    def test_search_for_one_matching_project_name(self):
        # If there's an exactly-matching project name, we redirect to that project's page
        # (instead of showing search results).
        mysite.search.models.Project.create_dummy(name='Twisted System')
        response = self.client.get('/projects/',
                                   {'q': 'twiSted SysTem'},
                                   follow=True)
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/projects/Twisted%20System', 302)])

    def test_form_sends_data_to_get(self):
        # This test will fail if a query that selects one project but doesn't
        # equal the project's name causes a redirect.

        # First, create the project that we will refer to below.
        mysite.search.models.Project.create_dummy(name='Twisted System')

        tc.go(better_make_twill_url('http://openhatch.org/projects'))
        query = 'Twisted'
        tc.fv(1, 'search_q', query)
        tc.submit()
        tc.url('\?q=Twisted') # Assert that URL contains this substring.
        tc.find(query)

    def test_template_get_matching_projects(self):
        mysite.search.models.Project.create_dummy(name='Twisted System')
        mysite.search.models.Project.create_dummy(name='Twisted Orange Drinks')
        response = self.client.get('/projects/',
                                   {'q': 'Twisted'},
                                   follow=True)
        matching_projects = response.context[0]['matching_projects']
        self.assertEqual(
            sorted([p.name for p in matching_projects]),
            sorted(['Twisted Orange Drinks', 'Twisted System']))

class ProjectList(TwillTests):
    def test_it_generally_works(self):
        self.client.get('/projects/')

    def test_plus_projects_redirects_to_projects(self):
        response = self.client.get("/+projects/")
        self.assertEqual(response.status_code, 301)
        parsed = urlparse.urlparse(response['location'])
        self.assertEqual('/projects/', parsed.path)

    def test_plus_projects_for_specific_project(self):
        mysite.search.models.Project.create_dummy(name='sample')
        response = self.client.get("/+projects/sample")
        self.assertEqual(response.status_code, 301)
        parsed = urlparse.urlparse(response['location'])
        self.assertEqual('/projects/sample', parsed.path)

    def test_space_projects_redirects_to_projects(self):
        response = self.client.get("/ projects/")
        self.assertEqual(response.status_code, 301)

    def test_projects_returns_projects(self):
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)


class ProjectPageCreation(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch('mysite.search.models.Project.populate_icon_from_ohloh')
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def test_post_handler(self, mock_populate_icon, mock_populate_language):
        # Show that it works
        project_name = 'Something novel'
        self.assertFalse(mysite.search.models.Project.objects.filter(name=project_name))

        client = self.login_with_client()
        response = client.post(reverse(mysite.project.views.create_project_page_do),
                                    {'project_name': project_name}, follow=True)

        # We successfully made the project...
        self.assert_(mysite.search.models.Project.objects.filter(name=project_name))

        #  and redirected to the editor.
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/+projedit/Something%20novel', 302)])

        # FIXME: Enqueue a job into the session to have this user take ownership
        # of this Project.
        # This could easily be a log for edits.

    @mock.patch('mysite.search.models.Project.populate_icon_from_ohloh')
    @mock.patch('mysite.search.tasks.PopulateProjectLanguageFromOhloh')
    def test_project_creator_simply_redirects_to_project_if_it_exists(
        self, mock_populate_icon, mock_populate_language):
        # Show that it works
        project_name = 'Something novel'
        Project.create_dummy(name=project_name.lower())

        # See? We have our project in the database (with slightly different case, but still)
        self.assertEqual(1, len(mysite.search.models.Project.objects.all()))

        response = self.client.post(reverse(mysite.project.views.create_project_page_do),
                                    {'project_name': project_name}, follow=True)

        # And we still have exactly that one project in the database.
        self.assertEqual(1, len(mysite.search.models.Project.objects.all()))

        #  and redirected.
        self.assertEqual(response.redirect_chain,
                         [('http://testserver/projects/something%20novel', 302)])

    def test_form_on_project_search_page_submits_to_project_creation_post_handler(self):
        project_search_page_url = better_make_twill_url(
                "http://openhatch.org%s?q=newproject" % reverse(mysite.project.views.projects))
        tc.go(project_search_page_url)
        # Fill form out with slightly different project name, which we
        # anticipate happening sometimes
        tc.fv('create_project', 'project_name', 'NewProject')
        tc.submit()
        post_handler_url = reverse(mysite.project.views.create_project_page_do)
        import re
        tc.url(re.escape(post_handler_url))

class ButtonClickMarksSomeoneAsWannaHelp(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_mark_as_wanna_help(self):
        person = Person.objects.get(user__username='paulproteus')
        p_before = Project.create_dummy()
        self.assertFalse(mysite.search.models.WannaHelperNote.objects.all())

        self.assertFalse(p_before.people_who_wanna_help.all())

        client = self.login_with_client()
        post_to = reverse(mysite.project.views.wanna_help_do)
        client.post(post_to, {u'project': unicode(p_before.pk)})

        p_after = Project.objects.get(pk=p_before.pk)

        self.assertEqual(
            list(p_after.people_who_wanna_help.all()),
            [person])

        note = mysite.search.models.WannaHelperNote.objects.get()
        self.assertEqual(note.person, person)
        self.assertEqual(note.project, p_after)

    def test_unmark_as_wanna_help(self):
        # We're in there...
        person = Person.objects.get(user__username='paulproteus')
        p_before = Project.create_dummy()
        p_before.people_who_wanna_help.add(person)
        p_before.save()
        mysite.search.models.WannaHelperNote.add_person_project(person, p_before)

        # Submit that project to unlist_self_from_wanna_help_do
        client = self.login_with_client()
        post_to = reverse(mysite.project.views.unlist_self_from_wanna_help_do)
        client.post(post_to, {u'project': unicode(p_before.pk)})

        # Are we gone yet?
        p_after = Project.objects.get(pk=p_before.pk)

        self.assertFalse(p_after.people_who_wanna_help.all())

    def test_mark_as_contacted(self):
        person = Person.objects.get(user__username='paulproteus')
        p_before = Project.create_dummy()
        p_before.people_who_wanna_help.add(person)
        p_before.save()
        mysite.search.models.WannaHelperNote.add_person_project(person, p_before)

        client = self.login_with_client()
        post_to = reverse(mysite.project.views.mark_contacted_do)
        vars = {u'mark_contact-project': unicode(p_before.pk),
                u'helper-%s-checked' % (person.pk,) : unicode('on'),
                u'helper-%s-person_id' % (person.pk) : unicode(person.pk),
                u'helper-%s-project_id' % (person.pk) : unicode(p_before.pk)}
        client.post(post_to, vars)

        whn_after = mysite.search.models.WannaHelperNote.objects.get(person=person, project=p_before)
        self.assertTrue(whn_after.contacted_on)
        self.assertTrue(whn_after.contacted_by, datetime.date.today())

class WannaHelpSubmitHandlesNoProjectIdGracefully(TwillTests):
    def test(self):
        # Submit nothing.
        post_to = reverse(mysite.project.views.wanna_help_do)
        response = self.client.post(post_to, {}, follow=True)
        self.assertEqual(response.status_code, 400)


class WannaHelpWorksAnonymously(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_mark_as_helper_anonymously(self):
        # Steps for this test
        # 1. User fills in the form anonymously
        # 2. We test that the Answer is not yet saved
        # 3. User logs in
        # 4. We test that the Answer is saved

        project_id = Project.create_dummy(name='Myproject').id

        # At the start, no one wants to help our project.
        self.assertFalse(Project.objects.get(id=project_id).people_who_wanna_help.all())

        # Click the button saying we want to help!
        post_to = reverse(mysite.project.views.wanna_help_do)
        response = self.client.post(post_to, {u'project': unicode(project_id)}, follow=True)

        # Make sure we are redirected to the right place
        self.assertEqual(response.redirect_chain,
            [('http://testserver/account/login/?next=%2Fprojects%2FMyproject%3Fwanna_help%3Dtrue', 302)])

        # check that the session can detect that we want to help Ubuntu out
        self.assertEqual(self.client.session['projects_we_want_to_help_out'],
                         [project_id])

        # According to the database, no one wants to help our project.
        self.assertFalse(Project.objects.get(id=project_id).people_who_wanna_help.all())

        # But when the user is logged in and *then* visits the project page
        login_worked = self.client.login(username='paulproteus',
                                         password="paulproteus's unbreakable password")
        self.assert_(login_worked)

        # Visit the project page...
        self.client.get(Project.objects.get(id=project_id).get_url())

        # After the GET, we've removed our note in the session
        self.assertFalse(self.client.session.get('projects_we_want_to_help_out', None))

        # then the DB knows the user wants to help out!
        self.assertEqual(list(Project.objects.get(id=project_id).people_who_wanna_help.all()),
                         [Person.objects.get(user__username='paulproteus')])
        self.assert_(mysite.search.models.WannaHelperNote.objects.all())

        # Say we're not interested anymore.
        post_to = reverse(mysite.project.views.unlist_self_from_wanna_help_do)
        response = self.client.post(post_to, {u'project': unicode(project_id)}, follow=True)

        # And now the DB shows we have removed ourselves.
        self.assertFalse(Project.objects.get(id=project_id).people_who_wanna_help.all())
        self.assertFalse(mysite.search.models.WannaHelperNote.objects.all())

class ProjectPageTellsNextStepsForHelpersToBeExpanded(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus',
                'miro-project']

    def test_default_to_false(self): # FIXME: Make it default to True soon
        client = self.login_with_client()
        response = client.get('/projects/Miro')
        self.assertFalse(response.context[0].get(
            'expand_next_steps', None))

class OffsiteAnonymousWannaHelpWorks(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test(self):
        # Steps for this test
        # 1. User POSTs to the wannahelp POST handler, indicating the request came from offsite
        # 2. User is redirected to a login page that knows the request came from offsite
        project_id = Project.create_dummy(name='Myproject').id

        # At the start, no one wants to help our project.
        self.assertFalse(Project.objects.get(id=project_id).people_who_wanna_help.all())

        # Click the button saying we want to help!
        post_to = reverse(mysite.project.views.wanna_help_do)
        response = self.client.post(post_to,
                                    {u'project': unicode(project_id),
                                     u'from_offsite': u'True'}, follow=True)

        # Make sure the session knows we came from offsite. Login-related
        # templates want this knowledge.
        self.assert_(self.client.session.get('from_offsite', False))

        ## FIXME: There should be a cancel button letting the user
        ## destroy the session and then go back to the Referring page.

        # Make sure we are redirected to the right place
        self.assertEqual(response.redirect_chain,
            [('http://testserver/account/login/?next=%2Fprojects%2FMyproject%3Fwanna_help%3Dtrue', 302)])

        lucky_projects = mysite.project.view_helpers.get_wanna_help_queue_from_session(self.client.session)
        self.assertEqual([k.name for k in lucky_projects], ['Myproject'])

class DecideWhichProjectDescriptionsAppearOnProjectPage(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus', 'user-barry', 'person-barry']

    def test(self):

        # Create a project.
        project = Project.create_dummy()

        # Create two profiles, each with a PortfolioEntry linking it to the
        # project, each with descriptions.
        def create_pfe_with_description(username):
            return PortfolioEntry.create_dummy(project=project,
                    person=Person.get_by_username(username),
                    is_published=True)
        pfes = {'uncheck_me': create_pfe_with_description('paulproteus'),
                'keep_me_checked': create_pfe_with_description('barry')}

        # Get a list of the PortfolioEntries that we use to get a random project
        # description for the project page.
        descriptions = project.get_pfentries_with_usable_descriptions()

        # Observe that the list contains both PortfolioEntries.
        for entry in pfes.values():
            self.assert_(entry in descriptions)

        self.login_with_twill()

        # Go to the project page.
        url = urlparse.urljoin("http://openhatch.org", project.get_edit_page_url())
        tc.go(better_make_twill_url(url))

        # In preparation for the next set of assertions, make sure that the
        # entries don't have the same description.
        self.assertNotEqual(
                pfes['uncheck_me'].project_description,
                pfes['keep_me_checked'].project_description)

        # See a list of project descriptions on the page, which equals the list of
        # descriptions in the DB.
        for entry in pfes.values():
            tc.find(entry.project_description)

        # Uncheck one of the checkboxes and submit the form
        name_of_checkbox_to_uncheck = "%s-use_my_description" % pfes['uncheck_me'].pk
        tc.fv("2", name_of_checkbox_to_uncheck, False)
        tc.submit()

        # Get a list of the PortfolioEntries that we use to get a random project
        # description for the project page.
        good_pfentries = project.get_pfentries_with_usable_descriptions()

        # Observe that the list contains only the checked PortfolioEntry.
        self.assert_(pfes['uncheck_me'] not in good_pfentries)
        self.assert_(pfes['keep_me_checked'] in good_pfentries)

class BugTrackersOnProjectEditPage(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus', 'user-barry', 'person-barry']

    def setUp(self):
        super(BugTrackersOnProjectEditPage, self).setUp()
        self.twisted = mysite.search.models.Project.create_dummy(name='Twisted System')

    def test_empty_at_start(self):
        self.assertFalse(self.twisted.get_corresponding_bug_trackers())

    def test_trackers_created_for_project_show_up(self):
        # Create a Roundup model
        bug_tracker = mysite.customs.models.RoundupTrackerModel(
            tracker_name='dummy',
            base_url='http://example.com/',
            closed_status='resolved')
        bug_tracker.created_for_project = self.twisted
        bug_tracker.save()

        # Now, the Twisted project should have one corresponding bug tracker
        trackers_from_project = list(self.twisted.get_corresponding_bug_trackers())
        self.assertEqual([bug_tracker], trackers_from_project)
