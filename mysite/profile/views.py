# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009 Karen Rustad
# Copyright (C) 2010 John Stumpo
# Copyright (C) 2011 Krzysztof Tarnowski (krzysztof.tarnowski@ymail.com)
# Copyright (C) 2009, 2010, 2011 OpenHatch, Inc.
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

# Imports {{{

# Python
import StringIO
import datetime
import urllib
from django.utils import simplejson
import re
import collections
import logging

# Django
from django.template.loader import render_to_string
from django.template import RequestContext
from django.core import serializers
from django.http import \
    HttpResponse, HttpResponseRedirect, HttpResponseServerError, HttpResponsePermanentRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
import django.views.generic
from django.utils import http

# OpenHatch apps
import mysite.base.view_helpers
import mysite.profile.view_helpers
from mysite.profile.models import \
    Person, Tag, TagType, \
    Link_Project_Tag, Link_Person_Tag, \
    DataImportAttempt, PortfolioEntry, Citation
from mysite.search.models import Project
from mysite.base.decorators import view, as_view
import mysite.profile.forms
import mysite.profile.tasks
from mysite.base.view_helpers import render_response
from django.views.decorators.csrf import csrf_protect

# }}}


@login_required
def delete_user_for_being_spammy(request):
    form = mysite.profile.forms.DeleteUser()
    if request.method == 'POST':
        if request.user.username != 'paulproteus':
            return HttpResponseBadRequest("Sorry, you may not do that.")
        form = mysite.profile.forms.DeleteUser(
            request.POST)
        if form.is_valid():
            u = User.objects.get(username=form.cleaned_data['username'])
            # Dump data about the user to the site admins
            mysite.profile.view_helpers.send_user_export_to_admins(u)
            # Send out an email to the poor sap.
            mysite.profile.view_helpers.email_spammy_user(u)
            # Okay... delete the user.
            u.delete()  # hoo boy!
            return HttpResponseRedirect(reverse(
                delete_user_for_being_spammy))

    return as_view(
        request,
        'profile/delete_user.html',
        {'form': form},
        None)


@login_required
def add_citation_manually_do(request):
    # {{{
    form = mysite.profile.forms.ManuallyAddACitationForm(request.POST)
    form.set_user(request.user)

    output = {
        'form_container_element_id': request.POST['form_container_element_id']
    }
    if form.is_valid():
        citation = form.save()

        # Manually added citations are published automatically.
        citation.is_published = True
        citation.save()

        json = simplejson.dumps(output)
        return HttpResponse(json, mimetype='application/json')

    else:
        error_msgs = []
        for error in form.errors.values():
            error_msgs.extend(eval(error.__repr__()))  # don't ask questions.

        output['error_msgs'] = error_msgs
        json = simplejson.dumps(output)
        return HttpResponseServerError(json, mimetype='application/json')

    #}}}


@view
def display_person_web(request, user_to_display__username=None):
    # {{{

    user = get_object_or_404(User, username=user_to_display__username)
    person, was_created = Person.objects.get_or_create(user=user)

    data = get_personal_data(person)
    data['edit_mode'] = False
    data['editable'] = (request.user == user)
    data['notifications'] = mysite.base.view_helpers.get_notification_from_request(
        request)
    data['explain_to_anonymous_users'] = True
    data['how_many_archived_pf_entries'] = person.get_published_portfolio_entries().filter(
        is_archived=True).count()

    return (request, 'profile/main.html', data)

    # }}}

# FIXME: Create a separate function that just passes the data required for
# displaying the little user bar on the top right to the template, and
# leaves out all the data required for displaying the large user bar on
# the left.


def get_personal_data(person):
    # {{{

    # FIXME: Make this more readable.
    data_dict = {
        'person': person,
        'photo_url': person.get_photo_url_or_default(),
    }

    data_dict['tags'] = tags_dict_for_person(person)
    data_dict['tags_flat'] = dict(
        [(key, ', '.join([k.text for k in data_dict['tags'][key]]))
         for key in data_dict['tags']])

    data_dict['has_set_info'] = any(data_dict['tags_flat'].values())

    data_dict['contact_blurb'] = mysite.base.view_helpers.put_forwarder_in_contact_blurb_if_they_want(
        person.contact_blurb, person.user)

    data_dict['projects_i_wanna_help'] = person.projects_i_wanna_help.all()

    return data_dict

    # }}}


def tags_dict_for_person(person):
    # {{{
    ret = collections.defaultdict(list)
    links = Link_Person_Tag.objects.filter(person=person).order_by('id')
    for link in links:
        ret[link.tag.tag_type.name].append(link.tag)

    return ret
    # }}}

# FIXME: Test this.


def widget_display_undecorated(request, user_to_display__username):
    """We leave this function unwrapped by @view """
    """so it can referenced by widget_display_string."""
    # {{{
    user = get_object_or_404(User, username=user_to_display__username)
    person = get_object_or_404(Person, user=user)

    data = get_personal_data(person)
    data.update(mysite.base.view_helpers.get_uri_metadata_for_generating_absolute_links(
        request))
    return (request, 'profile/widget.html', data)
    # }}}

widget_display = view(widget_display_undecorated)


def widget_display_string(request, user_to_display__username):
    request, template, data = widget_display_undecorated(
        request, user_to_display__username)
    return render_to_string(template, data)


def widget_display_js(request, user_to_display__username):
    # FIXME: In the future, use:
    html_doc = widget_display_string(request, user_to_display__username)
    # to generate html_doc
    encoded_for_js = simplejson.dumps(html_doc)
    # Note: using application/javascript as suggested by
    # http://www.ietf.org/rfc/rfc4329.txt
    return render_response(request, 'base/append_ourselves.js',
                           {'in_string': encoded_for_js},
                           mimetype='application/javascript')

# }}}

# Debtags {{{


def add_one_debtag_to_project(project_name, tag_text):
    # {{{
    tag_type, created = TagType.objects.get_or_create(name='Debtags')

    project, project_created = Project.objects.get_or_create(name=project_name)

    tag, tag_created = Tag.objects.get_or_create(
        text=tag_text, tag_type=tag_type)

    new_link = Link_Project_Tag.objects.create(
        tag=tag, project=project,
        source='Debtags')
    new_link.save()
    return new_link
# }}}


def list_debtags_of_project(project_name):
    # {{{
    debtags_list = list(TagType.objects.filter(name='Debtags'))
    if debtags_list:
        debtags = debtags_list[0]
    else:
        return []

    project_list = list(Project.objects.filter(name=project_name))
    if project_list:
        project = project_list[0]
    else:
        return []

    resluts = list(Link_Project_Tag.objects.filter(project=project,
                                                   tag__tag_type=debtags))
    return [link.tag.text for link in resluts]
    # }}}


def import_debtags(cooked_string=None):
    # {{{
    if cooked_string is None:
        # Warning: this re-downloads the list from Alioth every time this
        # is called
        import urllib2
        import gzip
        fd = urllib2.urlopen(
            'http://debtags.alioth.debian.org/tags/tags-current.gz')
        gzipped_sio = StringIO.StringIO(fd.read())  # this sucks, but I
        # can't stream to
        # gzip.GzipFile because
        # urlopen()'s result
        # lacks tell()
        gunzipped = gzip.GzipFile(fileobj=gzipped_sio)
    else:
        gunzipped = StringIO.StringIO(cooked_string)
    for line in gunzipped:
        if ':' in line:
            package, tagstring = line.split(':', 1)
            tags = map(lambda s: s.strip(), tagstring.split(','))
            for tag in tags:
                add_one_debtag_to_project(package, tag)
    # }}}

# }}}

# Project experience tags {{{

# }}}


def _project_hash(project_name):
    # {{{
    # This prefix is a sha256 of 1MiB of /dev/urandom
    PREFIX = '_project_hash_2136870e40a759b56b9ba97a0'
    PREFIX += 'd7f60b84dbc90097a32da284306e871105d96cd'
    import hashlib
    hashed = hashlib.sha256(PREFIX + project_name)
    return hashed.hexdigest()
    # }}}


@login_required
# this is a post handler
def edit_person_info_do(request):
    # {{{
    person = request.user.get_profile()

    edit_info_form = mysite.profile.forms.EditInfoForm(
        request.POST, prefix='edit-tags')
    contact_blurb_form = mysite.profile.forms.ContactBlurbForm(
        request.POST, prefix='edit-tags')
    contact_blurb_error = False
    errors_occurred = False

    # Grab the submitted homepage URL.
    if edit_info_form.is_valid():
        person.homepage_url = edit_info_form.cleaned_data['homepage_url']
    else:
        errors_occurred = True

    # grab their submitted bio
    person.bio = edit_info_form['bio'].data

    # grab the irc nick
    person.irc_nick = edit_info_form['irc_nick'].data

    # We can map from some strings to some TagTypes
    for known_tag_type_name in ('understands', 'understands_not',
                                'studying', 'can_pitch_in', 'can_mentor'):
        tag_type, _ = TagType.objects.get_or_create(name=known_tag_type_name)

        text = edit_info_form[known_tag_type_name].data or ''
        # Set the tags to this thing
        new_tag_texts_for_this_type_raw = text.split(',')
        new_tag_texts_for_this_type = [tag.strip()
                                       for tag in new_tag_texts_for_this_type_raw]
        # Now figure out what tags are in the DB
        old_tag_links = Link_Person_Tag.objects.filter(
            tag__tag_type=tag_type, person=person)

        # FIXME: Churn, baby churn
        for link in old_tag_links:
            link.delete()

        for tag_text in new_tag_texts_for_this_type:
            if not tag_text.strip():  # Don't save blank tags.
                continue

            # HACK
            if type(tag_text) == str:
                tag_text = unicode(tag_text, 'utf-8')

            # The following code gets the first matching tag or creates one. We
            # previously used a straight-up get_or_create, but the parameters
            # (name, tagtype) no longer uniquely select a tag. We get errors
            # like this: "MultipleObjectsReturned: get() returned more than one
            # Tag -- it returned 25!  Lookup parameters were {'text__regex':
            # u'^fran\\\xe7ais$', 'tag_type': <TagType: understands>}" Our
            # data, as you can see, is not very healthy. But I don't think it
            # will make a difference.
            matching_tags = Tag.objects.filter(
                text__regex=r"^%s$" % re.escape(tag_text),
                tag_type=tag_type)
            if matching_tags:
                tag = matching_tags[0]
            else:
                tag = Tag.objects.create(tag_type=tag_type, text=tag_text)

            new_link, _ = Link_Person_Tag.objects.get_or_create(
                tag=tag, person=person)

    posted_contact_blurb = contact_blurb_form['contact_blurb'].data or ''
    # If their new contact blurb contains $fwd, but they don't have an  email
    # address in our database, give them an error.
    if '$fwd' in posted_contact_blurb and not person.user.email:
        contact_blurb_error = True
        errors_occurred = True
    else:
        # if their new contact blurb contains $fwd and their old one didn't,
        # then make them a new forwarder
        if '$fwd' in posted_contact_blurb and not '$fwd' in person.contact_blurb:
            mysite.base.view_helpers.generate_forwarder(person.user)
        person.contact_blurb = posted_contact_blurb

    person.save()

    if errors_occurred:
        return edit_info(request,
                         edit_info_form=edit_info_form,
                         contact_blurb_form=contact_blurb_form,
                         contact_blurb_error=contact_blurb_error,
                         has_errors=errors_occurred)
    else:
        return HttpResponseRedirect(person.profile_url)

    # FIXME: This is racey. Only one of these functions should run at once.
    # }}}


@login_required
def ask_for_tag_input(request, username):
    # {{{
    return display_person_web(request, username, 'tags', edit='1')
    # }}}


def cut_list_of_people_in_three_columns(people):
    third = len(people) / 3
    return [people[0:third], people[third:(third * 2)], people[(third * 2):]]


def cut_list_of_people_in_two_columns(people):
    half = len(people) / 2
    return [people[0:half], people[half:]]


def permanent_redirect_to_people_search(request, property, value):
    '''Property is the "tag name", and "value" is the text in it.'''
    if property == 'seeking':
        property = 'can_pitch_in'

    if ' ' in value:
        escaped_value = '"' + value + '"'
    else:
        escaped_value = value

    q = '%s:%s' % (property, escaped_value)
    get_args = {u'q': q}
    destination_url = (reverse('mysite.profile.views.people') + '?' + 
                       http.urlencode(get_args))
    return HttpResponsePermanentRedirect(destination_url)


@view
def people(request):
    """Display a list of people."""
    data = {}

    # pull in q from GET
    query = request.GET.get('q', '')

    # Store the raw query in the template data
    data['raw_query'] = query

    # Parse the query, and store that in the template.
    parsed_query = mysite.profile.view_helpers.parse_string_query(query)
    data.update(parsed_query)

    # Get the list of people to display.
    if parsed_query['q'].strip():
        search_results = parsed_query['callable_searcher']()
        everybody, extra_data = search_results.people, search_results.template_data
        data.update(extra_data)
        data['people'] = everybody

        # Add JS-friendly version of people data to template
        person_id_ranges = mysite.base.view_helpers.int_list2ranges(
            [x.id for x in data['people']])
        person_ids = ''
        for stop, start in person_id_ranges:
            if stop == start:
                person_ids += '%d,' % (stop,)
            else:
                person_ids += '%d-%d,' % (stop, start)

    else:
        data = {}
    return (request, 'profile/search_people.html', data)


def gimme_json_for_portfolio(request):
    "Get JSON used to live-update the portfolio editor."
    """JSON includes:
        * The person's data.
        * DataImportAttempts.
        * other stuff"""

    # Since this view is meant to be accessed asynchronously, it doesn't make
    # much sense to decorate it with @login_required, since this will redirect
    # the user to the login page. Not much use if the browser is requesting
    # this page async'ly! So let's use a different method that explicitly warns
    # the user if they're not logged in. At time of writing, this error message
    # is NOT displayed on screen. I suppose someone will see if it they're
    # using Firebug, or accessing the page synchronously.
    if not request.user.is_authenticated():
        return HttpResponseServerError("Oops, you're not logged in.")

    person = request.user.get_profile()

    # Citations don't naturally serialize summaries.
    citations = list(Citation.untrashed.filter(portfolio_entry__person=person))
    portfolio_entries_unserialized = PortfolioEntry.objects.filter(
        person=person, is_deleted=False)
    projects_unserialized = [p.project for p in portfolio_entries_unserialized]

    # Serialize citation summaries
    summaries = {}
    for c in citations:
        summaries[c.pk] = render_to_string(
            "profile/portfolio/citation_summary.html",
            {'citation': c})

    # FIXME: Maybe we can serialize directly to Python objects.
    # fixme: zomg       don't recycle variable names for objs of diff types
    # srsly u guys!

    five_minutes_ago = datetime.datetime.utcnow() - \
        datetime.timedelta(minutes=5)
    recent_dias = DataImportAttempt.objects.filter(
        person=person, date_created__gt=five_minutes_ago)
    recent_dias_json = simplejson.loads(
        serializers.serialize('json', recent_dias))
    portfolio_entries = simplejson.loads(serializers.serialize('json',
                                                               portfolio_entries_unserialized))
    projects = simplejson.loads(
        serializers.serialize('json', projects_unserialized))
    # FIXME: Don't send like all the flippin projects down the tubes.
    citations = simplejson.loads(serializers.serialize('json', citations))

    recent_dias_that_are_completed = recent_dias.filter(completed=True)
    import_running = recent_dias.count() > 0 and (
        recent_dias_that_are_completed.count() != recent_dias.count())
    progress_percentage = 100
    if import_running:
        progress_percentage = int(
            recent_dias_that_are_completed.count() * 100.0 / recent_dias.count())
    import_data = {
        'running': import_running,
        'progress_percentage': progress_percentage,
    }

    json = simplejson.dumps({
        'dias': recent_dias_json,
        'import': import_data,
        'citations': citations,
        'portfolio_entries': portfolio_entries,
        'projects': projects,
        'summaries': summaries,
    })

    return HttpResponse(json, mimetype='application/json')


def replace_icon_with_default(request):
    "Expected postcondition: project's icon_dict says it is generic."
    """
    Expected output will look something like this:
    {
            'success': true,
            'portfolio_entry__pk': 0
    }"""
    portfolio_entry = PortfolioEntry.objects.get(
        pk=int(request.POST['portfolio_entry__pk']),
        person__user=request.user)
    # FIXME: test for naughty people trying to replace others' icons with the
    # default!
    project = portfolio_entry.project

    project_before_changes = mysite.search.models.Project.objects.get(
        pk=project.pk)

    # make a record of the old, wrong project icon in the database
    mysite.search.models.WrongIcon.spawn_from_project(project)

    try:
        wrong_icon_url = project_before_changes.icon_for_profile.url
    except ValueError:
        wrong_icon_url = "icon_url"

    # set project icon as default
    project.invalidate_all_icons()
    project.save()

    # prepare output
    data = {}
    data['success'] = True
    data['portfolio_entry__pk'] = portfolio_entry.pk
    return mysite.base.view_helpers.json_response(data)


@login_required
@csrf_exempt
def prepare_data_import_attempts_do(request):
    """
    Input: request.POST contains a list of usernames or email addresses.
    These are identifiers under which the authorized user has committed code
    to an open-source repository, or at least so says the user.

    Side-effects: Create DataImportAttempts that a user might want to execute.

    Not yet implemented: This means, don't show the user DIAs that relate to
    non-existent accounts on remote networks. And what *that* means is,
    before bothering the user, ask those networks beforehand if they even
    have accounts named identifiers[0], etc."""
    # {{{

    # For each commit identifier, prepare some DataImportAttempts.
    prepare_data_import_attempts(
        identifiers=request.POST.values(), user=request.user)

    return HttpResponse('1')
    # }}}


def prepare_data_import_attempts(identifiers, user):
    "Enqueue and track importation tasks."
    """Expected input: A list of committer identifiers, e.g.:
    ['paulproteus', 'asheesh@asheesh.org']

    For each data source, enqueue a background task.
    Keep track of information about the task in an object
    called a DataImportAttempt."""

    # Side-effects: Create DIAs that a user might want to execute.
    for identifier in identifiers:
        if identifier.strip():  # Skip blanks or whitespace
            for source_key, _ in DataImportAttempt.SOURCE_CHOICES:
                dia = DataImportAttempt(
                    query=identifier,
                    source=source_key,
                    person=user.get_profile())
                dia.save()


@login_required
@view
def importer(request, test_js=False):
    """Get the DIAs for the logged-in user's profile. Pass them to the template."""
    # {{{

    person = request.user.get_profile()
    data = get_personal_data(person)

    # This is used to create a blank 'Add another record' form, which is printed
    # to the bottom of the importer page. The HTML underlying this form is used
    # to generate forms dynamically.
    data['citation_form'] = mysite.profile.forms.ManuallyAddACitationForm(
        auto_id=False)

    # This variable is checked in base/templates/base/base.html
    data['test_js'] = test_js or request.GET.get('test', None)

    return (request, 'profile/importer.html', data)
    # }}}

# FIXME: Rename importer
portfolio_editor = importer


def portfolio_editor_test(request):
    return portfolio_editor(request, test_js=True)


def filter_by_key_prefix(dict, prefix):
    """Return those and only those items in a dictionary whose keys have the given prefix."""
    out_dict = {}
    for key, value in dict.items():
        if key.startswith(prefix):
            out_dict[key] = value
    return out_dict


@login_required
def user_selected_these_dia_checkboxes(request):
    """ Input: Request POST contains a list of checkbox IDs corresponding to DIAs.
    Side-effect: Make a note on the DIA that its affiliated person wants it.
    Output: Success?
    """
    # {{{

    prepare_data_import_attempts(request.POST, request.user)

    checkboxes = filter_by_key_prefix(request.POST, "person_wants_")
    identifiers = filter_by_key_prefix(request.POST, "identifier_")

    for checkbox_id, value in checkboxes.items():
        if value == 'on':
            x, y, identifier_index, source_key = checkbox_id.split('_')
            identifier = identifiers["identifier_%s" % identifier_index]
            if identifier:
                # FIXME: For security, ought this filter include only dias
                # associated with the logged-in user's profile?
                dia = DataImportAttempt(
                    identifier, source_key,
                    request.user.get_profile())
                dia.person_wants_data = True
                dia.save()

                # There may be data waiting or not,
                # but no matter; this function may
                # run unconditionally.
                dia.give_data_to_person()

    return HttpResponse('1')
    # }}}


@login_required
@view
def display_person_edit_name(request, name_edit_mode):
    '''Show a little edit form for first name and last name.

    Why separately handle first and last names? The Django user
    model already stores them separately.
    '''
    # {{{
    data = get_personal_data(request.user.get_profile())
    data['name_edit_mode'] = name_edit_mode
    data['editable'] = True
    return (request, 'profile/main.html', data)
    # }}}


@login_required
def display_person_edit_name_do(request):
    '''Take the new first name and last name out of the POST.

    Jam them into the Django user model.'''
    # {{{
    user = request.user

    new_first = request.POST['first_name']
    new_last = request.POST['last_name']

    user.first_name = new_first
    user.last_name = new_last
    user.save()

    return HttpResponseRedirect('/people/%s' % urllib.quote(user.username))
    # }}}


@login_required
def publish_citation_do(request):
    try:
        pk = request.POST['pk']
    except KeyError:
        return HttpResponse("0")

    try:
        c = Citation.objects.get(
            pk=pk, portfolio_entry__person__user=request.user)
    except Citation.DoesNotExist:
        return HttpResponse("0")

    c.is_published = True
    c.save()

    return HttpResponse("1")


@login_required
def delete_citation_do(request):
    try:
        pk = request.POST['citation__pk']
    except KeyError:
        return HttpResponse("0")

    try:
        c = Citation.objects.get(
            pk=pk, portfolio_entry__person__user=request.user)
    except Citation.DoesNotExist:
        return HttpResponse("0")

    c.is_deleted = True
    c.save()

    return HttpResponse("1")


@login_required
def delete_portfolio_entry_do(request):
    try:
        pk = int(request.POST['portfolio_entry__pk'])
    except KeyError:
        return mysite.base.view_helpers.json_response({'success': False})

    try:
        p = PortfolioEntry.objects.get(pk=pk, person__user=request.user)
    except PortfolioEntry.DoesNotExist:
        return mysite.base.view_helpers.json_response({'success': False})

    p.is_deleted = True
    p.save()

    return mysite.base.view_helpers.json_response({
        'success': True,
        'portfolio_entry__pk': pk})


@login_required
def save_portfolio_entry_do(request):
    pk = request.POST.get('portfolio_entry__pk', 'undefined')

    if pk == 'undefined':
        project, _ = Project.objects.get_or_create(
            name=request.POST['project_name'])
        p = PortfolioEntry(project=project, person=request.user.get_profile())
    else:
        p = PortfolioEntry.objects.get(pk=pk, person__user=request.user)
    p.project_description = request.POST['project_description']
    p.experience_description = request.POST['experience_description']
    p.receive_maintainer_updates = \
        request.POST['receive_maintainer_updates'].lower() not in (
            'false', '0')
    p.is_published = True
    p.save()

    # Publish all attached Citations
    citations = Citation.objects.filter(portfolio_entry=p)
    for c in citations:
        c.is_published = True
        c.save()

    return mysite.base.view_helpers.json_response({
        'success': True,
        'pf_entry_element_id': request.POST['pf_entry_element_id'],
        'project__pk': p.project_id,
        'portfolio_entry__pk': p.pk
    })


@login_required
def dollar_username(request):
    return HttpResponseRedirect(reverse(display_person_web,
                                        kwargs={'user_to_display__username':
                                                request.user.username}))


@login_required
def set_expand_next_steps_do(request):
    input_string = request.POST.get('value', None)
    string2value = {'True': True,
                    'False': False}
    if input_string not in string2value:
        return HttpResponseBadRequest("Bad POST.")

    person = request.user.get_profile()
    person.expand_next_steps = string2value[input_string]
    person.save()

    return HttpResponseRedirect(person.profile_url)


@login_required
@view
def edit_info(request, contact_blurb_error=False, edit_info_form=None, contact_blurb_form=None, has_errors=False):
    person = request.user.get_profile()
    data = get_personal_data(person)
    data['info_edit_mode'] = True
    if edit_info_form is None:
        edit_info_form = mysite.profile.forms.EditInfoForm(initial={
            'bio': person.bio,
            'homepage_url': person.homepage_url,
            'irc_nick': person.irc_nick,
            'understands': data['tags_flat'].get('understands', ''),
            'understands_not': data['tags_flat'].get('understands_not', ''),
            'studying': data['tags_flat'].get('studying', ''),
            'can_pitch_in': data['tags_flat'].get('can_pitch_in', ''),
            'can_mentor': data['tags_flat'].get('can_mentor', ''),
        }, prefix='edit-tags')
    if contact_blurb_form is None:
        contact_blurb_form = mysite.profile.forms.ContactBlurbForm(initial={
            'contact_blurb': person.contact_blurb,
        }, prefix='edit-tags')
    data['form'] = edit_info_form
    data['contact_blurb_form'] = contact_blurb_form
    data['contact_blurb_error'] = contact_blurb_error
    data['forwarder_sample'] = mysite.base.view_helpers.put_forwarder_in_contact_blurb_if_they_want(
        "$fwd", person.user)
    data['has_errors'] = has_errors
    return request, 'profile/info_wrapper.html', data


@login_required
def set_pfentries_dot_use_my_description_do(request):
    project = Project.objects.get(pk=request.POST['project_pk'])
    pfe_pks = project.portfolioentry_set.values_list('pk', flat=True)
    Form = mysite.profile.forms.UseDescriptionFromThisPortfolioEntryForm
    for pfe_pk in pfe_pks:
        pfe_before_save = PortfolioEntry.objects.get(pk=pfe_pk)
        form = Form(request.POST,
                    instance=pfe_before_save,
                    prefix=str(pfe_pk))
        if form.is_valid():
            pfe_after_save = form.save()
            logging.info("Project description settings edit: %s just edited a project.  The portfolioentry's data originally read as follows: %s.  Its data now read as follows: %s" % (
                request.user.get_profile(), pfe_before_save.__dict__, pfe_after_save.__dict__))
    return HttpResponseRedirect(project.get_url())


@view
def unsubscribe(request, token_string):
    context = {'unsubscribe_this_user':
               mysite.profile.models.UnsubscribeToken.whose_token_string_is_this(
                   token_string),
               'token_string': token_string}
    return (request, 'unsubscribe.html', context)


def unsubscribe_do(request):
    token_string = request.POST.get('token_string', None)
    person = mysite.profile.models.UnsubscribeToken.whose_token_string_is_this(
        token_string)
    person.email_me_re_projects = False
    person.save()
    return HttpResponseRedirect(reverse(unsubscribe, kwargs={'token_string': token_string}))

# API-y views go below here

# vim: ai ts=3 sts=4 et sw=4 nu
