from django.db import models
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from mysite.customs import ohloh
import datetime

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
    def get_icon_path(instance, filename):
        # MEDIA_ROOT is prefixed automatically.
        return 'images/icons/projects/%s' % uuid.uuid4().hex

    name = models.CharField(max_length=200, unique = True)
    language = models.CharField(max_length=200)

    # FIXME: Replace this with 'icon'
    icon_url = models.URLField(max_length=200)

    # In case we need it 
    # dont_use_ohloh_icon = models.BooleanField(default=False)
    icon = models.ImageField(
            upload_to=get_icon_path,
            null=True,
            default=None)

    date_icon_was_fetched_from_ohloh = models.DateTimeField(null=True, default=None)

    def populate_icon_from_ohloh(self):

        
        oh = ohloh.get_ohloh()
        try:
            icon_data = oh.get_icon_for_project(self.name)
            self.date_icon_was_fetched_from_ohloh = datetime.datetime.now()
        except ValueError:
            self.date_icon_was_fetched_from_ohloh = datetime.datetime.now()
            return None

        # if you want to scale, use get_image_data_scaled(icon_data)
        self.icon.save('', ContentFile(icon_data))

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
