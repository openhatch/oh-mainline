from django.db import models

class BugSet(models.Model):
    name = models.CharField(max_length=200)

class AnnotatedBug(models.Model):
    url = models.URLField(max_length=200, verbose_name='Bug URL')
    bugsets = models.ManyToManyField(BugSet)
