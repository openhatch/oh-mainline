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

from django.db import models
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
import datetime
import StringIO
import logging
import uuid
from urlparse import urljoin
import random
import mysite.customs
import mysite.base.unicode_sanity
from django.core.urlresolvers import reverse
import voting
import mysite.customs.ohloh
import mysite.base.depends
import mysite.base.decorators
import django.contrib.contenttypes.models


class OpenHatchModel(models.Model):
    created_date = models.DateTimeField(null=True, auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

def get_image_data_scaled(image_data, width):
    ### NOTE: We refuse to scale images if we do not
    ### have the Python Imaging Library.
    if not mysite.base.depends.Image:
        logging.info("NOTE: We cannot resize this image, so we are going to pass it through. See ADVANCED_INSTALLATION.mkd for information on PIL.")
        return image_data

    # scale it
    image_fd = StringIO.StringIO(image_data)
    im = mysite.base.depends.Image.open(image_fd)
    image_fd.seek(0)

    w, h = get_image_dimensions(image_fd)

    new_w = int(width)
    new_h = int((h * 1.0 / w) * width)

    smaller = im.resize((new_w, new_h),
                        mysite.base.depends.Image.ANTIALIAS)

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

    def get_corresponding_bug_trackers(self):
        '''This method returns all the bug trackers that should appear in the
        project's +projedit page.

        This is probably pretty inefficient, but it's not called very often.'''
        # Grab all the bug trackers that bugs refer to
        all_corresponding_bug_trackers = set([b.tracker for b in self.bug_set.all()
                                          if b.tracker])
        # Grab all the bug trackers that refer to the project
        for tracker in mysite.customs.models.TrackerModel.objects.filter(created_for_project=self).select_subclasses():
            all_corresponding_bug_trackers.add(tracker)

        return all_corresponding_bug_trackers

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
    def potential_mentor_count(self):
        '''Return a number of potential mentors, counted as the
        number of people who can mentor in the project by name unioned
        with those who can mentor in the project's language.'''
        all_mentor_person_ids = set()
        import mysite.profile.view_helpers
        for way_a_mentor_can_help in (self.name, self.language):
            tq = mysite.profile.view_helpers.TagQuery('can_mentor',
                                                     way_a_mentor_can_help)
            all_mentor_person_ids.update(tq.people.values_list('id', flat=True))
        return len(all_mentor_person_ids)

    @staticmethod
    def create_dummy(**kwargs):
        data = dict(name=uuid.uuid4().hex,
                icon_raw='/static/no-project-icon.png',
                    language='C')
        data.update(kwargs)
        ret = Project(**data)
        ret.save()
        return ret

    @staticmethod
    def create_dummy_no_icon(**kwargs):
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

    def get_contributor_count(self):
        """Return the number of Person objects who are contributors to
        this Project."""
        return self.get_contributors().count()

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
        import mysite.profile.view_helpers
        mentors_available = bool(mysite.profile.view_helpers.TagQuery(
                'can_mentor', self.name).people)
        if mentors_available or self.language:
            query_var = self.name
            if not mentors_available:
                query_var = self.language
            query_string = mysite.base.unicode_sanity.urlencode({u'q': u'can_mentor:"%s"' %
                                             query_var})
            return reverse(mysite.profile.views.people) + '?' + query_string
        else:
            return ""

    def get_bug_count(self):
        if hasattr(self, 'bug_count'):
            return self.bug_count
        return Bug.all_bugs.filter(project=self).count()

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

class Buildhelper(OpenHatchModel):
    '''Model where all the steps in the buildhelper live'''
    project = models.ForeignKey(Project)
    default_frustration_handler = models.URLField(max_length=200, default='')

    def addStep(self, name, time, is_prerequisite = False, description='', command='', hint='', frustration_handler = None):
        '''creates and saves a BuildhelperStep object'''
        if frustration_handler is None:
            import pdb; pdb.set_trace()
            frustration_handler = self.default_frustration_handler
        s = BuildhelperStep(buildhelper = self,is_prerequisite = is_prerequisite, name = name, description = description, command = command, time = time, hint= hint, frustration_handler = frustration_handler)
        s.save()

    def __unicode__(self):
        return self.project.display_name +"'s Buildhelper"


class BuildhelperStep(OpenHatchModel):
    '''A single step in the buildhelper'''
    buildhelper = models.ForeignKey(Buildhelper)
    is_prerequisite = models.BooleanField(default=False)
    is_checked = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    description = models.TextField(default='',blank=True)
    command = models.TextField(default='',blank=True)
    time = models.IntegerField(default=0)
    hint = models.URLField(max_length=200, default='http://cuteoverload.com',blank=True)
    frustration_handler = models.URLField(max_length=200, blank=True)
    def __unicode__(self):
        return "Buildhelper step for project " + self.buildhelper.project.display_name + ": " + self.name

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

    #TODO: This is bull****; what the heck is this template stuff doing in the models? Need refactoring!
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
    concerns_just_documentation = models.BooleanField(default=False)
    as_appears_in_distribution = models.CharField(max_length=200, default='')

    tracker_type = models.ForeignKey(ContentType, null=True)
    tracker_id = models.PositiveIntegerField(null=False)
    tracker = generic.GenericForeignKey('tracker_type', 'tracker_id')

    all_bugs = models.Manager()
    open_ones = OpenBugsManager()

    def data_is_more_fresh_than_one_day(self):
        age = datetime.datetime.now() - self.last_polled
        seems_really_fresh = age < datetime.timedelta(hours=20)
        return seems_really_fresh

    def __unicode__(self):
        return "title='%s' project='%s' project__language='%s' description='%s...'" % (self.title, self.project.name, self.project.language, self.description[:50])

    @staticmethod
    def create_dummy(**kwargs):
        # If there is no TracTrackerModel, we are going to need one. So, we
        # create one.
        if not mysite.customs.models.TracTrackerModel.objects.all():
            ttm = mysite.customs.models.TracTrackerModel.objects.create()
        else:
            ttm = mysite.customs.models.TracTrackerModel.objects.all()[0]

        # And if there is no corresponding ContentType, well, we are going
        # to need it.
        content_type, _ = (
            django.contrib.contenttypes.models.ContentType.objects.get_or_create(
                app_label="search", model="tractrackermodel"))

        now = datetime.datetime.utcnow()
        n = str(Bug.all_bugs.count())
        # FIXME (?) Project.objects.all()[0] call below makes an out-of-bounds error in testing...
        data = dict(
            title=n, project=Project.objects.all()[0],
            tracker_id=ttm.id,
            tracker_type=content_type,
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
    contacted_by = models.ForeignKey(User, related_name="contacted_by_user", blank=True, null=True)
    contacted_on = models.DateField(blank=True, null=True)

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


def post_bug_save_delete_increment_hit_count_cache_timestamp(sender, instance, **kwargs):
    # always bump it
    import mysite.base.models
    mysite.base.models.Timestamp.update_timestamp_for_string('hit_count_cache_timestamp'),

# Clear the hit count cache whenever Bugs are added or removed. This is
# simply done by bumping the Timestamp used to generate the cache keys.
# The hit count cache is used in get_or_create_cached_hit_count() in
# mysite.search.view_helpers.Query.
# Clear all people's recommended bug cache when a bug is deleted
# (or when it has been modified to say it looks_closed)
models.signals.post_save.connect(
    post_bug_save_delete_increment_hit_count_cache_timestamp,
    Bug)
models.signals.pre_delete.connect(
    post_bug_save_delete_increment_hit_count_cache_timestamp,
    Bug)

# vim: set ai ts=4 nu:
