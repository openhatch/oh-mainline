from django.db import models
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from mysite.customs import ohloh
from django.conf import settings
import datetime
import StringIO
import Image
import uuid

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

def populate_icon_on_project_creation(instance, created, *args, **kwargs):
    if created:
        instance.populate_icon_from_ohloh()
        
models.signals.post_save.connect(populate_icon_on_project_creation, Project)

# Create your models here.
class Project(models.Model):

    @staticmethod
    def get_icon_path(instance, filename):
        # MEDIA_ROOT is prefixed automatically.
        return 'images/icons/projects/%s.png' % uuid.uuid4().hex

    name = models.CharField(max_length=200, unique = True)
    language = models.CharField(max_length=200)

    # FIXME: Replace this with 'icon'
    icon_url = models.URLField(max_length=200)

    # In case we need it 
    # dont_use_ohloh_icon = models.BooleanField(default=False)
    icon = models.ImageField(
            upload_to=lambda a,b: Project.get_icon_path(a, b),
            null=True,
            default=None)

    date_icon_was_fetched_from_ohloh = models.DateTimeField(null=True, default=None)

    icon_smaller_for_badge = models.ImageField(
        upload_to=lambda a,b: Project.get_icon_path(a,b),
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
        self.update_badge_icon_from_self_icon()

    def get_url_of_icon_or_generic(self):
        if self.icon:
            return settings.MEDIA_URL + self.icon.url
        else:
            return settings.MEDIA_URL + 'no-project-icon.png'

    def get_url_of_badge_size_icon_or_generic(self):
        if self.icon_smaller_for_badge:
            return settings.MEDIA_URL + self.icon_smaller_for_badge.url
        else:
            return settings.MEDIA_URL + 'no-project-icon-w=40.png'

    def update_badge_icon_from_self_icon(self):
        '''This method should be called when you update the Project.icon attribute.
        Side-effect: Saves a scaled-down version of that icon in the
        Project.icon_smaller_for_badge field.'''
        # First of all, do nothing if self.icon is a false value.
        if not self.icon:
            return

        # Okay, now we must have some icon. Scale it down to badge size, which
        # happens to be width=40
        scaled_down = get_image_data_scaled(self.icon.file.read(), 40)
        self.icon_smaller_for_badge.save('', ContentFile(scaled_down))

    def __unicode__(self):
        return "<Project name='%s' language='%s'>" % (self.name, self.language)

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

    def __unicode__(self):
        return "<Bug title='%s' project='%s' project__language='%s' description='%s...'>" % (self.title, self.project.name, self.project.language, self.description[:50])

# vim: set ai ts=4 nu:
