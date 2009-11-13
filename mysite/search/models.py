from django.db import models
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.conf import settings
import datetime
import StringIO
import Image
import uuid
from django.db.models import Q

from mysite.customs import ohloh

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

# Create your models here.
class Project(models.Model):

    @staticmethod
    def generate_random_icon_path(instance, filename):
        # MEDIA_ROOT is prefixed automatically.
        return 'images/icons/projects/%s.png' % uuid.uuid4().hex

    name = models.CharField(max_length=200, unique = True)
    language = models.CharField(max_length=200)

    # FIXME: Replace this with 'icon'
    icon_url = models.URLField(max_length=200)

    # In case we need it 
    # dont_use_ohloh_icon = models.BooleanField(default=False)
    icon = models.ImageField(
            upload_to=lambda a,b: Project.generate_random_icon_path(a, b),
            null=True,
            default=None)

    date_icon_was_fetched_from_ohloh = models.DateTimeField(null=True, default=None)

    icon_smaller_for_badge = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    icon_for_search_result = models.ImageField(
        upload_to=lambda a,b: Project.generate_random_icon_path(a,b),
        null=True,
        default=None)

    def populate_icon_from_ohloh(self):

        oh = ohloh.get_ohloh()
        try:
            icon_data = oh.get_icon_for_project(self.name)
            self.date_icon_was_fetched_from_ohloh = datetime.datetime.utcnow()
        except ValueError:
            self.date_icon_was_fetched_from_ohloh = datetime.datetime.utcnow()
            return None

        # if you want to scale, use get_image_data_scaled(icon_data)
        self.icon.save('', ContentFile(icon_data))

        # Since we are saving an icon, also update our scaled-down version of
        # that icon for the badge.
        self.update_scaled_icons_from_self_icon()

    def get_url_of_icon_or_generic(self):
        if self.icon:
            return self.icon.url
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
        '''This method should be called when you update the Project.icon attribute.
        Side-effect: Saves a scaled-down version of that icon in the
        Project.icon_smaller_for_badge field.'''
        # First of all, do nothing if self.icon is a false value.
        if not self.icon:
            return
        # Okay, now we must have some normal-sized icon. 

        normal_sized_icon_data = self.icon.file.read()

        # Scale it down to badge size, which
        # happens to be width=40
        badge_icon_data = get_image_data_scaled(normal_sized_icon_data, 40)
        self.icon_smaller_for_badge.save('', ContentFile(badge_icon_data))

        # Scale normal-sized icon down to a size that fits in the search results--20px by 20px
        search_result_icon_data = get_image_data_scaled(normal_sized_icon_data, 20)
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
        return "<Project name='%s' language='%s'>" % (self.name, self.language)

def populate_icon_on_project_creation(instance, created, *args, **kwargs):
    if created and not instance.icon:
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
    people_involved = models.IntegerField()
    date_reported = models.DateTimeField()
    last_touched = models.DateTimeField()
    last_polled = models.DateTimeField()
    submitter_username = models.CharField(max_length=200)
    submitter_realname = models.CharField(max_length=200)
    canonical_bug_link = models.URLField(max_length=200)
    good_for_newcomers = models.BooleanField(default=False)
    looks_closed = models.BooleanField(default=False)
    bize_size_tag_name = models.CharField(max_length=50) 

    all_bugs = models.Manager()
    open_ones = OpenBugsManager()

    def __unicode__(self):
        return "<Bug title='%s' project='%s' project__language='%s' description='%s...'>" % (self.title, self.project.name, self.project.language, self.description[:50])
    
# vim: set ai ts=4 nu:
