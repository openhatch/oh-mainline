from django.db import models
from mysite.search.models import Project, Bug

# Create your models here.
class Person(models.Model):
	name = models.CharField(max_length=200)
	username = models.CharField(max_length=200)
	password_hash_md5 = models.CharField(max_length=200) #FIXME: Get specific length of hash
	time_joined = models.DateTimeField()

class PersonToProjectRelationship(models.Model):
	"""
	Many-to-one relation between projects and people
	"""
	person = models.ForeignKey(Person)
	project = models.ForeignKey(Project)
	role = models.CharField(max_length=200)
	description = models.TextField()
	datetime_start = models.DateTimeField()
	datetime_finish = models.DateTimeField()

class Commit(models.Model):
	person_to_project_relationship = models.ForeignKey(PersonExperienceWithProject)
	person = models.ForeignKey(Person) # Redundant
	project = models.ForeignKey(Project) # Redundant
	time = models.DateTimeField()
	description = models.TextField()

"""
For reference:
class Project(models.Model):
    name = models.CharField(max_length=200)
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
"""
