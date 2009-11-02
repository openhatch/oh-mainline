# vim: set ai ts=4 sw=4 et:

from django.db import models
from mysite.search.models import Project, Bug
from django.contrib.auth.models import User
from mysite.customs import ohloh
import datetime
import sys
import uuid

def generate_person_photo_path(instance, filename):
    random_uuid = uuid.uuid4()
    return random_uuid.hex

class Person(models.Model):
    """ A human bean. """
    # {{{
    user = models.ForeignKey(User, unique=True)
    gotten_name_from_ohloh = models.BooleanField(default=False)
    interested_in_working_on = models.CharField(max_length=1024, default='') # FIXME: Ditch this.
    last_polled = models.DateTimeField(default=datetime.datetime(1970, 1, 1))
    show_email = models.BooleanField(default=False)
    photo = models.ImageField(upload_to=
                              lambda a, b: 'static/photos/profile-photos/' + 
                              generate_person_photo_path(a, b),
                              default='')

    def __unicode__(self):
        return "username: %s, name: %s %s" % (self.user.username,
                self.user.first_name, self.user.last_name)

    def get_photo_url_or_default(self):
        try:
            return self.photo.url
        except ValueError:
            return '/static/images/profile-photos/penguin.png'

    def get_published_portfolio_entries(self):
        return PortfolioEntry.objects.filter(person=self, is_published=True, is_deleted=False)

    def get_recommended_search_terms(self):
        # {{{
        project_exps = ProjectExp.objects.filter(person=self)
        terms = [p.primary_language for p in project_exps
                if p.primary_language and p.primary_language.strip()]
        terms.extend(
                [p.project.name for p in project_exps
                    if p.project.name and p.project.name.strip()])
        terms = sorted(set(terms), key=lambda s: s.lower())
        return terms

        # FIXME: Add support for recommended projects.
        # FIXME: Add support for recommended project tags.

        # }}}

    def get_full_name(self):
        # {{{
        name = self.user.first_name 
        if self.user.first_name and self.user.last_name:
            name += " "
        name += self.user.last_name
        return name
        # }}}

    def get_full_name_or_username(self):
        return self.get_full_name() or self.user.username
    # }}}

def create_profile_when_user_created(instance, created, *args, **kwargs):
    if created:
        person, p_created = Person.objects.get_or_create(user=instance)
        
models.signals.post_save.connect(create_profile_when_user_created, User)

class DataImportAttempt(models.Model):
    # {{{
    SOURCE_CHOICES = (
        ('rs', "Ohloh"),
        ('ou', "Ohloh"),
        ('lp', "Launchpad"),
        )
    completed = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    source = models.CharField(max_length=2,
                              choices=SOURCE_CHOICES)
    person = models.ForeignKey(Person)
    query = models.CharField(max_length=200)
    date_created = models.DateTimeField(default=datetime.datetime.utcnow)

    def get_formatted_source_description(self):
        return self.get_source_display() % self.query

    def do_what_it_says_on_the_tin(self):
        """Attempt to import data by enqueuing a job in celery."""
        # We need to import here to avoid vicious cyclical imports.
        from mysite.profile.tasks import FetchPersonDataFromOhloh
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
    modified = models.BooleanField(default=False)

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
            # FIXME: Handle first_commit_time from Ohloh somehow
            #if 'first_commit_time' in ohloh_contrib_info:
                # parse it
                #parsed = datetime.datetime.strptime(
                #    ohloh_contrib_info['first_commit_time'],
                #    '%Y-%m-%dT%H:%M:%SZ')
                # This is UTC.

                # jam it into self
                #self.date_started = parsed
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

class PortfolioEntry(models.Model):
    # Constrain this so (person, project) pair uniquely finds a PortfolioEntry
    person = models.ForeignKey(Person)
    project = models.ForeignKey(Project)
    project_description = models.TextField()
    experience_description = models.TextField()
    date_created = models.DateTimeField(default=datetime.datetime.utcnow)
    is_published = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def get_published_citations(self):
        return Citation.objects.filter(portfolio_entry=self,
                is_published=True, is_deleted=False)

# FIXME: Add a DataSource class to DataImportAttempt.

class Citation(models.Model):
    portfolio_entry = models.ForeignKey(PortfolioEntry) # [0]
    url = models.URLField(null=True)
    contributor_role = models.CharField(max_length=200, null=True)
    data_import_attempt = models.ForeignKey(DataImportAttempt, null=True)
    distinct_months = models.IntegerField(null=True)
    languages = models.CharField(max_length=200, null=True)
    first_commit_time = models.DateTimeField(null=True)
    date_created = models.DateTimeField(default=datetime.datetime.utcnow)
    is_published = models.BooleanField(default=False) # unpublished == Unread
    is_deleted = models.BooleanField(default=False)
    old_summary = models.TextField(null=True, default=None)

    @property
    def summary(self):
        # FIXME: Pluralize correctly.
        # FIXME: Use "since year_started"

        if self.distinct_months != 1:
            suffix = 's'
        else:
            suffix = ''

        if self.data_import_attempt:
            if self.data_import_attempt.source in ['rs', 'ou']:
                if self.distinct_months is None:
                    raise ValueError, "Er, Ohloh always gives us a # of months."
                return "Coded for %d month%s in %s (%s)" % (
                        self.distinct_months,
                        suffix,
                        self.languages,
                        self.data_import_attempt.get_source_display(),
                        )
            elif self.data_import_attempt.source == 'lp':
                return "%s: Participated in %s" % (
                    self.data_import_attempt.get_source_display(),
                    self.contributor_role)
            else:
                raise ValueError, "There's a DIA of a kind I don't know how to summarize."
        elif self.url is not None:
            return self.url
        elif self.distinct_months is not None and self.languages is not None:
            return "Coded for %d month%s in %s." % (
                    self.distinct_months,
                    suffix,
                    self.languages,
                    )

        raise ValueError("There's no DIA and I don't know how to summarize this.")

    @staticmethod
    def create_from_ohloh_contrib_info(ohloh_contrib_info):
        """Create a new Citation from a dictionary roughly representing an Ohloh ContributionFact."""
        # {{{
        # FIXME: Enforce uniqueness on (source, vcs_committer_identifier, project)
        # Which is to say, overwrite the previous citation with the same source,
        # vcs_committer_identifier and project.
        # FIXME: Also store ohloh_contrib_info somewhere so we can parse it later.
        # FIXME: Also store the launchpad HttpResponse object somewhere so we can parse it l8r.
        # "We'll just pickle the sucker and throw it into a database column. This is going to be
        # very exciting. just Hhhomphf." -- Asheesh.
        citation = Citation()
        citation.distinct_months = ohloh_contrib_info['man_months']
        citation.languages = ohloh_contrib_info['primary_language']
        #citation.year_started = ohloh_contrib_info['year_started']
        return citation
        # }}}

    # [0]: FIXME: Let's learn how to use Django's ManyToManyField etc.

# vim: set nu:
