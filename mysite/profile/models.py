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
    last_touched = models.DateTimeField(null=True)
    poll_on_next_web_view = models.BooleanField(
            default=True)
    interested_in_working_on = models.CharField(max_length=1024, default='')

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
            exp = ProjectExp()
            exp.person = self
            exp = exp.from_ohloh_contrib_info(ohloh_contrib_info)
            exp.last_polled = datetime.datetime.now()
            exp.last_touched = datetime.datetime.now()
            exp.save()
        self.last_polled = datetime.datetime.now()
        self.save()
        
    def __unicode__(self):
        return "username: %s, name: %s" % (self.username, self.name)
    # }}}

class ProjectExp(models.Model):
    "Many-to-one relation between projects and people."
    # {{{
    person = models.ForeignKey(Person)
    project = models.ForeignKey(Project)
    person_role = models.CharField(max_length=200)
    time_record_was_created = models.DateTimeField(null=True)
    last_touched = models.DateTimeField(null=True)
    description = models.TextField()
    url = models.URLField(max_length=200, null=True)
    #time_start = models.DateTimeField(null=True)
    #time_finish = models.DateTimeField(null=True)
    man_months = models.PositiveIntegerField(null=True)
    favorite = models.BooleanField(default=0)
    primary_language = models.CharField(max_length=200, null=True)
    source = models.CharField(max_length=100, null=True)

    def save(self, *args, **kwargs):
        self.last_touched = datetime.datetime.now()
        super(ProjectExp, self).save(*args, **kwargs)

    # FIXME: Make this a static method or something
    def from_ohloh_contrib_info(self, ohloh_contrib_info):
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

    @staticmethod
    def create_from_text(
            username,
            project_name,
            description='',
            url='',
            man_months=None,
            primary_language=''
            ):

        person = Person.objects.get(username=username)
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
                person=Person.objects.get(username=username),
                project=Project.objects.get(name=project_name),
                )
    get_from_strings = get_from_text

    def save(self, *args, **kwargs):
        if self.time_record_was_created is None:
            self.time_record_was_created = datetime.datetime.now()
        super(ProjectExp, self).save(*args, **kwargs)

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
    time_record_was_created = models.DateTimeField(
            default=datetime.datetime.now())
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
    time_record_was_created = models.DateTimeField(
            default=datetime.datetime.now())
    source = models.CharField(max_length=200)
    # }}}

class SourceForgePerson(models.Model):
    '''A person in SourceForge.'''
    username = models.CharField(max_length=200)

class SourceForgeProject(models.Model):
    '''A project in SourceForge.'''
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
            
