# vim: set ai ts=4 sw=4 et:

from mysite.search.models import Project, Bug, get_image_data_scaled
import mysite.customs.models
from mysite.customs import ohloh
import mysite.profile.controllers

import django
from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend
from django.core.urlresolvers import reverse

import datetime
import sys
import uuid
import urllib
import random
import collections

DEFAULT_LOCATION='Inaccessible Island'

def url2printably_short(url, CUTOFF=50):
    short_enough_pieces_so_far = []
    die_next = False
    wrappable_characters = "/"
    for url_piece in url.split(wrappable_characters):
        if die_next:
            return '/'.join(short_enough_pieces_so_far)

        # Logic: If this URL piece is longer than CUTOFF, then stop appending
        # and return.
        if len(url_piece) > CUTOFF:
            url_piece = url_piece[:CUTOFF-3] + '...'
            die_next = True
        # always append
        short_enough_pieces_so_far.append(url_piece)
    return '/'.join(short_enough_pieces_so_far)

def generate_person_photo_path(instance, filename, suffix=""):
    random_uuid = uuid.uuid4()
    return random_uuid.hex + suffix

class RepositoryCommitter(models.Model):
    """Ok, so we need to keep track of repository committers, e.g.
        paulproteus@fspot
    That's because when a user says, 'oy, this data you guys imported isn't
    mine', what she or he is typically saying is something like
    'Don't give me any more data from Ohloh pertaining to this dude named
    mickey.mouse@strange.ly checking code into F-Spot.'"""
    project = models.ForeignKey(Project)
    data_import_attempt = models.ForeignKey('DataImportAttempt')

    def committer_identifier(self):
        return self.data_import_attempt.committer_identifier

    def source(self):
        return self.data_import_attempt.source

    class Meta:
        unique_together = ('project', 'data_import_attempt')

class Person(models.Model):
    """ A human bean. """
    # {{{
    homepage_url = models.URLField(default="", blank=True)
    user = models.ForeignKey(User, unique=True)
    gotten_name_from_ohloh = models.BooleanField(default=False)
    interested_in_working_on = models.CharField(max_length=1024, default='') # FIXME: Ditch this.
    last_polled = models.DateTimeField(default=datetime.datetime(1970, 1, 1))
    show_email = models.BooleanField(default=False)
    bio = models.TextField(blank=True) 
    contact_blurb = models.TextField(blank=True) 
    photo = models.ImageField(upload_to=
                              lambda a, b: 'static/photos/profile-photos/' + 
                              generate_person_photo_path(a, b),
                              default='')
    photo_thumbnail = models.ImageField(upload_to=
                              lambda a, b: 'static/photos/profile-photos/' + 
                              generate_person_photo_path(a, b, suffix="-thumbnail"),
                              default='',
                              null=True)
    blacklisted_repository_committers = models.ManyToManyField(RepositoryCommitter)
    dont_guess_my_location = models.BooleanField(default=False)
    location_confirmed = models.BooleanField(default=False)
    location_display_name = models.CharField(max_length=255, blank=True,
                                             verbose_name='Location')

    def location_is_public(self):
        return self.location_confirmed and self.location_display_name

    def get_public_location_or_default(self):
        if self.location_is_public():
            return self.location_display_name
        else:
            return DEFAULT_LOCATION
    
    def __unicode__(self):
        return "username: %s, name: %s %s" % (self.user.username,
                self.user.first_name, self.user.last_name)

    def get_photo_url_or_default(self):
        try:
            return self.photo.url
        except ValueError:
            return '/static/images/profile-photos/penguin.png'

    @staticmethod
    def get_from_session_key(session_key):
        '''Based almost entirely on
        http://www.djangosnippets.org/snippets/1276/
        Thanks jdunck!'''

        session_engine = __import__(settings.SESSION_ENGINE, {}, {}, [''])
        session_wrapper = session_engine.SessionStore(session_key)
        user_id = session_wrapper.get(SESSION_KEY)
        auth_backend = load_backend(
                session_wrapper.get(BACKEND_SESSION_KEY))

        if user_id and auth_backend:
            return Person.objects.get(user=auth_backend.get_user(user_id))
        else:
            return None

    @models.permalink
    def get_profile_url(self):
        return reverse(mysite.profile.views.display_person_web,
                {'user_to_display__username': self.user.username})

    def get_photo_thumbnail_url_or_default(self):
        try:
            return self.photo_thumbnail.url
        except ValueError:
            return '/static/images/profile-photos/penguin-40px.png'

    def get_published_portfolio_entries(self):
        return PortfolioEntry.objects.filter(person=self, is_published=True, is_deleted=False)

    def get_list_of_project_names(self):
        return self.get_published_portfolio_entries().values_list('project__name', flat=True)

    @staticmethod
    def only_terms_with_results(terms):
        # Remove terms whose hit counts are zero.
        terms_with_results = [] 
        for term in terms:
            query = mysite.search.controllers.Query(terms=[term])
            hit_count = query.get_or_create_cached_hit_count()
            if hit_count != 0:
                terms_with_results.append(term)
        return terms_with_results

    def get_recommended_search_terms(self):
        # {{{
        terms = []
        
        # Add terms based on languages in citations
        citations = self.get_published_citations_flat()
        for c in citations:
            terms.extend(c.get_languages_as_list())

        # Add terms based on projects in citations
        terms.extend(
                [pfe.project.name for pfe in self.get_published_portfolio_entries()
                    if pfe.project.name and pfe.project.name.strip()])

        # Add terms based on tags 
        terms.extend([tag.text for tag in self.get_tags_for_recommendations()])

        # Remove duplicates
        terms = sorted(set(terms), key=lambda s: s.lower())

        return Person.only_terms_with_results(terms)

        # FIXME: Add support for recommended projects.
        # FIXME: Add support for recommended project tags.

        # }}}

    def get_published_citations_flat(self):
        return sum([list(pfe.get_published_citations())
            for pfe in self.get_published_portfolio_entries()], [])

    def calculate_summary(self, tag_text):
        return ''

    def get_tag_texts_for_map(self):
        """Return a list of Tags linked to this Person.  Tags that would be useful from the map view of the people list"""
        exclude_me = TagType.objects.filter(name__in=['understands_not', 'studying'])
        my_tag_texts = (link.tag.text for link in Link_Person_Tag.objects.filter(person=self) if link.tag.tag_type not in exclude_me)
        #eliminate duplicates, case-sensitively, then return
        already_added = set()
        to_return = []
        for tag_text in my_tag_texts:
            lowered = tag_text.lower()
            if lowered in already_added:
                continue # skip if already added this
            else:
                to_return.append(tag_text)
                already_added.add(lowered)
        to_return.sort() # side-effect-y sort()
        return to_return

    def get_tags_as_dict(self):
        ret = collections.defaultdict(set)
        for link in Link_Person_Tag.objects.filter(person=self):
            ret[link.tag.tag_type.name].add(link.tag.text.lower())
        return ret

    def get_tag_descriptions_for_keyword(self, keyword):
        keyword = keyword.lower()
        d = self.get_tags_as_dict()
        return sorted([TagType.short_name2long_name[short]
                       for short in [key for key in d if (keyword in d[key])]])

    def get_tags_for_recommendations(self):
        """Return a list of Tags linked to this Person.  For use with bug recommendations."""
        exclude_me = TagType.objects.filter(name='understands_not')
        return [link.tag for link in Link_Person_Tag.objects.filter(person=self) if link.tag.tag_type not in exclude_me]

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

    def generate_thumbnail_from_photo(self):
        if self.photo:
            width = 40
            self.photo.file.seek(0) 
            scaled_down = get_image_data_scaled(self.photo.file.read(), width)
            self.photo_thumbnail.save('', ContentFile(scaled_down))

    def get_collaborators_for_landing_page(self, n=9):
        projects = set([e.project for e in self.get_published_portfolio_entries()])
        infinity = 10000
        collaborator_lists = []
        for project in projects:
            people = project.get_n_other_contributors_than(n=infinity, person=self)
            people = random.sample(people, min(n, len(people)))
            collaborator_lists.append(people)
        round_robin = mysite.profile.controllers.roundrobin(*collaborator_lists)
        collaborators = set() 
        while len(collaborators) < n:
            try:
                collaborators.add(round_robin.next())
            except StopIteration:
                break
        collaborators = list(collaborators)
        random.shuffle(collaborators) # don't forget, this has a side effect and returns None
        return collaborators

    @property
    def profile_url(self):
        return reverse(mysite.profile.views.display_person_web,
                kwargs={'user_to_display__username': self.user.username})

    @staticmethod
    def get_by_username(username):
        return Person.objects.get(user__username=username)

    def should_be_nudged_about_location(self):
        return not self.location_confirmed and not self.dont_guess_my_location

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
        ('gh', "Github"),
        ('ga', "Github"),
        ('db', "Debian"),
        )
    completed = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    source = models.CharField(max_length=2,
                              choices=SOURCE_CHOICES)
    person = models.ForeignKey(Person)
    query = models.CharField(max_length=200)
    date_created = models.DateTimeField(default=datetime.datetime.utcnow)
    web_response = models.ForeignKey(mysite.customs.models.WebResponse, 
                                     null=True) # null=True for
    # now, so the migration doesn't cause data validation errors

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

'''
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
'''

def reject_when_query_is_only_whitespace(sender, instance, **kwargs):
    if not instance.query.strip():
        raise ValueError, "You tried to save a DataImportAttempt whose query was only whitespace, and we rejected it."

def update_the_project_cached_contributor_count(sender, instance, **kwargs):
    instance.project.update_cached_contributor_count()

def update_the_person_index(sender, instance, **kwargs):
    person = instance.person
    # Enqueue a background task to re-index the person
    import mysite.profile.tasks
    task = mysite.profile.tasks.ReindexPerson()
    task.delay(person_id=person.id)

models.signals.pre_save.connect(reject_when_query_is_only_whitespace, sender=DataImportAttempt)

class TagType(models.Model):
    # {{{
    short_name2long_name = {'understands': 'understands',
                            'can_mentor': 'can mentor in',
                            'can_pitch_in': 'can pitch in with',
                            'understands_not': 'will never understand',
                            'studying': 'currently studying'}
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name
    # }}}

class Tag(models.Model):
    # {{{
    text = models.CharField(null=False, max_length=255)
    tag_type = models.ForeignKey(TagType)

    @property
    def name(self):
        return self.text

    def save(self, *args, **kwargs):
        if self.text:
            return super(Tag, self).save(*args, **kwargs)
        raise ValueError

    @staticmethod
    def get_people_by_tag_name(tag_name):
        peeps = []
        for tag_type in TagType.objects.all():
            peeps.extend(mysite.profile.controllers.people_matching(tag_type.name, tag_name))
        return peeps

    def __unicode__(self):
        return "%s: %s" % (self.tag_type.name, self.text)
    # }}}

class Link_Project_Tag(models.Model):
    "Many-to-many relation between Projects and Tags."
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
        return Citation.untrashed.filter(portfolio_entry=self,
                is_published=True)

# FIXME: Add a DataSource class to DataImportAttempt.

class UntrashedCitationManager(models.Manager):
    def get_query_set(self):
        return super(UntrashedCitationManager, self).get_query_set().filter(

                # Was the citation superseded by a previously imported equivalent?
                ignored_due_to_duplicate=False, 

                # Was the citation deleted?
                is_deleted=False,

                # Was its portfolio entry deleted?
                portfolio_entry__is_deleted=False)

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
    ignored_due_to_duplicate = models.BooleanField(default=False)
    old_summary = models.TextField(null=True, default=None)

    objects = models.Manager()
    untrashed = UntrashedCitationManager()

    @property
    def summary(self):
        # FIXME: Pluralize correctly.
        # FIXME: Use "since year_started"

        if self.distinct_months != 1:
            suffix = 's'
        else:
            suffix = ''

        if self.data_import_attempt:
            if self.data_import_attempt.source == 'db' and (
                self.contributor_role == 'Maintainer'):
                return 'Maintain a package in Debian.'
            if self.data_import_attempt.source == 'db' and (
                self.contributor_role.startswith('Maintainer of')):
                return self.contributor_role
            if self.data_import_attempt.source in ('gh', 'ga'):
                return '%s a repository on Github.' % self.contributor_role
            if self.data_import_attempt.source in ['rs', 'ou']:
                if not self.languages:
                    return "Committed to codebase (%s)" % (
                            self.data_import_attempt.get_source_display(),
                            )
                if self.distinct_months is None:
                    raise ValueError, "Er, Ohloh always gives us a # of months."
                return "Coded for %d month%s in %s (%s)" % (
                        self.distinct_months,
                        suffix,
                        self.languages,
                        self.data_import_attempt.get_source_display(),
                        )
            elif self.data_import_attempt.source == 'lp':
                return "Participated in %s (%s)" % (
                    self.contributor_role,
                    self.data_import_attempt.get_source_display()
                    )
            else:
                raise ValueError, "There's a DIA of a kind I don't know how to summarize."
        elif self.url is not None:
            return url2printably_short(self.url, CUTOFF=38)
        elif self.distinct_months is not None and self.languages is not None:
            return "Coded for %d month%s in %s." % (
                    self.distinct_months,
                    suffix,
                    self.languages,
                    )

        raise ValueError("There's no DIA and I don't know how to summarize this.")

    def get_languages_as_list(self):
        if self.languages is None:
            return []
        return [lang.strip() for lang in self.languages.split(",") if lang.strip()]

    def get_url_or_guess(self):
        if self.url:
            return self.url
        else:
            if self.data_import_attempt:
                if self.data_import_attempt.source in ['rs', 'ou']:
                    return "http://www.ohloh.net/search?%s" % urllib.urlencode(
                            {'q': self.portfolio_entry.project.name.encode('utf-8')})
                elif self.data_import_attempt.source == 'lp':
                    return "https://launchpad.net/~%s" % urllib.quote(
                            self.data_import_attempt.query)

    def save_and_check_for_duplicates(self):
        # FIXME: Cache summaries in the DB so this query is faster.
        duplicates = [citation for citation in
                Citation.objects.filter(portfolio_entry=self.portfolio_entry)
                if (citation.pk != self.pk) and (citation.summary == self.summary)]

        if duplicates:
            self.ignored_due_to_duplicate = True
        return self.save()

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

    def __unicode__(self):
        if self.pk is not None:
            pk = self.pk
        else:
            pk = 'unassigned'
        return "pk=%s, summary=%s" % (pk, self.summary)

class Forwarder(models.Model):
    address = models.TextField()
    expires_on = models.DateTimeField(default=datetime.datetime(1970, 1, 1))
    user = models.ForeignKey(User)
    def generate_table_line(self):
        line = '%s %s' % (self.get_email_address(), self.user.email)
        return line

    def get_email_address(self): 
        return self.address + "@" + settings.FORWARDER_DOMAIN

    @staticmethod
    def generate_list_of_lines_for_postfix_table():
        lines = []
        for live_forwarder in Forwarder.objects.all():
            if live_forwarder.user.email:
                line = live_forwarder.generate_table_line()
                lines.append(line)
        return lines
        


def make_forwarder_actually_work(sender, instance, **kwargs):
    from mysite.profile.tasks import RegeneratePostfixAliasesForForwarder
    RegeneratePostfixAliasesForForwarder.delay()

models.signals.post_save.connect(update_the_project_cached_contributor_count, sender=PortfolioEntry)
models.signals.post_save.connect(update_the_person_index, sender=PortfolioEntry)
models.signals.post_save.connect(make_forwarder_actually_work, sender=Forwarder)

# vim: set nu:
