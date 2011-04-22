# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 Karen Rustad
# Copyright (C) 2011 Jack Grigg
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

import importlib

from django.db import models
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.cache import cache
from django.conf import settings
import datetime
import StringIO
import uuid
import urllib
from urlparse import urljoin
import random
from django.db.models import Q
import mysite.customs
import mysite.base.unicode_sanity
from django.core.urlresolvers import reverse
import voting
import hashlib
import celery.decorators
import mysite.customs.ohloh
try:
    import Image
except:
    from PIL import Image

class OpenHatchModel(models.Model):
    created_date = models.DateTimeField(null=True, auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

def get_image_data_scaled(image_data, width):
    # scale it
    image_fd = StringIO.StringIO(image_data)
    im = Image.open(image_fd)
    image_fd.seek(0)

    w, h = get_image_dimensions(image_fd)

    new_w = width
    new_h = (h * 1.0 / w) * width

    smaller = im.resize((new_w, new_h),
                        Image.ANTIALIAS)

    # "Save" it to memory
    new_image_fd = StringIO.StringIO()
    smaller.save(new_image_fd, format='PNG')
    new_image_fd.seek(0)

    # pull data out
    image_data = new_image_fd.getvalue()
    return image_data


class Project(OpenHatchModel):
    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.name
        super(Project, self).save(*args, **kwargs)

    @staticmethod
    def generate_random_icon_path(instance, filename):
        # MEDIA_ROOT is prefixed automatically.
        return 'images/icons/projects/%s.png' % uuid.uuid4().hex

    def name_with_quotes_if_necessary(self):
        if '"' in self.name:
            # GIVE UP NOW, it will not tokenize properly
            return self.name
        elif ' ' in self.name:
            return '"%s"' % self.name
        return self.name

    @mysite.base.decorators.cached_property
    def potential_mentors(self):
        """Return the union of the people who can mentor in this project,
        or who can mentor in the project's language."""
        import mysite.profile.controllers
        mentor_set = set(mysite.profile.controllers.people_matching(
            'can_mentor', self.name))
        mentor_set.update(mysite.profile.controllers.people_matching(
                'can_mentor', self.language))
        return mentor_set

    @staticmethod
    def create_dummy(**kwargs):
        now = datetime.datetime.utcnow()
        data = dict(name=uuid.uuid4().hex,
                icon_raw='/static/no-project-icon.png',
                    language='C')
        data.update(kwargs)
        ret = Project(**data)
        ret.save()
        return ret
        
    @staticmethod
    def create_dummy_no_icon(**kwargs):
        now = datetime.datetime.utcnow()
        data = dict(name=uuid.uuid4().hex,
                icon_raw='',
                    language='C')
        data.update(kwargs)
        ret = Project(**data)
        ret.save()
        return ret

    name = models.CharField(max_length=200, unique=True,
            help_text='<span class="example">This is the name that will uniquely identify this project (e.g. in URLs), and this box is fixing capitalization mistakes. To change the name of this project, email <a style="color: #666;" href="mailto:%s">%s</a>.</span>' % (('hello@openhatch.org',)*2))
    display_name = models.CharField(max_length=200, default='',
            help_text='<span class="example">This is the name that will be displayed for this project, and is freely editable.</span>')
    display_name = models.CharField(max_length=200, default='')
    homepage = models.URLField(max_length=200, blank=True, default='',
            verbose_name='Project homepage URL')
    language = models.CharField(max_length=200, blank=True, default='',
            verbose_name='Primary programming language')

    def invalidate_all_icons(self):
        self.icon_raw = None
        self.icon_url = u''
        self.icon_for_profile = None
        self.icon_smaller_for_badge = None
        self.icon_for_search_result = None
        pass

    def get_random_pfentry_that_has_a_project_description(self):
        import random
        pfentries = self.portfolioentry_set.exclude(project_description='')
        only_good_pfentries = lambda pfe: pfe.project_description.strip()
        pfentries = filter(only_good_pfentries, pfentries)

        if pfentries:
            return random.choice(pfentries)
        else:
            return None

    # FIXME: Remove this field and update fixtures.
    icon_url = models.URLField(max_length=200)

    icon_raw = models.ImageField(
            upload_to=lambda a,b: Project.generate_random_icon_path(a, b),
            null=True,
            default=None,
            blank=True,
            verbose_name='Icon',
            )

    date_icon_was_fetched_from_ohloh = models.DateTimeField(null=True, default=None)

    icon_for_profile = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    icon_smaller_for_badge = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    icon_for_search_result = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    logo_contains_name = models.BooleanField(default=False)

    people_who_wanna_help = models.ManyToManyField('profile.Person',
                                                   related_name='projects_i_wanna_help')

    # Cache the number of OpenHatch members who have contributed to this project.
    cached_contributor_count = models.IntegerField(default=0, null=True)

    def populate_icon_from_ohloh(self):

        oh = mysite.customs.ohloh.get_ohloh()
        try:
            icon_data = oh.get_icon_for_project(self.name)
            self.date_icon_was_fetched_from_ohloh = datetime.datetime.utcnow()
        except ValueError:
            self.date_icon_was_fetched_from_ohloh = datetime.datetime.utcnow()
            return False

        # if you want to scale, use get_image_data_scaled(icon_data)
        self.icon_raw.save('', ContentFile(icon_data))

        # Since we are saving an icon, also update our scaled-down version of
        # that icon for the badge.
        self.update_scaled_icons_from_self_icon()
        return True

    def get_url_of_icon_or_generic(self):
        # Recycle icon_smaller_for_badge since it's the same size as
        # the icon for most other uses (profiles, etc.).
        if self.icon_for_profile:
            return self.icon_for_profile.url
        else:
            return settings.MEDIA_URL + 'no-project-icon.png'

    def get_url_of_badge_size_icon_or_generic(self):
        if self.icon_smaller_for_badge:
            return self.icon_smaller_for_badge.url
        else:
            return settings.MEDIA_URL + 'no-project-icon-w=40.png'

    def get_url_of_search_result_icon_or_generic(self):
        if self.icon_for_search_result:
            return self.icon_for_search_result.url
        else:
            return settings.MEDIA_URL + 'no-project-icon-w=20.png'

    def update_scaled_icons_from_self_icon(self):
        '''This method should be called when you update the Project.icon_raw attribute.
        Side-effect: Saves a scaled-down version of that icon in the
        Project.icon_smaller_for_badge field.'''
        # First of all, do nothing if self.icon_raw is a false value.
        if not self.icon_raw:
            return
        # Okay, now we must have some normal-sized icon. 

        raw_icon_data = self.icon_raw.file.read()

        # Scale raw icon to a size for the profile.
        profile_icon_data = get_image_data_scaled(raw_icon_data, 64)
        self.icon_for_profile.save('', ContentFile(profile_icon_data))

        # Scale it down to badge size, which
        # happens to be width=40
        badge_icon_data = get_image_data_scaled(raw_icon_data, 40)
        self.icon_smaller_for_badge.save('', ContentFile(badge_icon_data))

        # Scale normal-sized icon down to a size that fits in the search results--20px by 20px
        search_result_icon_data = get_image_data_scaled(raw_icon_data, 20)
        self.icon_for_search_result.save('', ContentFile(search_result_icon_data))

    def get_contributors(self):
        """Return a list of Person objects who are contributors to
        this Project."""
        from mysite.profile.models import Person
        return Person.objects.filter(
                portfolioentry__project=self, 
                portfolioentry__is_deleted=False,
                portfolioentry__is_published=True
                ).distinct()


    def update_cached_contributor_count_and_save(self):
        contributors = self.get_contributors()
        self.cached_contributor_count = len(contributors)
        self.save()

    def get_n_other_contributors_than(self, n, person):
        import random
        # FIXME: Use the method above.
        from mysite.profile.models import PortfolioEntry
        pf_entries = list(PortfolioEntry.published_ones.filter(
            project=self).exclude(person=person))
        random.shuffle(pf_entries)
        other_contributors = [p.person for p in pf_entries]

        photod_people = [person for person in other_contributors if person.photo]
        unphotod_people = [person for person in other_contributors if not person.photo]
        ret = []
        ret.extend(photod_people)
        ret.extend(unphotod_people)

        return ret[:n]

    def __unicode__(self):
        return "name='%s' display_name='%s' language='%s'" % (self.name, self.display_name, self.language)
    
    def get_url(self):
        import mysite.project.views
        return reverse(mysite.project.views.project,
                kwargs={'project__name': mysite.base.unicode_sanity.quote(self.name)}) 

    def get_edit_page_url(self):
        import mysite.project.views
        return reverse(mysite.project.views.edit_project,
                kwargs={'project__name': mysite.base.unicode_sanity.quote(self.name)}) 

    @mysite.base.decorators.cached_property
    def get_mentors_search_url(self):
        import mysite.profile.controllers
        mentor_count = len(set(mysite.profile.controllers.people_matching(
            'can_mentor', self.name)))
        if mentor_count > 0 or self.language:
            query_var = self.name
            if mentor_count == 0:
                query_var = self.language
            query_string = mysite.base.unicode_sanity.urlencode({u'q': u'can_mentor:"%s"' %
                                             query_var})
            return reverse(mysite.profile.views.people) + '?' + query_string
        else:
            return ""

    def get_open_bugs(self):
        return Bug.open_ones.filter(project=self)

    def get_open_bugs_randomly_ordered(self):
        return self.get_open_bugs().order_by('?')

    def get_pfentries_with_descriptions(self, listen_to_the_community=False, **kwargs):
        pfentries = self.portfolioentry_set.exclude(project_description='').filter(**kwargs)
        if listen_to_the_community:
            # Exclude pfentries that have been unchecked on the project edit page's
            # descriptions section.
            pfentries = pfentries.filter(use_my_description=True, )
        has_a_description = lambda pfe: pfe.project_description.strip()
        return filter(has_a_description, pfentries)

    def get_pfentries_with_usable_descriptions(self):
        return self.get_pfentries_with_descriptions(listen_to_the_community=True)

    def get_random_description(self):
        pfentries = self.get_pfentries_with_usable_descriptions()
        if pfentries:
            return random.choice(pfentries)
        else:
            return None
    
def populate_icon_on_project_creation(instance, raw, created, *args, **kwargs):
    if raw:
        return

    import mysite.search.tasks
    if created and not instance.icon_raw:
        task = mysite.search.tasks.PopulateProjectIconFromOhloh()
        task.delay(project_id=instance.id)

def grab_project_language_from_ohloh(instance, raw, created, *args,
                                     **kwargs):
    if raw:
        return

    import mysite.search.tasks
    if created and not instance.language:
        task = mysite.search.tasks.PopulateProjectLanguageFromOhloh()
        task.delay(project_id=instance.id)

models.signals.post_save.connect(populate_icon_on_project_creation, Project)
models.signals.post_save.connect(grab_project_language_from_ohloh, Project)

class WrongIcon(OpenHatchModel):

    @staticmethod
    def spawn_from_project(project):
        kwargs = {
            'project': project,
            'icon_url': project.icon_url,
            'icon_raw': project.icon_raw,
            'date_icon_was_fetched_from_ohloh': project.date_icon_was_fetched_from_ohloh,
            'icon_for_profile': project.icon_for_profile,
            'icon_smaller_for_badge': project.icon_smaller_for_badge,
            'icon_for_search_result': project.icon_for_search_result,
            'logo_contains_name': project.logo_contains_name,
        }
        wrong_icon_obj = WrongIcon(**kwargs)
        wrong_icon_obj.save()
        return wrong_icon_obj


    project = models.ForeignKey(Project)

    icon_url = models.URLField(max_length=200)

    icon_raw = models.ImageField(
            upload_to=lambda a,b: Project.generate_random_icon_path(a, b),
            null=True,
            default=None)

    date_icon_was_fetched_from_ohloh = models.DateTimeField(null=True, default=None)

    icon_for_profile = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    icon_smaller_for_badge = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    icon_for_search_result = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    logo_contains_name = models.BooleanField(default=False)

class ProjectInvolvementQuestion(OpenHatchModel):
    key_string = models.CharField(max_length=255)
    text = models.TextField()
    is_bug_style = models.BooleanField(default=False)

    def get_answers_for_project(self, a_project):
        def get_score(obj):
            return (-1)* voting.models.Vote.objects.get_score(obj)['score']
        the_answers = list(self.answers.filter(project=a_project))
        # TODO: sort them
        the_answers.sort(key=get_score)
        return the_answers

    @staticmethod
    def create_dummy(**kwargs):
        data = {'text': 'how are you doing?'}
        data.update(kwargs)
        ret = ProjectInvolvementQuestion(**data)
        ret.save()
        return ret

class OwnedAnswersManager(models.Manager):
    def get_query_set(self):
        return super(OwnedAnswersManager, self).get_query_set().filter(
            author__isnull=False)

class Answer(OpenHatchModel):
    title = models.CharField(null=True, max_length=255)
    text = models.TextField(blank=False)
    author = models.ForeignKey(User, null=True)
    question = models.ForeignKey(ProjectInvolvementQuestion, related_name='answers')
    project = models.ForeignKey(Project)
    objects = OwnedAnswersManager()
    all_even_unowned = models.Manager()

    def get_question_text(self, mention_project_name=True):
        if self.question.key_string == 'where_to_start':
            retval =  "I'd like to participate%s. How do I begin?" % (
                        " in %s" % self.project.display_name if mention_project_name else "")
        elif self.question.key_string == 'stress':
            retval = "What is a bug or issue%s that you've been putting off, neglecting or just plain avoiding?" % (
                        " with %s" % self.project.display_name if mention_project_name else "")
        elif self.question.key_string == 'newcomers':
            retval =  "What's a good bug%s for a newcomer to tackle?" % (
                        " in %s" % self.project.display_name if mention_project_name else "")
        elif self.question.key_string == 'non_code_participation':
            retval =  "Other than writing code, how can I contribute%s?" % (
                        " to %s" % self.project.display_name if mention_project_name else "")
        else: # Shouldn't get here.
            retval = ""
        return retval

    @property
    def template_for_feed(self):
        return 'base/answer-in-feed.html'

    def get_title_for_atom(self):
        return "%s added an answer for %s" % (
                self.author.get_profile().get_full_name_and_username(),
                self.project.display_name)

    def get_description_for_atom(self):
        return "%s added an answer to the question \"%s\"" % (
                self.author.get_profile().get_full_name_and_username(),
                self.get_question_text())

    def get_absolute_url(self):
        return urljoin(reverse('mysite.project.views.project', args=[self.project.name]), "#answer_whose_pk_is_%d" % self.pk)

    @staticmethod
    def create_dummy(**kwargs):
        data = {
                'text': 'i am doing well',
                'author': User.objects.get_or_create(username='yooz0r')[0],
                'question': ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='where_to_start', is_bug_style=False)[0],
                'project': Project.create_dummy()
                }
        data.update(kwargs)
        ret = Answer(**data)
        ret.save()
        return ret

class BugTracker(OpenHatchModel):
    # The purpose of this BugTracker model is to permit Bug objects to
    # find and instantiate their bug tracker, whatever type of bug tracker
    # it is.
    #
    # For now, it can only represent static classes, like the various Bugzilla
    # bug trackers.
    #
    # It is a Model so that Bug objects can simply use a ForeignKey to point at a
    # BugTracker object.
    #
    # I do realize there is some duplication between this and the various bug tracker
    # classes in customs. This model should probably be renamed.
    #
    # We could maybe use the Content Types framework in Django instead of writing
    # our own wrapper: http://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
    # See the (very exciting) "Generic relations" section of that page.
    #
    # However, right now, some of our bug tracker classes are not models at all, so
    # we can't access them through the Django content types framework. Once we convert
    # those classes to be model instances, then we can ditch this BugTracker class.
    #
    # EDIT: The Content Types framework is used for all trackers (including hard-coded
    # special cases) handled by the asynchronous bug importer. Once all existing bug
    # importers have been migrated over, this BugTracker class can be removed.

    # If it is a hard-coded class, use these
    module_name = models.CharField(max_length=500, blank=True)
    class_name = models.CharField(max_length=500, blank=True)

    # If it is a bug tracker that we create from the database, use these
    bug_tracker_model_module = models.CharField(max_length=500, blank=True)
    bug_tracker_model_class_name = models.CharField(max_length=500, blank=True)
    bug_tracker_model_pk = models.IntegerField(default=0)

    @staticmethod
    def _instance2module_and_class(instance):
        module_name = instance.__module__
        try:
            class_name = instance.__name__
        except AttributeError:
            class_name = instance.__class__.__name__
        return module_name, class_name

    @staticmethod
    def get_or_create_from_bug_tracker_instance(bug_tracker_instance):
        # First, make sure that the bug tracker is actually capable of refreshing this bug,
        # if we asked it.
        assert hasattr(bug_tracker_instance.__class__, 'refresh_one_bug')

        # Okay, so it provides the necessary method to be something worth serializing.
        # Next question: Is it autogenerated from the database, or is it a hard-coded class
        # that lives in the database?
        if hasattr(bug_tracker_instance, 'provide_hints_for_how_to_recreate_self'):
            # Okay, so it's autogenerated.
            hints = bug_tracker_instance.provide_hints_for_how_to_recreate_self()
            (bug_tracker_model_module,
             bug_tracker_model_class_name) = BugTracker._instance2module_and_class(hints['bug_tracker_class'])
            bug_tracker_model_pk = hints['corresponding_pk']

            obj, was_created = BugTracker.objects.get_or_create(
                bug_tracker_model_module=bug_tracker_model_module,
                bug_tracker_model_class_name=bug_tracker_model_class_name,
                bug_tracker_model_pk=bug_tracker_model_pk)
            return obj

        # If we get this far, the instance does not provide a provide_hints_for_how_to_recreate_self
        # method, so we assume that it's an importable class that lives in the database.
        module_name, class_name = BugTracker._instance2module_and_class(bug_tracker_instance)
        obj, was_created = BugTracker.objects.get_or_create(module_name=module_name,
                                                            class_name=class_name)
        return obj

    def make_instance(self):
        if self.bug_tracker_model_class_name:
            # Then try to reconstitute the instance through the class
            module = importlib.import_module(self.bug_tracker_model_module)
            cls = getattr(module, self.bug_tracker_model_class_name)
            return cls.all_trackers.get(pk=self.bug_tracker_model_pk).create_class_that_can_actually_crawl_bugs()

        # Otherwise, it's a raw, hard-coded class that we can import.
        module = importlib.import_module(self.module_name)
        cls = getattr(module, self.class_name)
        return cls()

class OpenBugsManager(models.Manager):
    def get_query_set(self):
        return super(OpenBugsManager, self).get_query_set().filter(
                looks_closed=False)

class Bug(OpenHatchModel):
    project = models.ForeignKey(Project)
    title = models.CharField(max_length=500)
    description = models.TextField()
    status = models.CharField(max_length=200)
    importance = models.CharField(max_length=200)
    people_involved = models.IntegerField(null=True)
    date_reported = models.DateTimeField()
    last_touched = models.DateTimeField()
    last_polled = models.DateTimeField(default=datetime.datetime(1970, 1, 1))
    submitter_username = models.CharField(max_length=200)
    submitter_realname = models.CharField(max_length=200, null=True)
    canonical_bug_link = models.URLField(max_length=200, unique=True,
                                         blank=False, null=False)
    good_for_newcomers = models.BooleanField(default=False)
    looks_closed = models.BooleanField(default=False)
    bize_size_tag_name = models.CharField(max_length=50) 
    concerns_just_documentation = models.BooleanField(default=False)
    as_appears_in_distribution = models.CharField(max_length=200, default='')

    tracker_type = models.ForeignKey(ContentType, null=True)
    tracker_id = models.PositiveIntegerField(null=True)
    tracker = generic.GenericForeignKey('tracker_type', 'tracker_id')

    bug_tracker = models.ForeignKey(BugTracker, null=True)

    all_bugs = models.Manager()
    open_ones = OpenBugsManager()

    def data_is_more_fresh_than_one_day(self):
        age = datetime.datetime.now() - self.last_polled
        seems_really_fresh = age < datetime.timedelta(hours=20)
        return seems_really_fresh

    def __unicode__(self):
        return "title='%s' project='%s' project__language='%s' description='%s...'" % (self.title, self.project.name, self.project.language, self.description[:50])

    def set_bug_tracker_class_from_instance(self, instance):
        self.bug_tracker = BugTracker.get_or_create_from_bug_tracker_instance(instance)

    @staticmethod
    def create_dummy(**kwargs):
        now = datetime.datetime.utcnow()
        n = str(Bug.all_bugs.count())
        # FIXME (?) Project.objects.all()[0] call below makes an out-of-bounds error in testing...
        data = dict(title=n, project=Project.objects.all()[0], 
                date_reported=now,
                last_touched=now,
                last_polled=now,
                canonical_bug_link="http://asdf.com/" + uuid.uuid4().hex,
                submitter_username='dude',
                description='')
        data.update(kwargs)
        ret = Bug(**data)
        ret.save()
        return ret

    @staticmethod
    def create_dummy_with_project(**kwargs):
        kwargs['project'] = Project.create_dummy()
        return Bug.create_dummy(**kwargs)

class BugAlert(OpenHatchModel):
    user = models.ForeignKey(User, null=True)
    query_string = models.CharField(max_length=255)
    how_many_bugs_at_time_of_request = models.IntegerField()
    email = models.EmailField(max_length=255)

class WannaHelperNote(OpenHatchModel):
    class Meta:
        unique_together = [('project', 'person')]
    person = models.ForeignKey('profile.Person')
    project = models.ForeignKey(Project)

    @staticmethod
    def add_person_project(person, project):
        note, _ = WannaHelperNote.objects.get_or_create(
            person=person, project=project)
        return note

    @staticmethod
    def remove_person_project(person, project):
        try:
            note = WannaHelperNote.objects.get(person=person, project=project)
            note.delete()
        except WannaHelperNote.DoesNotExist:
            pass

    @property
    def template_for_feed(self):
        return 'base/wannahelp-in-feed.html'

    def get_title_for_atom(self):
        return "%s is willing to help %s" % (
                self.person.get_full_name_and_username(), self.project.display_name)

    def get_description_for_atom(self):
        return self.get_title_for_atom()

    def get_absolute_url(self):
        return urljoin(reverse('mysite.project.views.project', args=[self.project.name]), "#person_summary_%d" % self.person.pk)

class HitCountCache(OpenHatchModel):
    hashed_query = models.CharField(max_length=40, primary_key=True) # stores a sha1 
    hit_count = models.IntegerField()

    @staticmethod
    def clear_cache(*args, **kwargs):
        # Ignore arguments passed here by Django signals.
        HitCountCache.objects.all().delete()

def post_bug_save_increment_bug_model_timestamp(sender, raw, instance, created, **kwargs):
    if raw:
        return # this is coming in from loaddata. You must know what you are doing.

    if created:
        return # whatever, who cares
    if instance.looks_closed:
        # bump it
        import mysite.base.models
        mysite.base.models.Timestamp.update_timestamp_for_string(str(sender))
        # and clear the search cache
        import mysite.search.tasks
        mysite.search.tasks.clear_search_cache.delay()

def post_bug_delete_increment_bug_model_timestamp(sender, instance, **kwargs):
    # always bump it
    import mysite.base.models
    mysite.base.models.Timestamp.update_timestamp_for_string(str(sender))

# Clear the cache whenever Bugs are added or removed.
models.signals.post_save.connect(HitCountCache.clear_cache, Bug)
models.signals.post_delete.connect(HitCountCache.clear_cache, Bug)

# Clear all people's recommended bug cache when a bug is deleted
# (or when it has been modified to say it looks_closed)
models.signals.post_save.connect(
    post_bug_save_increment_bug_model_timestamp,
    Bug)

models.signals.post_delete.connect(
    post_bug_delete_increment_bug_model_timestamp,
    Bug)

# Re-index the person when he says he likes a new project
def update_the_person_index_from_project(sender, instance, **kwargs):
    import mysite.profile.tasks
    for person in instance.people_who_wanna_help.all():
        task = mysite.profile.tasks.ReindexPerson()
        task.delay(person.id)

models.signals.post_save.connect(update_the_person_index_from_project, sender=Project)

# vim: set ai ts=4 nu:
