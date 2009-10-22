# Imports {{{

# Python
import StringIO
import datetime
import urllib
import simplejson
import re
from odict import odict
import collections
import difflib
import os
import tempfile
import random
import Image
import urlparse

# Django
from django.template.loader import render_to_string
from django.core import serializers
from django.http import \
        HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import \
        render_to_response, get_object_or_404, get_list_or_404
import django.contrib.auth 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.images import get_image_dimensions
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

# OpenHatch global
from django.conf import settings

# OpenHatch apps
import mysite.base.controllers
from mysite.customs import ohloh
from mysite.profile.models import \
        Person, ProjectExp, \
        Tag, TagType, \
        Link_ProjectExp_Tag, Link_Project_Tag, \
        Link_SF_Proj_Dude_FM, Link_Person_Tag, \
        DataImportAttempt
from mysite.search.models import Project
from mysite.base.decorators import view

# This app
import forms
import mysite.profile.forms
# }}}

# Add a contribution {{{

def projectexp_add_do(request):
    # {{{
    form = mysite.profile.forms.ProjectExpForm(request.POST)
    username = request.user.username
    if form.is_valid():
        ProjectExp.create_from_text(
            username, project_name=form.cleaned_data['project_name'],
            description=form.cleaned_data['involvement_description'],
            url=form.cleaned_data['citation_url'])

        # FIXME: Use reverse() here to avoid quoting things ourself
        url_that_displays_project_exp = '/people/%s/projects/%s' % (
            urllib.quote(username), urllib.quote(form.cleaned_data[
                'project_name']))
        return HttpResponseRedirect(url_that_displays_project_exp)

    else:
        return projectexp_add_form(request, form)

    #}}}

# }}}

@login_required
@view
def display_person_edit_web(request, info_edit_mode=False, title=''):
    # {{{

    person = request.user.get_profile()

    data = get_personal_data(person)

    # FIXME: Django builds this in.
    data['editable'] = True
    data['info_edit_mode'] = info_edit_mode

    return (request, 'profile/main.html', data)
    # }}}

@login_required
@view
def display_person_web(request, user_to_display__username=None):
    # {{{

    user = get_object_or_404(User, username=user_to_display__username)
    person, was_created = Person.objects.get_or_create(user=user)

    data = get_personal_data(person)
    data['edit_mode'] = False
    data['editable'] = (request.user == user)
    data['notifications'] = mysite.base.controllers.get_notification_from_request(request)

    return (request, 'profile/main.html', data)

    # }}}

#FIXME: Create a separate function that just passes the data required for displaying the little user bar on the top right to the template, and leaves out all the data required for displaying the large user bar on the left.
def get_personal_data(person):
    # {{{
    project_exps = ProjectExp.objects.filter(person=person)
    projects = [project_exp.project for project_exp in project_exps]
    projects_extended = odict({})

    for project in projects:
        exps_with_this_project = ProjectExp.objects.filter(
                person=person, project=project)
        exps_with_this_project_extended = {}
        for exp in exps_with_this_project:
            tag_links = Link_ProjectExp_Tag.objects.filter(project_exp=exp)
            tags_for_this_exp = [link.tag for link in tag_links]
            exps_with_this_project_extended[exp] = {
                    'tags': tags_for_this_exp}
            tags_for_this_project = Link_Project_Tag.objects.filter(
                    project=project)
            projects_extended[project] = {
                    'tags': tags_for_this_project,
                    'experiences': exps_with_this_project_extended}

            # projects_extended now looks like this:
    # {
    #   Project: {
    #       'tags': [Tag, Tag, ...],
    #       'experiences': {
    #               ProjectExp: [Tag, Tag, ...],
    #               ProjectExp: [Tag, Tag, ...],
    #               ...
    #           }
    #   },
    #   Project: {
    #       'tags': [Tag, Tag, ...],
    #       'experiences': {
    #               ProjectExp: [Tag, Tag, ...],
    #               ProjectExp: [Tag, Tag, ...],
    #               ...
    #           }
    #   }
    # }

    # Asheesh's evil hack
    for exp in project_exps:
        links = Link_ProjectExp_Tag.objects.filter(project_exp=exp)
        for link in links:
            if link.favorite:
                link.tag.prefix = 'Favorite: ' # FIXME: evil hack, will fix later
            else:
                link.tag.prefix = ''

    interested_in_working_on_list = re.split(r', ', person.interested_in_working_on)

    try:
        photo_url = person.photo.url
    except ValueError:
        photo_url = '/static/images/profile-photos/penguin.png'

    # FIXME: Make this more readable.
    data_dict = {
            'person': person,
            'photo_url': photo_url,
            'interested_in_working_on_list': interested_in_working_on_list, 
            'projects': projects_extended,
            } 
    data_dict['tags'] = tags_dict_for_person(person)
    data_dict['tags_flat'] = dict(
        [ (key, ', '.join([k.text for k in data_dict['tags'][key]]))
          for key in data_dict['tags'] ])

    data_dict['has_set_info'] = any(data_dict['tags_flat'].values())

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

@login_required
@view
def projectexp_display(request, user_to_display__username, project__name):
    # {{{
    user = get_object_or_404(User, username=user_to_display__username)
    person = get_object_or_404(Person, user=user)
    project = get_object_or_404(Project, name=project__name)

    data = get_personal_data(person)
    data['project'] = project
    data['exp_list'] = get_list_or_404(ProjectExp,
            person=person, project=project)
    data['projectexp_editable'] = (user == request.user)
    data['editable'] = (user == request.user)
    return (request, 'profile/projectexp.html', data)
    # }}}
    
def widget_display_undecorated(request, user_to_display__username):
    """We leave this function unwrapped by @view """
    """so it can referenced by widget_display_string."""
    # {{{
    user = get_object_or_404(User, username=user_to_display__username)
    person = get_object_or_404(Person, user=user)

    data = {}
    data['projectexp_editable'] = (user == request.user)
    data['editable'] = (user == request.user)
    data['url_prefix'] = request.META['SERVER_NAME'] + ':' + request.META['SERVER_PORT']
    return (request, 'profile/widget.html', data)
    # }}}

widget_display = view(widget_display_undecorated)

def widget_display_string(request, user_to_display__username):
    request, template, data = widget_display_undecorated(request, user_to_display__username)
    return render_to_string(template, data)

def widget_display_js(request, user_to_display__username):
    # FIXME: In the future, use:
    html_doc = widget_display_string(request, user_to_display__username)
    # to generate html_doc
    encoded_for_js = simplejson.dumps(html_doc)
    # Note: using application/javascript as suggested by
    # http://www.ietf.org/rfc/rfc4329.txt
    return render_to_response('base/append_ourselves.js',
                              {'in_string': encoded_for_js},
                              mimetype='application/javascript')

def prepare_p_e_forms(person, project):
    """Input: a person and a project.
    Output: A list of ProjectExpForms populated from that guy's relevant p_es."""
    # Let's prepare some forms
    forms = []
    
    # We need a form for each of the user's experiences with a given project.
    project_exps = ProjectExp.objects.filter(
        project=project,
        person=person)
    
    for n, p_e in enumerate(project_exps):
        form_data = dict(
            project_exp_id=p_e.id,
            citation_url=p_e.url,
            man_months=p_e.man_months,
            primary_language=p_e.primary_language,
            involvement_description=p_e.description,
            )
        forms.append(mysite.profile.forms.ProjectExpEditForm(initial=form_data, prefix=str(n)))
    return forms

@login_required
@view
def projectexp_edit(request, project__name, forms = None):
    """Page that allows user to edit project experiences for a project."""
    # {{{
    # FIXME: Change this function's misleading name.

    project = get_object_or_404(Project, name=project__name)
    person = request.user.get_profile()

    if forms is None:
        forms = prepare_p_e_forms(person, project)
        
    data = get_personal_data(person)
    data['exp_list'] = get_list_or_404(ProjectExp,
            person=person, project=project)
    data['forms'] = forms
    data['edit_mode'] = True
    data['project__name'] = project__name
    data['editable'] = True
    return (request, 'profile/projectexp_edit.html', data)
    # }}}

@login_required
def projectexp_edit_do(request, project__name):
    """Update database with new information about a user's experiences with a particular project."""
    # FIXME: Change this function's misleading name.
    # {{{
    project = get_object_or_404(Project, name=project__name)

    # Find all the unique strings before a hyphen and convert them to integers.
    numbers = sorted(map(int, set([k.split('-')[0] for k in request.POST.keys()])))
    forms = []

    forms_all_valid = True
    
    for n in numbers:
        form = mysite.profile.forms.ProjectExpEditForm(
            request.POST, prefix=str(n))
        form.set_user(request.user)
        
        if form.data.get('%d-delete_this' % n, None) == 'on':
            # FIXME: This is duplicate code, duplicate code.

            # this way, if there are no matches, we fail gently.
            # Presumably a crazy-reloading user might run into that,
            # so it's probably be best to allow ourselves to "redelete"
            # a ProjectExp that has already been deleted.
            exps = ProjectExp.objects.filter(
                    id=int(form.data['%d-project_exp_id' % n]),
                    person__user=request.user)

            for exp in exps:
                exp.delete()

            continue

        forms.append(form) # append it in case we
        # will need to push it onto the edit page later

        if form.is_valid():
            p_e = form.cleaned_data['project_exp']
            p_e.modified = True
            p_e.description = form.cleaned_data['involvement_description']
            p_e.url = form.cleaned_data['citation_url']
            p_e.man_months = form.cleaned_data['man_months']
            p_e.primary_language=form.cleaned_data['primary_language']
            p_e.save()
        else:
            forms_all_valid = False

    if not forms_all_valid:
        # Return the original view, with the forms populated with
        # the data the user entered (even though that data isn't valid).
        return projectexp_edit(request, project__name, forms)

    # Are there any left?
    any_left = ProjectExp.objects.filter(
        project=project, person=request.user.get_profile()
        ).count()
    if any_left:
        # If so, send the user back to the
        # projectexp edit page.
        outta_here = reverse(projectexp_edit, kwargs={'project__name': project__name})
    else:
        # if not, back to profile.
        outta_here = reverse(display_person_web, kwargs=dict(
            user_to_display__username=request.user.username))

    return HttpResponseRedirect(outta_here)
    # }}}

@login_required
@view
def projectexp_add_form(request, form = None):
    # {{{
    if form is None:
        form = mysite.profile.forms.ProjectExpForm()

    person = request.user.get_profile()
    data = get_personal_data(person)
    data['form'] = form
    
    return (request, 'profile/projectexp_add.html', data)
    # }}}

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

def import_debtags(cooked_string = None):
    # {{{
    if cooked_string is None:
        # Warning: this re-downloads the list from Alioth every time this
        # is called
        import urllib2
        import gzip
        fd = urllib2.urlopen('http://debtags.alioth.debian.org/tags/tags-current.gz')
        gzipped_sio = StringIO.StringIO(fd.read()) # this sucks, but I
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

# FIXME: rename to project_exp_tag__add__web
#def add_tag_to_project_exp_web(request):

# FIXME: rename to project_exp_tag__add
#def add_tag_to_project_exp(username, project_name,
#        tag_text, tag_type_name='user_generated'):

#def project_exp_tag__remove(username, project_name,
#        tag_text, tag_type_name='user_generated'):

#def project_exp_tag__remove__web(request):

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

def project_icon_url(project_name, width = None, actually_fetch = True):
    # {{{
    project_hash = _project_hash(project_name)

    # First, do it all with relative links.
    relative_root ='project-icons'
    # If we specify a width, put that into the path too.
    if width is not None:
        relative_root = os.path.join(relative_root, 'w=%d' % width)

    # where should the image exist?
    relative_path = os.path.join(relative_root, project_hash + '.png')


    path = os.path.join(settings.MEDIA_ROOT, relative_path)
    url  = urlparse.urljoin(settings.MEDIA_URL, relative_path)

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    if actually_fetch:
        # Then verify the image exists
        if not os.path.exists(path):
            # See if Ohloh will give us an icon
            oh = ohloh.get_ohloh()
            try:
                icon_data = oh.get_icon_for_project(project_name)
            except ValueError:
                icon_data = open(os.path.join(
                        settings.MEDIA_ROOT,
                        'no-project-icon.png')).read()

            if width is not None:
                # scale it
                icon_fd = StringIO.StringIO(icon_data)
                im = Image.open(icon_fd)
                icon_fd.seek(0)

                w, h = get_image_dimensions(icon_fd)

                new_w = width
                new_h = (h * 1.0 / w) * width

                smaller = im.resize((new_w, new_h),
                                    Image.ANTIALIAS)

                # "Save" it to memory
                new_image_fd = StringIO.StringIO()
                smaller.save(new_image_fd, format='PNG')
                new_image_fd.seek(0)

                # pull data out
                icon_data = new_image_fd.getvalue()
        
            # then mktemp and save the Ohloh icon there, and rename it in
            tmp = tempfile.mkstemp(dir=os.path.dirname(path))
            fd = open(tmp[1], 'w')
            fd.write(icon_data)
            fd.close()
            os.rename(tmp[1], path)
            os.chmod(path, 0644)

    return path, url
    # FIXME: One day, add cache expiry.
    # }}}

@login_required
def edit_person_info(request):
    # {{{
    person = request.user.get_profile()

    # We can map from some strings to some TagTypes
    for known_tag_type_name in ('understands', 'understands_not',
                           'studying', 'seeking', 'can_mentor'):
        tag_type, _ = TagType.objects.get_or_create(name=known_tag_type_name)

        text = request.POST.get('edit-tags-' + known_tag_type_name, '')
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
            new_tag, _ = Tag.objects.get_or_create(
                    tag_type=tag_type, text=tag_text)
            new_link, _ = Link_Person_Tag.objects.get_or_create(
                    tag=new_tag, person=person)
            
    return HttpResponseRedirect('/people/%s/' %
                                urllib.quote(request.user.username))

    # FIXME: This is racey. Only one of these functions should run at once.
    # }}}

def project_icon_web(request, project_name, width = None):
    # {{{
    path, url = project_icon_url(project_name, width)
    return HttpResponseRedirect(url)
    # }}}

def import_commits_by_commit_username(request):
    # {{{

    commit_username = request.POST.get('commit_username', None)

    if not commit_username:
        fail

    nobgtask_s = request.GET.get('nobgtask', False)

    involved_projects = []
    
    try:
        nobgtask = bool(nobgtask_s)
    except ValueError:
        nobgtask = False
    
    # get the person
    person = request.user.get_profile()

    # Find the existing ProjectExps
    project_exps = ProjectExp.objects.filter(person=person)
    involved_projects.extend([exp.project.name for exp in project_exps])

    # if we are allowed to make bgtasks, create background tasks
    # to pull in this user's data (just the one huge one)
    do_it = True # unless...

    if nobgtask:
        do_it = False

    if do_it:
        username= request.user.username
        import tasks 
        # say we're trying
        dia = DataImportAttempt(source='rs', person=person,
                                query=commit_username)
        dia.save()

        result = tasks.FetchPersonDataFromOhloh.delay(dia.id)
    # }}}

def ohloh_contributor_facts_to_project_exps(dia_id,
                                     ohloh_results):
    # {{{
    '''Input: A sequence of Ohloh ContributorInfo dicts
    and the id of the DataImport they came from.

    Side-effect: Create matching structures in the DB
    and mark our success in the database.'''
    dia = DataImportAttempt.objects.get(id=dia_id)
    person = dia.person
    for c_i in ohloh_results:
        for ohloh_contrib_info in ohloh_results:
            exp = ProjectExp()
            exp = exp.from_ohloh_contrib_info(ohloh_contrib_info)
            exp.last_polled = datetime.datetime.now()
            exp.last_touched = datetime.datetime.now()
            exp.data_import_attempt = dia
            exp.save()
    person.last_polled = datetime.datetime.now()
    dia.completed = True
    dia.save()
    person.save()

    if dia.person_wants_data:
        dia.give_data_to_person()
    # }}}

def create_project_exps_from_launchpad_contributor_facts(dia_id, lp_results):
    # {{{
    '''Input: A sequence of Ohloh ContributorInfo dicts
    and the id of the DataImport they came from.

    Side-effect: Create matching structures in the DB
    and mark our success in the database.'''
    dia = DataImportAttempt.objects.get(id=dia_id)
    person = dia.person
    # lp_results looks like this:
    # 
    # It returns a dictionary like this:
    #     {
    #         'F-Spot': {
    #             'url': 'http://launchpad.net/f-spot',
    #             'involvement_types': ['Bug Management', 'Bazaar Branches'],
    #             'languages': ['python', 'ruby'],
    #         }
    #     }
    for project_name in lp_results:
        result = lp_results[project_name]
        for involvement_type in result['involvement_types']:
            person_role = involvement_type
            exp = ProjectExp()
            if result['languages']:
                primary_language = result['languages'][0]
            else:
                primary_language = None
            exp = exp.from_launchpad_result(project_name, primary_language, person_role)
            exp.last_polled = datetime.datetime.now()
            exp.last_touched = datetime.datetime.now()
            exp.data_import_attempt = dia
            exp.save()
    person.last_polled = datetime.datetime.now()
    dia.completed = True
    dia.save()
    person.save()

    if dia.person_wants_data:
        dia.give_data_to_person()

    # }}}

@login_required
def ask_for_tag_input(request, username):
    # {{{
    return display_person_web(request, username, 'tags', edit='1')
    # }}}

@login_required
@view
def display_list_of_people(request):
    """Display a list of people."""
    # {{{
    data = {}
    data['people'] = Person.objects.all().order_by('user__username')
    return (request, 'profile/search_people.html', data)
    # }}}

def gimme_json_that_says_that_commit_importer_is_done(request):
    '''This web controller is called when you want JSON that tells you 
    if the background jobs for the logged-in user have finished.

    It has no side-effects.'''
    # {{{
    person = request.user.get_profile()
    dias = get_list_or_404(DataImportAttempt, person=person)
    non_stale_dias =  [ d for d in dias if not d.stale]
    json = serializers.serialize('json', non_stale_dias)

    # look at me, evil side effect
    if all([d.completed for d in non_stale_dias]):
        for dia in non_stale_dias:
            dia.stale = True
            dia.save()
    
    return HttpResponse(json)
    # }}}

@login_required
def import_do(request):
    # {{{
    # This is POSTed to when you want to start
    # a background job that gets some data from Ohloh.

    # So naturally we should create that job:
    import_commits_by_commit_username(request)

    # and then just redirect to the profile page
    return HttpResponseRedirect('/people/%s' % urllib.quote(
            request.user.username))
    # }}}

@login_required
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
    # for each commit_username_*, call some silly controller """
    prepare_data_import_attempts(request.POST, request.user)

    if request.POST.get('format', None) == 'success_code':
        return HttpResponse('1')
    else:
        return HttpResponseRedirect('/people/portfolio/import/')
    # }}}

def prepare_data_import_attempts(post, user):
    identifiers = []
    for key in post:
        if key.startswith('identifier_'):
            value = post[key].strip()
            if not value:
                continue # Skip blanks
            identifiers.append(value)

    # Side-effects: Create DIAs that a user might want to execute.
    for identifier in identifiers:
        if identifier:
            for source_key, _ in DataImportAttempt.SOURCE_CHOICES:
                # FIXME: "...that a user might want to execute" means,
                # don't show the user DIAs that relate to non-existent
                # accounts on remote networks.
                # And what *that* means is, before bothering the user,
                # ask those networks beforehand if they even have
                # accounts named commit_usernames[0], etc.
                dia = get_most_recent_data_import_attempt_or_create(
                        query=identifier,
                        source=source_key,
                        person=user.get_profile())

@login_required
@view
def importer(request):
    """Get the DIAs for the logged-in user's profile. Pass them to the template."""
    # {{{

    blank_query_index = 0
    checkboxes = []
    for source_key, source_display in DataImportAttempt.SOURCE_CHOICES:
        checkboxes.append({
            'id': "%s%d" % (source_key, blank_query_index),
            'label': source_display,
            })
    blank_query = {
            'index': blank_query_index,
            'checkboxes': checkboxes
            }
    person = request.user.get_profile()
    data = get_personal_data(person)
    data['dias'] = DataImportAttempt.objects.filter(person=person, stale=False).order_by('id')
    data['blank_query'] = blank_query

    return (request, 'profile/importer.html', data)
    # }}}

def filter_by_key_prefix(dict, prefix):
    """Return those and only those items in a dictionary whose keys have the given prefix."""
    out_dict = {}
    for key, value in dict.items():
        if key.startswith(prefix):
            out_dict[key] = value
    return out_dict

def get_most_recent_data_import_attempt_or_create(query, source, person):
    """NOTE: This is a bit weird, so let me explain it.
    
    Here are three different use cases:

    1. Someone did an import of a new username. This case is
       easy. The DIA is created the first time this function
       is called, and it is the one reflected by the checkmarks
       or clouds.

    2. Someone did an import of a username one week ago, and
       they are re-doing it right now. The DIA in the past
       failed or otherwise returned nothing; that's the reason
       to run it again.

    3. ...?
    """
    dias = DataImportAttempt.objects.filter(
            query=query, source=source, stale=False,
            person=person).order_by("-pk")
    if not dias:
        dia = DataImportAttempt(
                query=query,
                source=source,
                stale=False,
                person=person)
        dia.save()
        dia.do_what_it_says_on_the_tin()
        return dia
    else:
        return dias[0]

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
                dia = get_most_recent_data_import_attempt_or_create(
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

def people_matching(property, value):
    links = Link_Person_Tag.objects.filter(tag__tag_type__name=property, tag__text__iexact=value)
    peeps = [l.person for l in links]
    sorted_peeps = sorted(set(peeps), key = lambda thing: (thing.user.first_name, thing.user.last_name))
    return sorted_peeps

@login_required
@view
def display_list_of_people_who_match_some_search(request, property, value):
    '''Property is the "tag name", and "value" is the text in it.'''
    peeps = people_matching(property, value)
    data = {}
    data['people'] = peeps
    data['property'] = property
    data['value'] = value
    return (request, 'profile/search_people.html', data)

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

# vim: ai ts=3 sts=4 et sw=4 nu
