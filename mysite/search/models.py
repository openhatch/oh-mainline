from django.db import models

# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=200)
    language = models.CharField(max_length=200)

class Bug(models.Model):
    project = models.ForeignKey(Project)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=200)

