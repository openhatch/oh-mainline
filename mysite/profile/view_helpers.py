# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
# Copyright (C) 2009, 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import hashlib
from itertools import cycle, islice

import pygeoip

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
import django.core.mail
import django.core.serializers
from django.utils import simplejson

import logging
import mysite.search.view_helpers
import mysite.base.models
import mysite.search.models
import mysite.profile.models
import mysite.base.decorators

# roundrobin() taken from http://docs.python.org/library/itertools.html

# Name constants
SUGGESTION_COUNT = 6
DEFAULT_CACHE_TIMESPAN = 86400 * 7


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))

geoip_database = None


def geoip_city_database_available():
    return os.path.exists(settings.DOWNLOADED_GEOLITECITY_PATH)


def get_geoip_guess_for_ip(ip_as_string):
    # initialize database
    global geoip_database
    if geoip_database is None:
        system_geoip_path = '/usr/share/GeoIP/GeoIP.dat'
        downloaded_geolitecity_path = os.path.join(
            settings.MEDIA_ROOT,
            '../../downloads/GeoLiteCity.dat')
        if os.path.exists(system_geoip_path):
            geoip_database = pygeoip.GeoIP(system_geoip_path)
        if os.path.exists(settings.DOWNLOADED_GEOLITECITY_PATH):
            geoip_database = pygeoip.GeoIP(downloaded_geolitecity_path)

    if geoip_database is None:  # still?
        logging.warn("Uh, we could not find the GeoIP database.")
        return False, u''

    # First, get the country. This works on both the GeoCountry
    # and the GeoLiteCity database.
    country_name = geoip_database.country_name_by_addr(ip_as_string)

    # Try to increase our accuracy if we have the GeoLiteCity database.
    try:
        all_data_about_this_ip = geoip_database.record_by_addr(ip_as_string)
    except pygeoip.GeoIPError:
        return True, unicode(country_name, 'latin-1')

    if all_data_about_this_ip is None:
        return False, ''

    gimme = lambda x: all_data_about_this_ip.get(x, '')

    pieces = [gimme('city')]

    # Only add the region name if it's a string. Otherwise we add numbers to
    # the location, which can be confusing.
    region_name = gimme('region_name')
    try:
        int(region_name)
    except ValueError:
        pieces.append(region_name)

    pieces.append(gimme('country_name'))

    as_string = ', '.join([p for p in pieces if p])
    as_unicode = unicode(as_string, 'Latin-1')

    if as_unicode:
        return True, as_unicode
    return False, u''


def parse_string_query(s):
    parsed = {}
    valid_prefixes = ['project', 'icanhelp']
    valid_prefixes.extend(
        mysite.profile.models.TagType.short_name2long_name.keys())

    pieces_from_splitting_on_first_colon = s.split(':', 1)
    if (len(pieces_from_splitting_on_first_colon) > 1 and
            pieces_from_splitting_on_first_colon[0] in valid_prefixes):
        first, rest = pieces_from_splitting_on_first_colon
        parsed['query_type'], parsed['q'] = first, rest
    else:
        parsed['query_type'] = 'all_tags'
        parsed['q'] = s

    # Now, clean up the q to parse out quotation marks
    parsed['q'] = parsed['q'].strip()  # trim whitespace
    if len(parsed['q']) >= 2 and (
            parsed['q'][0] == '"' == parsed['q'][-1]):
        parsed['q'] = parsed['q'][1:-1]

    # If this is not a project-related search, but there are projects
    # that directly match the input, provide that info to the template.
    parsed.update(provide_project_query_hint(parsed))

    # Add a key to the structure called "callable_searcher" -- upon calling
    # this, you can access its .people and .template_data values.
    def callable_searcher(query_type=parsed['query_type'], search_string=parsed['q']):
        return _query2results(query_type, search_string)
    parsed['callable_searcher'] = callable_searcher
    return parsed


def email_spammy_user(u):
    message = '''Dear user of OpenHatch,

We took a look at your account activity and it looked like
your account is spamming the site with links. For now, we've
deleted your data from the site.

If this is an error, let us know your username (which was
%s ) and we can try to restore your data from a backup. If
it was a mistake, our apologies; we're just trying to make
the site more useful to everyone.

Sincerely,

-- OpenHatch.org staff''' % (u.username, )
    subject = "Removing your OpenHatch.org account due to possible abuse"
    msg = django.core.mail.EmailMessage(subject=subject,
                                        body=message,
                                        to=[u.email],
                                        bcc=[email
                                             for (name, email)
                                             in django.conf.settings.ADMINS],
                                        )
    msg.send()


def send_user_export_to_admins(u):
    '''You might want to call this function before deleting a user.

    It sends a semi-reasonable JSON representation of the user to the
    email addressed defined in ADMINS.

    That could be useful for:

    * training an antispam tool

    * recovering data on a user'''
    body = simplejson.dumps(generate_user_export(u),
                            cls=django.core.serializers.json.DjangoJSONEncoder)
    msg = django.core.mail.EmailMessage(subject="User export for %d" % u.id,
                                        body=body,
                                        to=[email
                                            for (name, email)
                                            in django.conf.settings.ADMINS],
                                        )
    msg.send()


def generate_user_export(u):
    out = {}
    out['answer_data'] = [django.forms.models.model_to_dict(a)
                          for a in u.answer_set.all()]
    out['tags'] = [django.forms.models.model_to_dict(t)
                   for t in mysite.profile.models.Tag.objects.filter(
                       link_person_tag__person__user=u)]
    out['user'] = django.forms.models.model_to_dict(u)
    del out['user']['password']
    person = u.get_profile()
    # Skip columns that can't be easily JSON serialized
    person.photo = None
    person.photo_thumbnail = None
    person.photo_thumbnail_30px_wide = None
    person.photo_thumbnail_20px_wide = None
    out['person'] = django.forms.models.model_to_dict(
        u.get_profile(), exclude=[
            'photo', 'photo_thumbnail', 'photo_thumbnail_20px_wide',
            'photo_thumbnail_30px_wide',
        ])
    return out


def _query2results(query_type, search_string):
    if query_type == 'project':
        return ProjectQuery(search_string=search_string)

    if query_type == 'icanhelp':
        return WannaHelpQuery(search_string=search_string)

    if query_type == 'all_tags':
        return AllTagsQuery(search_string=search_string)

    return TagQuery(tag_short_name=query_type,
                    search_string=search_string)

# These are helper functions for showing information about the query.


def query_type2query_summary(template_data):
    output_dict = {}

    if not template_data['q']:
        return output_dict

    if template_data['query_type'] == 'project':
        output_dict['this_query_summary'] = 'who have contributed to '
        output_dict['query_is_a_project_name'] = True
    elif template_data['query_type'] == 'icanhelp':
        output_dict[
            'this_query_summary'] = 'willing to contribute to the project '
        output_dict['query_is_a_project_name'] = True
    elif template_data['query_type'] == 'all_tags':
        output_dict['this_query_summary'] = 'who have listed'
        output_dict['this_query_post_summary'] = ' on their profiles'
    elif template_data['query_type'] == 'understands_not':
        output_dict['this_query_summary'] = 'tagged with understands_not = '
    elif template_data['query_type'] == 'understands':
        output_dict['this_query_summary'] = 'who understand '
    elif template_data['query_type'] == 'studying':
        output_dict['this_query_summary'] = 'who are currently studying '
    else:
        long_name = mysite.profile.models.TagType.short_name2long_name[
            template_data['query_type']]
        output_dict['this_query_summary'] = 'who ' + long_name

    if template_data['query_type'] == 'icanhelp' and not template_data['people']:
        output_dict['total_query_summary'] = (
            "No one has yet listed himself/herself as willing to contribute "
            "to the project <strong>%s</strong>." % template_data['q'])

    return output_dict


def provide_project_query_hint(parsed_query):
    output_dict = {}

    if parsed_query['query_type'] != 'project':
        # Figure out which projects happen to match that
        projects_that_match_q_exactly = []
        for word in [parsed_query['q']]:  # This is now tokenized smartly.
            name_matches = mysite.search.models.Project.objects.filter(
                name__iexact=word)
            for project in name_matches:
                if project.cached_contributor_count:
                    # only add those projects that have people in them
                    projects_that_match_q_exactly.append(project)
        output_dict[
            'projects_that_match_q_exactly'] = projects_that_match_q_exactly

    return output_dict


def get_most_popular_projects():
    # FIXME: This code is presumably terrible.
    key_name = 'most_popular_projects_last_flushed_on_20100325'
    popular_projects = cache.get(key_name)
    if popular_projects is None:
        projects = mysite.search.models.Project.objects.all()
        popular_projects = sorted(
            projects, key=lambda proj: len(proj.get_contributors()) * (-1))[:SUGGESTION_COUNT]
        # extract just the names from the projects
        popular_projects = [project.name for project in popular_projects]
        # cache it for a week
        cache.set(key_name, popular_projects, DEFAULT_CACHE_TIMESPAN)
    return popular_projects


def get_matching_project_suggestions(search_text):
    # FIXME: This code is presumably terrible.
    mps1 = mysite.search.models.Project.objects.filter(
        cached_contributor_count__gt=0, name__icontains=search_text).filter(
        ~Q(name__iexact=search_text)).order_by(
        '-cached_contributor_count')
    mps2 = mysite.search.models.Project.objects.filter(
        cached_contributor_count__gt=0, display_name__icontains=search_text).filter(
        ~Q(name__iexact=search_text)).order_by(
        '-cached_contributor_count')
    return mps1 | mps2


def get_most_popular_tags():
    # FIXME: This code is presumably terrible.
    key_name = 'most_popular_tags'
    popular_tags = cache.get(key_name)
    if popular_tags is None:
        # to get the most popular tags:
        # get all tags
        # order them by the number of people that list them
        # remove duplicates
        # lowercase them all and then remove duplicates
        # take the popular ones
        # cache it for a week
        popular_tags = []  # FIXME: I removed the implementation of this.
        cache.set(key_name, popular_tags, DEFAULT_CACHE_TIMESPAN)
    return popular_tags

# This code finds the right people to show on /people/, gathering a list
# of people and optional extra template data for the map.


class PeopleFinder(object):

    '''Subclasses of PeopleFinder take a query string as the only argument
    to __init__.py, and they create the self.template_data and self.people
    attributes.'''

    def __init__(self, search_string):
        raise NotImplementedError

    def get_person_instances_from_person_ids(self, person_ids):
        return mysite.profile.models.Person.objects.filter(
            pk__in=person_ids).select_related().order_by('user__username')

    def calculate_project(self, search_string):
        orm_projects = mysite.search.models.Project.objects.filter(
            name__iexact=search_string)
        if orm_projects:
            self.project = orm_projects[0]
            self.template_data['queried_project'] = self.project
        else:
            self.project = None
            self.template_data[
                'total_query_summary'] = "Sorry, we couldn't find a project named <strong>%s</strong>." % search_string

    def add_query_summary(self):
        raise NotImplementedError


class WannaHelpQuery(PeopleFinder):

    def __init__(self, search_string):
        self.template_data = {}
        self.calculate_project(search_string)
        self.people = []
        if self.project:
            self.people = self.project.people_who_wanna_help.all()
        self.add_query_summary()

    def add_query_summary(self):
        self.template_data[
            'this_query_summary'] = 'willing to contribute to the project '
        self.template_data['query_is_a_project_name'] = True


class TagQuery(PeopleFinder):
    # FIXME: Probably we should add a add_query_summary() method.

    def __init__(self, tag_short_name, search_string):
        self.template_data = {}
        self.people = []
        tag_type = self.get_tag_type(tag_short_name)
        if tag_type:
            self.people = self.get_persons_by_tag_type_and_text(
                tag_type, search_string)

    def get_tag_type(self, tag_short_name):
        tag_types = mysite.profile.models.TagType.objects.filter(
            name=tag_short_name)
        if not tag_types:
            return None
        return tag_types[0]

    def get_persons_by_tag_type_and_text(self, tag_type, search_string):
        tag_ids = mysite.profile.models.Tag.objects.filter(
            tag_type=tag_type, text__iexact=search_string).values_list('id', flat=True)
        person_ids = mysite.profile.models.Link_Person_Tag.objects.filter(
            tag__id__in=tag_ids).values_list('person_id', flat=True)
        return self.get_person_instances_from_person_ids(person_ids)


class AllTagsQuery(PeopleFinder):
    # FIXME: Probably we should add a add_query_summary() method.

    def __init__(self, search_string):
        self.template_data = {}
        self.people = mysite.profile.models.Person.objects.none()

        search_list = search_string.split(" ")

        # get search based on tags
        tag_results = mysite.profile.models.Person.objects.none()
        tag_results = self.get_persons_by_tag_text(
            search_string)

        # get search based on username
        user_results = mysite.profile.models.Person.objects.none()
        if len(search_list) == 1:
            user_results = self.get_persons_by_username(
                search_string)

        # get search based on last name
        lastname_results = mysite.profile.models.Person.objects.none()
        lastname_results2 = mysite.profile.models.Person.objects.none()
        for search_word in search_list:
            lastname_results2 = self.get_persons_by_lastname(
                search_word)
            lastname_results = lastname_results | lastname_results2

        # get search based on first name
        firstname_results = mysite.profile.models.Person.objects.none()
        firstname_results2 = mysite.profile.models.Person.objects.none()
        for search_word in search_list:
            firstname_results2 = self.get_persons_by_firstname(
                search_word)
            firstname_results = firstname_results | firstname_results2

        # Chain all the search results together
        self.people = tag_results | user_results | lastname_results | firstname_results

    def get_persons_by_tag_text(self, search_string):
        tag_ids = mysite.profile.models.Tag.objects.filter(
            text__iexact=search_string).values_list('id', flat=True)
        person_ids = mysite.profile.models.Link_Person_Tag.objects.filter(
            tag__id__in=tag_ids).values_list('person_id', flat=True)
        return self.get_person_instances_from_person_ids(person_ids)

    def get_persons_by_username(self, search_string):
        return mysite.profile.models.Person.objects.filter(
            user__username__icontains=search_string)

    def get_persons_by_lastname(self, search_string):
        return mysite.profile.models.Person.objects.filter(
            user__last_name__icontains=search_string)

    def get_persons_by_firstname(self, search_string):
        return mysite.profile.models.Person.objects.filter(
            user__first_name__icontains=search_string)


class ProjectQuery(PeopleFinder):

    def __init__(self, search_string):
        self.template_data = {}
        self.people = []
        # We never got faceting working properly with Haystack, while doing
        # exact searches, so we do the queries via the ORM.

        self.calculate_project(search_string)
        self.add_query_summary()

        if self.project:
            self.calculate_people_for_project()
            self.add_wanna_help_count()

    def calculate_people_for_project(self):
        person_ids = mysite.profile.models.PortfolioEntry.published_ones.filter(
            project=self.project).values_list('person_id', flat=True)
        self.people = self.get_person_instances_from_person_ids(person_ids)

    def add_wanna_help_count(self):
        self.template_data[
            'icanhelp_count'] = self.project.people_who_wanna_help.count()

    def add_query_summary(self):
        self.template_data['this_query_summary'] = 'who have contributed to '
        self.template_data['query_is_a_project_name'] = True
