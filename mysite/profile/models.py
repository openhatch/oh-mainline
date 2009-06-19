# vim: set ai ts=4 sw=4 et:

from django.db import models
from mysite.search.models import Project, Bug
import datetime

class Person(models.Model):
    """ A human bean. """
    # {{{
    name = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    password_hash_md5 = models.CharField(
            max_length=200)
    #FIXME: Get specific length of hash
    time_record_was_created = models.DateTimeField(
            default=datetime.datetime.now())
    last_polled = models.DateTimeField(
            blank=True, null=True)
    last_touched = models.DateTimeField()
    poll_on_next_web_view = models.BooleanField(
            default=True)

    def save(self, *args, **kwargs):
        if self.time_record_was_created is None:
            self.time_record_was_created = datetime.datetime.now()
        self.last_touched = datetime.datetime.now()
        super(Person, self).save(*args, **kwargs)

    def fetch_contrib_data_from_ohloh(self):
        # self has to be saved, otherwise person_id becomes null
        self.save()
        import ohloh
        oh = ohloh.get_ohloh()
        ohloh_contrib_info_list = oh.get_contribution_info_by_username(
                self.username)
        for ohloh_contrib_info in ohloh_contrib_info_list:
            p2p_rel = ProjectExp()
            p2p_rel.person = self
            p2p_rel.from_ohloh_contrib_info(ohloh_contrib_info)
            p2p_rel.save()
        self.last_polled = datetime.datetime.now()
        self.save()

    # }}}

class ProjectExp(models.Model):
    "Many-to-one relation between projects and people."
    # {{{
    person = models.ForeignKey(Person)
    project = models.ForeignKey(Project)
    person_role = models.CharField(max_length=200)
    tags = models.TextField() # A list of tags, delimited with spaces.
    time_record_was_created = models.DateTimeField()
    url = models.URLField(max_length=200)
    description = models.TextField()
    man_months = models.PositiveIntegerField()
    primary_language = models.CharField(max_length=200)

    source = models.CharField(max_length=100)

    def from_ohloh_contrib_info(self, ohloh_contrib_info):
        if not self.person:
            self.person = Person.objects.get_or_create(
                    username=ohloh_contrib_info['username'])
        else:
            pass # Don't overwrite.

        self.project, bool_created = Project.objects.get_or_create(
                name=ohloh_contrib_info['project'])
        # FIXME: Automatically populate project url here.
        self.man_months = ohloh_contrib_info['man_months']
        self.primary_language = ohloh_contrib_info['primary_language']
        self.source = "Ohloh"
        self.time_gathered_from_source = datetime.date.today()

    def save(self, *args, **kwargs):
        if self.time_record_was_created is None:
            self.time_record_was_created = datetime.datetime.now()
        super(ProjectExp, self).save(*args, **kwargs)



    # }}}

class Tag(models.Model):
    # {{{
    text = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    # }}}

class TagType(models.Model):
    # {{{
    name = models.CharField(max_length=100)
    prefix = models.CharField(max_length=20)
    # }}}

class Link_ProjectExp_Tag(models.Model):
    "Many-to-many relation between p2prels and tags."
    # {{{
    tag = models.ForeignKey(Tag)
    project_exp = models.ForeignKey(ProjectExp)
    time_record_was_created = models.DateTimeField(
            default=datetime.datetime.now())
    source = models.CharField(max_length=200)
    # }}}
