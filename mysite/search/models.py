from django.db import models

# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=200, unique = True)
    language = models.CharField(max_length=200)
    icon_url = models.URLField(max_length=200)

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
