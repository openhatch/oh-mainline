# vim: set ai ts=4 sw=4 et:

from django.db import models
from mysite.search.models import Project, Bug

# Create your models here.
class Person(models.Model):
    # {{{
    name = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    password_hash_md5 = models.CharField(max_length=200) #FIXME: Get specific length of hash
    time_record_created = models.DateTimeField()

    def save(self):
        if not self.id:
            self.time_record_created = date_reported.datetime.today()
        super(Person, self).save()
    # }}}

class PersonToProjectRelationship(models.Model):
    """ Many-to-one relation between projects and people """
    # {{{
    person = models.ForeignKey(Person)
    project = models.ForeignKey(Project)
    person_role = models.CharField(max_length=200)
    tags = models.TextField() # A list of tags, delimited with spaces.
    time_record_was_created = models.DateTimeField()
    url = models.URLField(max_length=200)
    description = models.TextField()
    time_start = models.DateTimeField()
    time_finish = models.DateTimeField()
    man_months = models.PositiveIntegerField()
    primary_language = models.CharField(max_length=200)

    source = model.CharField(max_length=100)

    def save(self):
        if not self.id:
            self.time_record_was_created = datetime.date.today()

    def from_ohloh_contrib_info(self, ohloh_contrib_info):
        if not self.person:
            self.person = Person.objects.get_or_create(
                    username=ohloh_contrib_info['username'])
        else:
            pass # Don't overwrite.

        self.project = Project.objects.get_or_create(
                name=ohloh_contrib_info['project'])
        # FIXME: Automatically populate project url here.
        self.man_months = ohloh_contrib_info['man_months']
        self.primary_language = ohloh_contrib_info['primary_language']
        self.source = "Ohloh"
        self.time_gathered_from_source = datetime.date.today()
    # }}}

class Commit(models.Model):
    # {{{
    person_to_project_relationship = models.ForeignKey(
            PersonToProjectRelationship)
    person = models.ForeignKey(Person) # Redundant
    project = models.ForeignKey(Project) # Redundant
    time = models.DateTimeField()
    description = models.TextField()
    # }}}

class Tag(models.Model):
    # {{{
    text = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    # }}}

class TagTypes(models.Model):
    # {{{
    prefix = models.CharField(max_length=20)
    # }}}
