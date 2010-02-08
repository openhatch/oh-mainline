from django.db import models
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.conf import settings
import datetime
import StringIO
import Image
import uuid
import urllib
from django.db.models import Q
import mysite.customs 
from django.core.urlresolvers import reverse

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

class Project(models.Model):

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

    def potential_mentors(self):
        '''Return the union of the people who can mentor in this project,
        or who can mentor in the project's language.'''
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
                icon_raw='/static/no-project-icon.png')
        data.update(kwargs)
        ret = Project(**data)
        ret.save()
        return ret

    name = models.CharField(max_length=200, unique=True)
    language = models.CharField(max_length=200)

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

    def update_cached_contributor_count(self):
        contributors = self.get_contributors()
        self.cached_contributor_count = len(contributors)

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
        query_string = urllib.urlencode({'q': 'project:' +
                                         self.name_with_quotes_if_necessary()})
        return reverse(mysite.profile.views.people) + '?' + query_string

    def get_open_bugs(self):
        return Bug.open_ones.filter(project=self)

    def get_open_bugs_randomly_ordered(self):
        return self.get_open_bugs().order_by('?')
    
def populate_icon_on_project_creation(instance, created, *args, **kwargs):
    if created and not instance.icon_raw:
        instance.populate_icon_from_ohloh()
        
models.signals.post_save.connect(populate_icon_on_project_creation, Project)

# An easy way to find 

class OpenBugsManager(models.Manager):
    def get_query_set(self):
        return super(OpenBugsManager, self).get_query_set().filter(
                looks_closed=False)

class Bug(models.Model):
    project = models.ForeignKey(Project)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=200)
    importance = models.CharField(max_length=200)
    people_involved = models.IntegerField(null=True)
    date_reported = models.DateTimeField()
    last_touched = models.DateTimeField()
    last_polled = models.DateTimeField()
    submitter_username = models.CharField(max_length=200)
    submitter_realname = models.CharField(max_length=200, null=True)
    canonical_bug_link = models.URLField(max_length=200)
    good_for_newcomers = models.BooleanField(default=False)
    looks_closed = models.BooleanField(default=False)
    bize_size_tag_name = models.CharField(max_length=50) 
    concerns_just_documentation = models.BooleanField(default=False)

    all_bugs = models.Manager()
    open_ones = OpenBugsManager()

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
                canonical_bug_link="http://asdf.com",
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

class HitCountCache(models.Model):
    hashed_query = models.CharField(max_length=40, primary_key=True) # stores a sha1 
    hit_count = models.IntegerField()

    @staticmethod
    def clear_cache(*args, **kwargs):
        # Ignore arguments passed here by Django signals.
        HitCountCache.objects.all().delete()

# Clear the cache whenever Bugs are added or removed.
models.signals.post_save.connect(HitCountCache.clear_cache, Bug)
models.signals.post_delete.connect(HitCountCache.clear_cache, Bug)

# vim: set ai ts=4 nu:
