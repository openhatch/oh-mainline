from django.db import models
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings
import datetime
import StringIO
import Image
import uuid
import urllib
from django.db.models import Q
import mysite.customs
import mysite.base.unicode_sanity
from django.core.urlresolvers import reverse
import voting
import hashlib
import celery.decorators

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

    name = models.CharField(max_length=200, unique=True)
    language = models.CharField(max_length=200)

    def invalidate_all_icons(self):
        self.icon_raw = None
        self.icon_url = u''
        self.icon_for_profile = None
        self.icon_smaller_for_badge = None
        self.icon_for_search_result = None
        pass

    # FIXME: Remove this field and update fixtures.
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
            return None

        # if you want to scale, use get_image_data_scaled(icon_data)
        self.icon_raw.save('', ContentFile(icon_data))

        # Since we are saving an icon, also update our scaled-down version of
        # that icon for the badge.
        self.update_scaled_icons_from_self_icon()

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
        from mysite.profile.models import PortfolioEntry
        # What portfolio entries point to this project?
        pf_entries = PortfolioEntry.objects.filter(
                Q(project=self), Q(is_deleted=False),
                Q(is_published=True) )
        # List the owners of those portfolio entries.
        return [pf_entry.person for pf_entry in pf_entries]

    def update_cached_contributor_count_and_save(self):
        contributors = self.get_contributors()
        self.cached_contributor_count = len(contributors)
        self.save()

    def get_n_other_contributors_than(self, n, person):
        # FIXME: Use the method above.
        from mysite.profile.models import PortfolioEntry
        pf_entries = list(PortfolioEntry.objects.filter(Q(project=self),
                ~Q(person=person),
                Q(is_deleted=False),
                Q(is_published=True),
                ))
        import random
        random.shuffle(pf_entries)
        pf_entries = pf_entries[:n] # Slicing the pf entries has the same effect as
                                    # slicing the list of people.
        other_contributors = [p.person for p in pf_entries]
        return other_contributors

    def __unicode__(self):
        return "name='%s' language='%s'" % (self.name, self.language)
    
    def get_url(self):
        return reverse(mysite.project.views.project,
                kwargs={'project__name': mysite.base.unicode_sanity.quote(self.name)}) 

    @mysite.base.decorators.cached_property
    def get_mentors_search_url(self):
        query_string = mysite.base.unicode_sanity.urlencode({u'q': u'can_mentor:"%s"' %
                                         self.language})
        return reverse(mysite.profile.views.people) + '?' + query_string

    def get_open_bugs(self):
        return Bug.open_ones.filter(project=self)

    def get_open_bugs_randomly_ordered(self):
        return self.get_open_bugs().order_by('?')
    
def populate_icon_on_project_creation(instance, created, *args, **kwargs):
    if created and not instance.icon_raw:
        instance.populate_icon_from_ohloh()

def grab_project_language_from_ohloh(instance, created, *args,
                                     **kwargs):
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

    @property
    def template_for_feed(self):
        return 'base/answer-in-feed.html'

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
    title = models.CharField(max_length=200)
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

    all_bugs = models.Manager()
    open_ones = OpenBugsManager()

    def data_is_more_fresh_than_one_day(self):
        age = datetime.datetime.now() - self.last_polled
        if age < datetime.timedelta(days=1):
            return True
        return False

    def __unicode__(self):
        return "title='%s' project='%s' project__language='%s' description='%s...'" % (self.title, self.project.name, self.project.language, self.description[:50])

    @staticmethod
    def create_dummy(**kwargs):
        now = datetime.datetime.utcnow()
        n = str(Bug.all_bugs.count())
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

class Epoch(OpenHatchModel):
    zero_hour = datetime.datetime.fromtimestamp(0).timetuple()
    # The modified_date column in this can be passed to
    # functions that cache based on their arguments. Careful
    # updating of this table can create convenient, implicit
    # cache expiry.
    class_name = models.CharField(null=False,
                                  blank=False,
                                  unique=True,
                                  max_length=255)

    @staticmethod
    def get_for_model(class_object):
        class_name = unicode(str(class_object))
        matches = Epoch.objects.filter(class_name=class_name)
        if matches:
            match = matches[0]
            return match.modified_date.timetuple()
        return Epoch.zero_hour

    @staticmethod
    def bump_for_model(class_object):
        class_name = unicode(str(class_object))
        epoch, _ = Epoch.objects.get_or_create(
            class_name=class_name)
        epoch.modified_date = datetime.datetime.utcnow()
        epoch.save() # definitely!
        return epoch

class NoteThatSomeoneWantsToHelpAProject(OpenHatchModel):
    class Meta:
        unique_together = [('project', 'person')]
    person = models.ForeignKey('profile.Person')
    project = models.ForeignKey(Project)

    @staticmethod
    def add_person_project(person, project):
        note, _ = NoteThatSomeoneWantsToHelpAProject.objects.get_or_create(
            person=person, project=project)
        return note

    @staticmethod
    def remove_person_project(person, project):
        try:
            note = NoteThatSomeoneWantsToHelpAProject.objects.get(person=person, project=project)
            note.delete()
        except NoteThatSomeoneWantsToHelpAProject.DoesNotExist:
            pass

    @property
    def template_for_feed(self):
        return 'base/wannahelp-in-feed.html'

class HitCountCache(OpenHatchModel):
    hashed_query = models.CharField(max_length=40, primary_key=True) # stores a sha1 
    hit_count = models.IntegerField()

    @staticmethod
    def clear_cache(*args, **kwargs):
        # Ignore arguments passed here by Django signals.
        HitCountCache.objects.all().delete()

def post_bug_save_increment_bug_model_epoch(sender, instance, created, **kwargs):
    if created:
        return # whatever, who cares
    if instance.looks_closed:
        # bump it
        mysite.search.models.Epoch.bump_for_model(sender)

def post_bug_delete_increment_bug_model_epoch(sender, instance, **kwargs):
    # always bump it
    mysite.search.models.Epoch.bump_for_model(sender)

# Clear the cache whenever Bugs are added or removed.
models.signals.post_save.connect(HitCountCache.clear_cache, Bug)
models.signals.post_delete.connect(HitCountCache.clear_cache, Bug)

# Clear all people's recommended bug cache when a bug is deleted
# (or when it has been modified to say it looks_closed)
models.signals.post_save.connect(
    post_bug_save_increment_bug_model_epoch,
    Bug)

models.signals.post_delete.connect(
    post_bug_delete_increment_bug_model_epoch,
    Bug)

# Re-index the person when he says he likes a new project
def update_the_person_index_from_project(sender, instance, **kwargs):
    import mysite.profile.tasks
    for person in instance.people_who_wanna_help.all():
        task = mysite.profile.tasks.ReindexPerson()
        task.delay(person.id)

models.signals.post_save.connect(update_the_person_index_from_project, sender=Project)

# vim: set ai ts=4 nu:
