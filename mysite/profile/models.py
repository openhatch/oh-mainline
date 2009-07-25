# vim: set ai ts=4 sw=4 et:

from django.db import models
from mysite.search.models import Project, Bug
from django.contrib.auth.models import User
import customs.ohloh as ohloh
import datetime

class Person(models.Model):
    """ A human bean. """
    # {{{
    user = models.ForeignKey(User, unique=True)
    gotten_name_from_ohloh = models.BooleanField(default=False)
    interested_in_working_on = models.CharField(max_length=1024, default='')
    last_polled = models.DateTimeField(default=datetime.datetime(1970, 1, 1))

    def fetch_contrib_data_from_ohloh(self):
        # self has to be saved, otherwise person_id becomes null
        self.save()
        oh = ohloh.get_ohloh()

        ohloh_contrib_info_list = oh.get_contribution_info_by_username(
                self.user.username)
        for ohloh_contrib_info in ohloh_contrib_info_list:
            exp = ProjectExp()
            exp.person = self
            exp = exp.from_ohloh_contrib_info(ohloh_contrib_info)
            exp.save()
        self.save()
        
    def __unicode__(self):
        return "username: %s, name: %s %s" % (self.user.username,
                self.user.first_name, self.user.last_name)
    # }}}

class DataImportAttempt(models.Model):
    # {{{
    SOURCE_CHOICES = (
        ('rs', "Search all repositories for %s."),
        ('ou', "I'm %s on Ohloh; import my data."),
        ('lp', "I'm %s on Launchpad; import my data."),
        )
    completed = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    source = models.CharField(max_length=2,
                              choices=SOURCE_CHOICES)
    person = models.ForeignKey(Person)
    person_wants_data = models.BooleanField(default=False)
    query = models.CharField(max_length=200)

    def get_formatted_source_description(self):
        return self.get_source_display() % self.query

    def give_data_to_person(self):
        """ This DataImportAttempt assigns its person to its ProjectExps. """

        project_exps = ProjectExp.objects.filter(data_import_attempt=self)
        for pe in project_exps:
            if pe.person and pe.person != self.person:
                raise ValueError, ("You tried to give some ProjectExps to "
                + "a person (%s), but those ProjectExps already belonged to somebody else (%s)." % (
                        self.person, pe.person))
            pe.person = self.person
            pe.save()

    def do_what_it_says_on_the_tin(self):
        """Attempt to import data."""
        from profile.tasks import FetchPersonDataFromOhloh
        FetchPersonDataFromOhloh.delay(self.id)

    def __unicode__(self):
        return "Attempt to import data, source = %s, person = <%s>, query = %s" % (self.get_source_display(), self.person, self.query)

    # }}}

"""
Scenario A.
* Dia creates background job.
* User marks Dia "I want it"
* Background job finishes.
* Background job asks, Does anybody want this?
* Background job realizes, "yes, User wants this"
* Background job attaches the projects to the user

Scenario B.
* Dia creates background job.
* Background job finishes.
* Background job asks, Does anybody want this?
* Background job realizes, "Nobody has claimed this yet. I'll just sit tight."
* User marks Dia "I want it"
* The marking method attaches the projects to the user
"""

def reject_when_query_is_only_whitespace(sender, instance, **kwargs):
    if not instance.query.strip():
        raise ValueError, "You tried to save a DataImportAttempt whose query was only whitespace, and we rejected it."

models.signals.pre_save.connect(reject_when_query_is_only_whitespace, sender=DataImportAttempt)

class ProjectExp(models.Model):
    "Many-to-one relation between projects and people."
    # {{{
    person = models.ForeignKey(Person, null=True)
    should_show_this = models.BooleanField(default=False)
    data_import_attempt = models.ForeignKey(DataImportAttempt, null=True)
    project = models.ForeignKey(Project)
    person_role = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(max_length=200, null=True)
    man_months = models.PositiveIntegerField(null=True)
    primary_language = models.CharField(max_length=200, null=True)
    source = models.CharField(max_length=100, null=True)

    # FIXME: Make this a static method or something
    def from_ohloh_contrib_info(self, ohloh_contrib_info):
        # {{{
        self.project, bool_created = Project.objects.get_or_create(
                name=ohloh_contrib_info['project'])
        matches = list(ProjectExp.objects.filter(project=self.project,
                                           person=self.person))
        if matches:
            return matches[0]
        else:
            # FIXME: Automatically populate project url here.
            self.man_months = ohloh_contrib_info['man_months']
            self.primary_language = ohloh_contrib_info['primary_language']
            self.source = "Ohloh"
            self.time_gathered_from_source = datetime.date.today()
            return self
        # }}}
    # FIXME: Make this a static method or something
    def from_launchpad_result(self, project_name, language, person_role):
        # {{{
        self.project, bool_created = Project.objects.get_or_create(
                name=project_name)
        matches = list(ProjectExp.objects.filter(project=self.project,
                                           person=self.person))
        if matches:
            return matches[0]
        else:
            # FIXME: Automatically populate project url here.
            self.primary_language = language
            self.person_role = person_role
            self.source = "Launchpad"
            self.time_gathered_from_source = datetime.date.today()
            return self
        # }}}

    @staticmethod
    def create_from_text(
            username,
            project_name,
            description='',
            url='',
            man_months=None,
            primary_language=''
            ):

        person = Person.objects.get(user__username=username)
        project, created = Project.objects.get_or_create(name=project_name)
        if man_months is not None:
            man_months = int(man_months)

        exp = ProjectExp(
                person=person,
                project=project,
                url=str(url),
                description=str(description),
                man_months=man_months,
                primary_language=primary_language)

        exp.save()
        return exp

    @staticmethod
    def get_from_text(username, project_name):
        return ProjectExp.objects.get(
                person=Person.objects.get(user__username=username),
                project=Project.objects.get(name=project_name),
                )
    get_from_strings = get_from_text

    # }}}

class TagType(models.Model):
    # {{{
    name = models.CharField(max_length=100)
    prefix = models.CharField(max_length=20)
    # }}}

class Tag(models.Model):
    # {{{
    text = models.CharField(max_length=50)
    tag_type = models.ForeignKey(TagType)

    # }}}

class Link_ProjectExp_Tag(models.Model):
    "Many-to-many relation between ProjectExps and Tags."
    # {{{
    tag = models.ForeignKey(Tag)
    favorite = models.BooleanField(default=False)
    project_exp = models.ForeignKey(ProjectExp)
    source = models.CharField(max_length=200)

    class Meta:
        unique_together = [ ('tag', 'project_exp', 'source'),
                            ]
    @staticmethod
    def get_from_strings(username, project_name, tag_text, tag_type=None):
        # {{{
        # FIXME: Add support for tag-type-specific grabbing of Link_ProjectExp_Tags

        exp = ProjectExp.get_from_text(username, project_name)

        if tag_type is not None:
            tag_type_obj = TagType.objects.get(name=tag_type)
            tag = Tag.objects.get(text=tag_text, tag_type=tag_type_obj)
        else:
            tag = Tag.objects.get(text=tag_text)

        new_link = Link_ProjectExp_Tag.objects.get(project_exp=exp, tag=tag)

        return new_link
        # }}}

    # }}}

class Link_Project_Tag(models.Model):
    "Many-to-many relation between ProjectExps and Tags."
    # {{{
    tag = models.ForeignKey(Tag)
    project = models.ForeignKey(Project)
    source = models.CharField(max_length=200)
    # }}}

class Link_Person_Tag(models.Model):
    "Many-to-many relation between Person and Tags."
    # {{{
    tag = models.ForeignKey(Tag)
    person = models.ForeignKey(Person)
    source = models.CharField(max_length=200)
    # }}}

class SourceForgePerson(models.Model):
    '''A person in SourceForge.'''
    # FIXME: Make this unique
    username = models.CharField(max_length=200)

class SourceForgeProject(models.Model):
    '''A project in SourceForge.'''
    # FIXME: Make this unique
    unixname = models.CharField(max_length=200)


class Link_SF_Proj_Dude_FM(models.Model):
    '''Link from SourceForge Project to Person, via FlossMOLE'''
    person  = models.ForeignKey(SourceForgePerson)
    project = models.ForeignKey(SourceForgeProject)
    is_admin = models.BooleanField(default=False)
    position = models.CharField(max_length=200)
    date_collected = models.DateTimeField()
    class Meta:
        unique_together = [
            ('person', 'project'),]
            
    # FIXME: One day, this should

    @staticmethod
    def create_from_flossmole_row_data(dev_loginname, proj_unixname, is_admin,
                                       position, date_collected):
        """Given:
        {'dev_loginname': x, 'proj_unixname': y, is_admin: z,
        'position': a, 'date_collected': b}, return a
        SourceForgeProjectMembershipFromFlossMole instance."""
        person, _ = SourceForgePerson.objects.get_or_create(username=
                                                            dev_loginname)
        project, _ = SourceForgeProject.objects.get_or_create(unixname=
                                                              proj_unixname)
        is_admin = bool(int(is_admin))
        date_collected = datetime.datetime.strptime(
            date_collected, '%Y-%m-%d %H:%M:%S') # no time zone
        return Link_SF_Proj_Dude_FM.objects.get_or_create(
            person=person, project=project, is_admin=is_admin,
            position=position, date_collected=date_collected)

    @staticmethod
    def create_from_flossmole_row_string(row):
        row = row.strip()
        if row.startswith('#'):
            return None
        if row.startswith('dev_loginname'):
            return None
        person, proj_unixname, is_admin, position, date_collected = row.split('\t')
        return Link_SF_Proj_Dude_FM.create_from_flossmole_row_data(person,
                                                   proj_unixname,
                                                   is_admin, position,
                                                   date_collected)

