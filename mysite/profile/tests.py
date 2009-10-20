# Imports {{{
from mysite.base.tests import make_twill_url, TwillTests

from mysite.search.models import Project
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_Person_Tag, Link_ProjectExp_Tag, DataImportAttempt, PortfolioEntry, Citation

import mysite.profile.views
import mysite.profile.models
import mysite.profile.controllers

from mysite.profile import views

from django.conf import settings

from mysite.customs import ohloh 

import re
from StringIO import StringIO
import urllib
import simplejson
import BeautifulSoup
import time
import tasks 
import mock

import django.test
from django.test.client import Client
from django.core import management
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

import twill
from twill import commands as tc
from twill.shell import TwillCommandLoop
# }}}

class ProfileTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus',
            'cchost-data-imported-from-ohloh']

    def testSlash(self):
        response = self.client.get('/people/')

    def test__projectexp_add(self):
        # {{{
        username = 'paulproteus'

        project_name = 'seeseehost'
        description = 'did some work'
        url = 'http://example.com/'
        exp = ProjectExp.create_from_text(username, project_name,
                                    description, url)
        found = list(ProjectExp.objects.filter(person__user__username=username))
        # Verify it shows up in the DB
        self.assert_('seeseehost' in [f.project.name for f in found])

        # Verify it shows up in the data passed to the portfolio view.
        client = self.login_with_client()

        paulproteus_portfolio_url = reverse(mysite.profile.views.display_person_web, kwargs={
            'user_to_display__username': 'paulproteus'})
        response = client.get(paulproteus_portfolio_url)

        # Check that the newly added project is there.
        projects = response.context[0]['projects']
        self.assert_(exp.project in projects)
        # }}}

    def test__project_exp_create_from_text__unit(self):
        # {{{

        # Create requisite objects
        person = Person.objects.get(user__username='paulproteus')
        project = Project.objects.get(name='ccHost')

        # Assemble text input
        username = person.user.username
        project_name = project.name
        description = "sample description"
        url = "http://sample.com"
        man_months = "3"
        primary_language = "perl"

        ProjectExp.create_from_text(
                person.user.username,
                project.name,
                description,
                url,
                man_months,
                primary_language)
        # }}}

    def test_change_my_name(self):
        """Test that user can change his/her first and last name, and that it appears in the logged-in user's profile page."""
        # {{{
        self.login_with_twill()

        # Assert we're on profile page.
        tc.url('/people/paulproteus')

        # No named entered yet
        tc.notfind('Newfirst Newlast')

        # Let's go enter a name
        tc.go(make_twill_url('http://openhatch.org/edit/name'))
        tc.fv('edit_name', 'first_name', 'Newfirst')
        tc.fv('edit_name', 'last_name', 'Newlast')
        tc.submit()

        tc.url('/people/paulproteus')

        # Has name been entered correctly? Hope so!
        tc.find('Newfirst')
        tc.find('Newlast')
        # }}}

    # }}}

class DebTagsTests(TwillTests):
    # {{{

    def testAddOneDebtag(self):
        tag = views.add_one_debtag_to_project('alpine', 'implemented-in::c')
        self.assertEqual(views.list_debtags_of_project('alpine'),
                         ['implemented-in::c'])

    def testImportDebtags(self):
        views.import_debtags(cooked_string=
                                     'alpine: works-with::mail, protocol::smtp') # side effects galore!
        self.assertEqual(set(views.list_debtags_of_project('alpine')),
                         set(['works-with::mail', 'protocol::smtp']))
    # }}}

#class ExpTag(TwillTests):

# If you're looking for SourceForge and FLOSSMole stuff, look in the repository history.

class PersonTabProjectExpTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def test_project_exp_page_template_displays_project_exp(self):
        # {{{
        self.login_with_twill()
        url = 'http://openhatch.org/people/paulproteus/'
        tc.go(make_twill_url(url))
        tc.find('ccHost')
        # }}}
    # }}}

class ProjectExpTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
            'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def projectexp_add(self, project__name, project_exp__description, project_exp__url, tc_dot_url_should_succeed=True):
        """Paulproteus can login and add a projectexp to bumble."""
        # {{{
        self.login_with_twill()

        tc.go(make_twill_url('http://openhatch.org/form/projectexp_add'))
        tc.fv('projectexp_add', 'project_name', project__name)
        tc.fv('projectexp_add', 'involvement_description', project_exp__description)
        tc.fv('projectexp_add', 'citation_url', project_exp__url)
        tc.submit()

        tc_url_matched = None
        try:
            tc.url('/people/.*/projects/')
            tc_url_matched = True
        except twill.errors.TwillAssertionError, e:
            tc_url_matched = False

        if tc_dot_url_should_succeed:
            assert tc_url_matched
        else:
            assert not tc_url_matched

        tc.find(project__name)
        tc.find(project_exp__description)
        tc.find(project_exp__url)
        # }}}

    def test_projectexp_add(self):
        """Paulproteus can login and add two projectexps."""
        # {{{
        self.login_with_twill()
        self.projectexp_add('asdf', 'qwer', 'http://jkl.com/')
        self.projectexp_add('asdf', 'QWER!', 'https://JKLbang.edu/')
        # }}}

    def test_projectexp_add(self):
        """Paulproteus can login and add two projectexps."""
        # {{{
        self.login_with_twill()

        # Test for basic success: All fields filled out reasonably
        self.projectexp_add('asdf', 'qwer', 'http://jkl.com/')
        # (once more with a weird character and weirdish url)
        self.projectexp_add('asdf', 'QWER!', 'https://JKLbang.edu/')

        # Test that empty descriptions are okay
        self.projectexp_add('asdf', '', 'https://JKLbang.edu/')

        # Test that URLs are validated
        self.projectexp_add('asdf', 'QWER!', 'not a real URL, what now', tc_dot_url_should_succeed=False)

        # }}}

    def test_projectexp_delete(self):
        '''The server can log in paulproteus remove the word 'ccHost' from his profile by posting to the delete controller's URL.'''
        # {{{
        client = Client()
        username='paulproteus'
        client.login(username=username,
                     password="paulproteus's unbreakable password")

        person_page = '/people/%s/' % urllib.quote(username)
        
        # Load up the profile page
        response = client.get(person_page)
        # See! It talks about ccHost!
        self.assertContains(response, 'ccHost')

        # POST saying we want to delete the ccHost experience...
        # luckily I read the fixture and I know its ID is 13
        deletion_handler_url = reverse(
                mysite.profile.views.projectexp_edit_do,
                kwargs={'project__name': 'ccHost'})
        response = client.post(deletion_handler_url,
                {'0-project_exp_id': '13', '0-delete_this': 'on'})
        
        # Now re-GET the profile
        response = client.get(person_page)

        # See! It no longer talks about ccHost!
        self.assertNotContains(response, 'ccHost')
        # }}}

    def test_projectexp_delete_unauthorized(self):
        '''Barry tries to delete a ProjectExp he doesn't own and fails.'''
        # {{{

        # Meet Barry, a shady character.
        barry = User.objects.get(username='barry')
        barry_password = 'parallelism'
        client = Client()
        login_success = client.login( username=barry.username, 
                password=barry_password)
        self.assert_(login_success)

        # Barry doesn't own ProjectExp #13
        self.assertNotEqual( barry,
                ProjectExp.objects.get(id=13).person.user)

        # What happens if he tries to delete ProjectExp #13
        deletion_handler_url = reverse(
                mysite.profile.views.projectexp_edit_do,
                kwargs={'project__name': 'ccHost'})
        response = client.post(deletion_handler_url,
                {'0-project_exp_id': '13', '0-delete_this': 'on'})

        # Still there, Barry. Keep on truckin'.
        self.assert_(ProjectExp.objects.get(id=13))

        # }}}

    def test_projectexp_delete_web(self):
        '''Notorious user of OpenHatch, paulproteus, can log in and remove the word 'ccHost' from his profile by clicking the appropriate delete button.'''
        # {{{

        self.login_with_twill()

        # Load up the ProjectExp edit page.
        project_name = 'ccHost'
        exp_url = 'http://openhatch.org/people/paulproteus/projects/%s' % (
                urllib.quote(project_name))
        tc.go(make_twill_url(exp_url))

        # See! It talks about ccHost!
        tc.find(project_name)

        # Click the correct delete button...
        tc.config('readonly_controls_writeable', True)
        tc.fv('delete-projectexp-13', 'id', '13')   # Bring twill's attention
                                                    # to the form named
                                                    # ``delete-projectexp-13''.
        tc.submit()

        # FIXME: What page are we on now?

        # Alakazam! It's gone.
        tc.notfind('ccHost')
        # }}}

    def test_projectexp_edit(self):
        """Paulproteus can edit information about his project experiences."""
        # {{{
        self.login_with_twill()

        # Let's go edit info about a project experience.
        editor_url = reverse(mysite.profile.views.projectexp_edit,
                kwargs={'project__name': 'ccHost'})
        tc.go(make_twill_url(editor_url))
        
        # Let's fill in the text fields like pros.
        tc.fv('1', '0-involvement_description', 'ze description')
        tc.fv('1', '0-citation_url', 'ze-u.rl')
        tc.fv('1', '0-man_months', '13')
        tc.fv('1', '0-primary_language', 'tagalogue')
        tc.fv('1', '0-delete_this', 'off')
        tc.submit()

        exp = ProjectExp.objects.get(project__name='ccHost')
        self.assertEqual(exp.description, 'ze description')
        self.assertEqual(exp.url, 'http://ze-u.rl/')
        self.assertEqual(exp.man_months, 13)
        self.assertEqual(exp.primary_language, 'tagalogue')
        self.assert_(exp.modified)
        # }}}

    def test_person_involvement_description(self):
        # {{{
        self.login_with_twill()
        username = 'paulproteus'
        project_name = 'ccHost'
        url = 'http://openhatch.org/people/%s/projects/%s' % (
                urllib.quote(username), urllib.quote(project_name))
        tc.go(make_twill_url(url))
        tc.find('1 month')
        tc.find('shell script')
        # }}}

    # FIXME: Move these next two functions to their proper home.

    tags = {
            'understands': ['ack', 'b', 'c'],
            'understands_not': ['dad', 'e', 'f'],
            'seeking': ['gone', 'h', 'i'],
            'studying': ['jam', 'k', 'l'],
            'can_mentor': ['mop', 'n', 'o'],
            }
    tags_2 = {
            'understands': ['Ack!', 'B!', 'C!'],
            'understands_not': ['dad', 'e', 'f'],
            'seeking': ['gone', 'h', 'i'],
            'studying': ['Jam?', 'K?', 'L?'],
            'can_mentor': ['mop', 'n', 'o'],
            }
    # FIXME: Test whitespace, too.

    # FIXME: Write a unit test for this.
    def update_tags(self, tag_dict):
        # {{{
        url = 'http://openhatch.org/people/edit/info'
        tc.go(make_twill_url(url))
        for tag_type_name in tag_dict:
            tc.fv('edit-tags', 'edit-tags-' + tag_type_name, ", ".join(tag_dict[tag_type_name]))
        tc.submit()

        # Check that at least the first tag made it into the database.
        self.assert_(list(Link_Person_Tag.objects.filter(
            tag__text=tag_dict.values()[0][0], person__user__username='paulproteus')))

        # Check that the output is correct.
        soup = BeautifulSoup.BeautifulSoup(tc.show())
        for tag_type_name in tag_dict:
            text = ''.join(soup(id='tags-%s' % tag_type_name)[0].findAll(text=True))
            self.assert_(', '.join(tag_dict[tag_type_name]) in ' '.join(text.split()))

        # Go back to the form and make sure some of these are there
        tc.go(make_twill_url(url))
        tc.find(tag_dict.values()[0][0])
        # }}}

    def test_tag_edit_once(self):
        # {{{
        self.login_with_twill()
        self.update_tags(self.tags)
        # }}}

    def test_tag_edit_twice(self):
        # {{{
        self.login_with_twill()
        self.update_tags(self.tags)
        self.update_tags(self.tags_2)
        # }}}

    # }}}

# Create a mock Ohloh get_contribution_info_by_username
mock_gcibu = mock.Mock()
# This object will always return:
mock_gcibu.return_value = [{
        'man_months': 1,
        'project': u'ccHost',
        'project_homepage_url':
            u'http://wiki.creativecommons.org/CcHost',
        'primary_language': u'shell script'}]

# Create a mock Ohloh get_contribution_info_by_ohloh_username
mock_gcibou = mock.Mock()
mock_gcibou.return_value = [{
        'man_months': 1,
        'project': u'who knows',
        'project_homepage_url':
            u'http://wiki.creativecommons.org/CcHost',
        'primary_language': u'Vala'}]

# Create a mock Launchpad get_info_for_launchpad_username
mock_giflu = mock.Mock()
mock_giflu.return_value = {
        'ccHost': {
            'url': 'http://launchpad.net/ccHost', # ok this url doesn't really exist
            'involvement_types': ['Bug Management', 'Bazaar Branches'],
            'languages': ['python', 'ruby'],
            }
        }

# FIXME: If this is made dynamically, it would be easier!
class MockFetchPersonDataFromOhloh(object):
    real_task_class = tasks.FetchPersonDataFromOhloh
    @classmethod
    def delay(*args, **kwargs):
        "Don't enqueue a background task. Just run the task."
        args = args[1:] # FIXME: Wonder why I need this
        task = MockFetchPersonDataFromOhloh.real_task_class()
        task.debugging = True # See FetchPersonDataFromOhloh
        task.run(*args, **kwargs)

class CeleryTests(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    # FIXME: One day, test that after self.test_slow_loading_via_emulated_bgtask
    # getting the data does not go out to Ohloh.

    def _test_data_source_via_emulated_bgtask(self, source, data_we_expect):
        "1. Go to the page that has paulproteus' data. "
        "2. Verify that the page doesn't yet know about ccHost. "
        "3. Prepare an object that will import data from ccHost. "
        "The object is a DataImportAttempt. The DataImportAttempt has a method "
        "that will create a background task using the celery package. The method "
        "is called do_what_it_says_on_the_tin, because it will attempt to "
        "import data. "
        "3. Run the celery task ourselves, but instead of going to Ohloh, "
        "we hand-prepare data for it."""

        # Let's run this test using a sample user, paulproteus.
        username = 'paulproteus'
        person = Person.objects.get(user__username=username)

        # Store a note in the DB that we're about to run a background task
        dia = DataImportAttempt(query=username, source=source, person=person)
        dia.person_wants_data = True
        dia.save()

        gimme_json_url = '/people/gimme_json_that_says_that_commit_importer_is_done'
        
        client = self.login_with_client()

        # Ask if background task has been completed.
        # We haven't even created the background task, so 
        # the answer should be no.
        response_before_task_is_run = client.get(gimme_json_url)
        response_json = simplejson.loads(response_before_task_is_run.content)
        self.assertEqual(response_json[0]['pk'], dia.id)
        self.assertFalse(response_json[0]['fields']['completed'])
        
        # Are there any PortfolioEntries for ccHost
        # before we import data? Expected: no.
        portfolio_entries = PortfolioEntry.objects.filter(project__name='ccHost')
        self.assertEqual(portfolio_entries.count(), 0)

        dia.do_what_it_says_on_the_tin()
        # NB: The task is being run, but the communication with the external data source
        # is mocked out.

        # Now that we have synchronously run the task, it should be
        # marked as completed.
        self.assert_(DataImportAttempt.objects.get(id=dia.id).completed)

        #######################################################
        # Let's see if the browser's method of checking agrees. 
        #######################################################

        # First, request the JSON again.
        response_after = client.get(gimme_json_url)

        # Ask if background task has been completed. (Hoping for yes.)
        response_json = simplejson.loads(response_after.content)
        self.assertEquals(response_json[0]['pk'], dia.id)
        self.assert_(response_json[0]['fields']['completed'])

        # There ought now to be a PortfolioEntry for ccHost...
        portfolio_entry = PortfolioEntry.objects.get(person=person, project__name='ccHost')

        # ...and the expected number of citations.
        citations = Citation.objects.filter(portfolio_entry=portfolio_entry)

        self.assert_(citations.count() > 0)

        # Let's make sure we got the data we expected.
        partial_citation_dicts = list(citations.values(*data_we_expect[0].keys()))
        self.assertEqual(partial_citation_dicts, data_we_expect)

        # Let's make sure that these citations are linked with the
        # DataImportAttempt we used to import them.
        for citation in citations:
            self.assertEqual(citation.data_import_attempt, dia)

    @mock.patch('mysite.customs.ohloh.Ohloh.get_contribution_info_by_username', mock_gcibu)
    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_ohloh_import_via_emulated_bgtask(self):
        "Test that we can import data from Ohloh, except don't test "
        "that Ohloh actually gives data. Instead, create a little "
        "placeholder that acts like Ohloh, and make sure we respond "
        "to it correctly."
        # {{{
        data_we_expect = [{
                'languages': mock_gcibu.return_value[0]['primary_language'],
                'distinct_months': mock_gcibu.return_value[0]['man_months'],
                'is_published': False,
                'is_deleted': False,
                #'year_started': 2007,
                }]
        return self._test_data_source_via_emulated_bgtask(
                source='rs', data_we_expect=data_we_expect)
        # }}}

    @mock.patch('mysite.customs.lp_grabber.get_info_for_launchpad_username', mock_giflu)
    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_launchpad_import_via_emulated_bgtask(self):
        "Test that we can import data from Ohloh, except don't test "
        "that Ohloh actually gives data. Instead, create a little "
        "placeholder that acts like Ohloh, and make sure we respond "
        "to it correctly."
        # {{{
        lp_result = mock_giflu.return_value.values()[0]
        data_we_expect = [
                {
                    'contributor_role': lp_result['involvement_types'][0],
                    'languages': ", ".join(lp_result['languages']),
                    'is_published': False,
                    'is_deleted': False,
                    },
                {
                    'contributor_role': lp_result['involvement_types'][1],
                    'languages': ", ".join(lp_result['languages']),
                    'is_published': False,
                    'is_deleted': False,
                    }
                ]
        return self._test_data_source_via_emulated_bgtask(
                source='lp', data_we_expect=data_we_expect)
        # }}}

    @mock.patch('mysite.customs.ohloh.Ohloh.get_contribution_info_by_username', mock_gcibu)
    @mock.patch('mysite.profile.tasks.FetchPersonDataFromOhloh', MockFetchPersonDataFromOhloh)
    def test_stale_dias_are_not_shown_in_json(self):
        """Create a DIA that is stale. Verify it is ignored by JSON."""
        # {{{
        # do this work for user = paulproteus
        username = 'paulproteus'
        person = Person.objects.get(user__username=username)

        stale_dia = DataImportAttempt(
                    stale=True,
                    query='who cares',
                    person=person,
                    source='rs')
        stale_dia.save()

        # Verify the JSON gives back an empty list
        c = self.login_with_client()

        url = '/people/gimme_json_that_says_that_commit_importer_is_done'
        response = c.get(url)
        decoded = simplejson.loads(response.content)

        self.assertEqual(decoded, [])

        # FIXME: One day, test that, after
        # self.test_slow_loading_via_emulated_bgtask,
        # getting the data does not go out to Ohloh.

        # }}}

    # }}}

class UserListTests(TwillTests):
    # {{{
    fixtures = [ 'user-paulproteus', 'person-paulproteus',
            'user-barry', 'person-barry']

    def test_display_list_of_users_web(self):
        # {{{
        self.login_with_twill()
        url = 'http://openhatch.org/people/'
        url = make_twill_url(url)
        tc.go(url)
        tc.find(r'paulproteus')
        tc.find(r'Barry Spinoza \(barry\)')

        tc.follow('paulproteus')
        tc.url('people/paulproteus') 
        tc.find('paulproteus')
        # }}}

    # }}}

class Importer(TwillTests):
    # {{{
    fixtures = ['user-paulproteus', 'person-paulproteus']

    form_url = "http://openhatch.org/people/portfolio/import/"

    @mock.patch('mysite.profile.models.DataImportAttempt.do_what_it_says_on_the_tin')
    def test_create_data_import_attempts(self, mock_do_what_it_says_on_the_tin):
        "Enqueue and track importation tasks."
        """
        Test the following behavior: 
        For each data source, enqueue a background task.
        Keep track of information about the task in an object
        called a DataImportAttempt."""

        paulproteus = Person.objects.get(user__username='paulproteus')
        input = {'committer_identifier': 'paulproteus'}

        def count_tasks_for_paulproteus():
            return DataImportAttempt.objects.filter(person=paulproteus).count()

        self.assertEqual(count_tasks_for_paulproteus(), 0,
                "Pre-condition: "
                "No tasks for paulproteus.")

        response = self.client.get(reverse(mysite.profile.views.start_importing), input)

        # FIXME: We should also check that we call this function
        # once for each data source.
        self.assert_(mock_do_what_it_says_on_the_tin.called)

        self.assertEqual(response.content, "[{'success': 1}]",
                "Post-condition: "
                "profile.views.start_importing sent a success message via JSON.")

        for (source_key, _) in DataImportAttempt.SOURCE_CHOICES:
            self.assertEqual(DataImportAttempt.objects.filter(
                person=paulproteus, source=source_key).count(),
                1,
                "Post-condition: "
                "paulproteus has a task recorded in the DB "
                "for source %s." % source_key)

    def test_action_via_view(self):
        """Send a Person objects and a list of usernames and email addresses to the action controller. Test that the controller really added some corresponding DIAs for that Person."""
        # {{{
        client = Client()
        username='paulproteus'
        client.login(username=username,
                     password="paulproteus's unbreakable password")

        data = {}
        commit_usernames_and_emails = ["bilbo", "bilbo@baggin.gs"]
        for n, cu in enumerate(commit_usernames_and_emails):
            data["identifier_%d" % n] = cu

        # Not a DIA in sight.
        self.assertFalse(list(DataImportAttempt.objects.filter(person=Person.objects.get(user__username='paulproteus'))))

        response = client.post('/people/portfolio/import/prepare_data_import_attempts_do', data) 

        # DIAs, nu?
        self.assert_(list(DataImportAttempt.objects.filter(person=Person.objects.get(user__username='paulproteus'))))
        #}}}

    def test_prepare_data_import_attempts(self):
        user = User.objects.get(username='paulproteus')
        self.assertEqual(len(DataImportAttempt.objects.filter(person=user.get_profile())), 0)
        post = {
                'identifier_0': 'paulproteus',
                'checkbox_0_rs': 'on',
                'checkbox_0_lp': 'on',
                'checkbox_0_ou': 'on'
                }
        views.prepare_data_import_attempts(post, user)
        self.assertEqual(len(DataImportAttempt.objects.filter(person=user.get_profile())), 3)

    # }}}

class UserCanShowEmailAddress(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    # {{{
    def test_show_email(self):
        """This test: (a) verifies my@ema.il does not appear on paulproteus's profile page, then goes to his account settings and opts in to showing it, and then verifies it does appear."""
        # {{{
        self.login_with_twill()

        tc.go('/people/paulproteus/')
        tc.notfind('my@ema.il')

        tc.follow('settings')
        tc.follow('contact info')
        tc.fv(1, 'show_email', '1')
        tc.submit()

        tc.go('/people/paulproteus/')
        tc.find('my@ema.il')
        # }}}
    # }}}

class BugsAreRecommended(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus',
               'bugs-for-two-projects.json']

    def test_recommendations_found(self):
        # Recommendations defined like this:
        # the first N bugs matching the various "recommended searches" (N=5?)

        # It's round-robin across the searches.
        # So if we create two Python bugs and one C# bug, and we set N to 2,
        # and paulproteus ought to get hits from Python and C#, we should see
        # only one Python bug.
        recommended = list(mysite.profile.controllers.recommend_bugs(['Python', 'C#'], n=2))
        python_bugs = [ bug for bug in recommended if bug.project.language == 'Python']
        self.assertEqual(len(python_bugs), 1)
        csharp_bugs = [ bug for bug in recommended if bug.project.language == 'C#']
        self.assertEqual(len(csharp_bugs), 1)
        
    def test_recommendations_not_duplicated(self):
        """ Run two equivalent searches in parallel, and discover that they weed out duplicates."""
        recommended = list(mysite.profile.controllers.recommend_bugs(['Python', 'Python'], n=2))
        self.assertNotEqual(recommended[0], recommended[1])

class OnlyFreshDiasAreSelected(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    @mock.patch("mysite.profile.models.DataImportAttempt.do_what_it_says_on_the_tin")
    def test_dias_created_only_once(self, mock_dia_do_what_it_says):
        query = 'query'
        source = 'oh'
        person = Person.objects.get(user__username='paulproteus')

        self.assertEqual(0, DataImportAttempt.objects.count())
        
        mysite.profile.views.get_most_recent_data_import_attempt_or_create(
            query, source, person)

        self.assertEqual(1, DataImportAttempt.objects.count())

        mysite.profile.views.get_most_recent_data_import_attempt_or_create(
            query, source, person)

        self.assertEqual(1, DataImportAttempt.objects.count())        

    @mock.patch("mysite.profile.models.DataImportAttempt.do_what_it_says_on_the_tin")
    def test_dias_created_again_for_stale_dias(self, mock_dia_do_what_it_says):
        query = 'query'
        source = 'oh'
        person = Person.objects.get(user__username='paulproteus')

        self.assertEqual(0, DataImportAttempt.objects.count())
        
        mysite.profile.views.get_most_recent_data_import_attempt_or_create(
            query, source, person)

        self.assertEqual(1, DataImportAttempt.objects.count())

        # Now, set that one to stale:
        dia = DataImportAttempt.objects.get()
        dia.stale = True
        dia.save()

        mysite.profile.views.get_most_recent_data_import_attempt_or_create(
            query, source, person)

        self.assertEqual(2, DataImportAttempt.objects.count())


    def test_showing_checkbox_marks_dia_as_stale(self):
        c = self.login_with_client()
        
        # First, make a DIA. Make it already completed.
        dia_done = DataImportAttempt(
                    query='query',
                    completed=True,
                    person=Person.objects.get(user__username='paulproteus'),
                    source='lp')
        dia_done.save()

        self.assertFalse(dia_done.stale)

        # Now, get the JSON
        
        url = '/people/gimme_json_that_says_that_commit_importer_is_done'
        response = c.get(url)

        # Now verify it's done
        self.assert_(DataImportAttempt.objects.get().stale)

class PersonInfoLinksToSearch(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']
    
    def test_whatever(self):
        '''
        * Have a user, say that he understands+wantstolearn+currentlylearns+canmentor something
        * Go to his user page, and click those various links
        * Find yourself on some search page that mentions the user.
        '''
        tags = {
            'understands': ['thing1'],
            'understands_not': ['thing2'],
            'seeking': ['thing3'],
            'studying': ['thing4'],
            'can_mentor': ['thing5'],
            }

        # Log in as paulproteus
        
        self.login_with_twill()

        # Update paulproteus's tags
        url = 'http://openhatch.org/people/edit/info'
        tc.go(make_twill_url(url))
        for tag_type_name in tags:
            tc.fv('edit-tags', 'edit-tags-' + tag_type_name, ", ".join(tags[tag_type_name]))
        tc.submit()

        # Now, click on "thing1"
        tc.follow("thing1")

        # Now find ourself there
        tc.find('Asheesh Laroia')

class Widget(TwillTests):
    fixtures = ['user-paulproteus', 'person-paulproteus']

    def test_widget_display(self):
        widget_url = reverse(mysite.profile.views.widget_display,
                kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        response = client.get(widget_url)

    def test_widget_display_js(self):
        widget_js_url = reverse(mysite.profile.views.widget_display_js,
                kwargs={'user_to_display__username': 'paulproteus'})
        client = self.login_with_client()
        response = client.get(widget_js_url)

class PersonalData(TwillTests):
    fixtures = ['user-paulproteus', 'user-barry', 'person-barry',
            'person-paulproteus', 'cchost-data-imported-from-ohloh']

    def test_all_views_that_call_get_personal_data(self):
        # Views where you can look at somebody else.
        stalking_view2args = {
                mysite.profile.views.display_person_web: {'user_to_display__username': 'paulproteus'},
                mysite.profile.views.projectexp_display: {'user_to_display__username': 'paulproteus', 'project__name': 'ccHost'},
                }

        # Views where you look only at yourself.
        navelgazing_view2args = {
                mysite.profile.views.display_person_edit_web: {},
                mysite.profile.views.projectexp_add_form: {},
                mysite.profile.views.projectexp_edit: {'project__name': 'ccHost'},
                mysite.profile.views.importer: {},
                mysite.profile.views.display_person_edit_name: {},
                }

        for view in stalking_view2args:
            self.client.login(username='barry', password='parallelism')
            kwargs = stalking_view2args[view]
            url = reverse(view, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(response.context[0]['person'].user.username, 'paulproteus')
            self.client.logout()

        for view in navelgazing_view2args:
            client = self.login_with_client()
            kwargs = navelgazing_view2args[view]
            url = reverse(view, kwargs=kwargs)
            response = client.get(url)
            self.assertEqual(response.context[0]['person'].user.username, 'paulproteus')
            client.logout()

# vim: set ai et ts=4 sw=4 nu:
