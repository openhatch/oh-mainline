# vim: ai ts=3 sts=4 et sw=4 nu

# Imports {{{
import settings
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag, DataImportAttempt
from mysite.search.models import Project
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
import django.contrib.auth 
from django.contrib.auth.models import User
from customs import ohloh
import forms
from django.contrib.auth.decorators import login_required
# }}}

# Add a contribution {{{

def projectexp_add_do(request):
    # {{{
    project_name = request.POST['project__name']
    description = request.POST.get('project_exp__description', '')
    url = request.POST.get('project_exp__url', '')
    format = request.POST.get('format', 'html')

    username = request.user.username
    notification = ''
    if project_name and description and url:
        ProjectExp.create_from_text(
                username, project_name,
                description, url)
        notification = "Added %s's experience with %s." % (
                username, project_name)
    else:
        notification = "Unexpectedly imperfect input: {username: %s, project_name: %s}" % (
                username, project_name)
        if format == 'json':
            dictionary = {'notification': notification}
            return HttpResponse(simplejson.dumps([dictionary]))

    url_that_displays_project_exp = '/people/%s/projects/%s' % (
            urllib.quote(username), urllib.quote(project_name))
    return HttpResponseRedirect(url_that_displays_project_exp)
    #}}}

# }}}

def profile_data_from_username(username):
    # {{{
    person = Person.objects.get(
            user__username=username)

    project_exps = ProjectExp.objects.filter(
            person=person)

    exps_to_tags = {}
    for exp in project_exps:
        tag_links = Link_ProjectExp_Tag.objects.filter(project_exp=exp)
        for link in tag_links:
            if link.favorite:
                link.tag.prefix = 'Favorite: ' # FIXME: evil hack, will fix later
            else:
                link.tag.prefix = ''
        exps_to_tags[exp] = [link.tag for link in tag_links]

    # {
    #   Experience1:
    #   ["awesome", "fun", "illuminating", "helped_me_get_laid"],
    # }

    exp_taglist_pairs = exps_to_tags.items()

    interested_in_working_on_list = re.split(r', ',person.interested_in_working_on)

    return {
            'person': person,
            'interested_in_working_on_list': interested_in_working_on_list, 
            'exp_taglist_pairs': exp_taglist_pairs } 
    # }}}

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

    # Tell person templates about

    photos_url_prefix = '/static/images/profile-photos/'
    photos = ['collins.jpg', 'sufjan.jpg', 'iris.jpg', 'selleck.jpg']
    photo_url = photos_url_prefix + photos[random.randint(0, len(photos)-1)]
    photo_url = photos_url_prefix + photos[1]

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

@login_required
def display_person_edit_web(request, info_edit_mode=False, title=''):
    # {{{

    person = request.user.get_profile()

    data = get_personal_data(person)

    # FIXME: Django builds this in.
    data['the_user'] = request.user
    data['editable'] = True
    data['info_edit_mode'] = info_edit_mode

    return render_to_response('profile/main.html', data)
    # }}}

def display_person_web(request, user_to_display__username=None):
    # {{{
    user = User.objects.get(username=user_to_display__username)
    person = user.get_profile()

    data = get_personal_data(person)

    data['the_user'] = request.user
    data['title'] = 'openhatch / %s' % user.username
    data['edit_mode'] = False
    data['editable'] = (request.user == user)

    return render_to_response('profile/main.html', data)

    # }}}

def projectexp_display(request, user_to_display__username, project__name):
    # {{{
    user = get_object_or_404(User, username=user_to_display__username)
    person = get_object_or_404(Person, user=user)
    project = get_object_or_404(Project, name=project__name)
    data = get_personal_data(person)
    data['project'] = project
    data['exp_list'] = get_list_or_404(ProjectExp,
            person=person, project=project)
    data['title'] = "%s's contributions to %s" % (
            user.username, project.name)
    data['the_user'] = request.user
    data['projectexp_editable'] = (user == request.user)
    return render_to_response('profile/projectexp.html', data)
    # }}}

@login_required
def projectexp_edit(request, project__name):
    # {{{
    person = request.user.get_profile()
    project = get_object_or_404(Project, name=project__name)
    data = get_personal_data(person)
    data['exp_list'] = get_list_or_404(ProjectExp,
            person=person, project=project)
    data['form'] = forms.ProjectExpForm()
    data['edit_mode'] = True
    data['title'] = "Edit your contributions to %s" % project.name
    data['the_user'] = request.user
    return render_to_response('profile/projectexp.html', data)
    # }}}

@login_required
def projectexp_add_form(request):
    # {{{
    try:
        person = request.user.get_profile()
    except AttributeError:
        return render_to_response('search/index.html', {
            'notification': "You've gotta be logged in to do that! (Coming soon: a slightly easier way to get back to where you were.)"
            })
    data = get_personal_data(person)
    data['the_user'] = request.user
    data['title'] = "Log a contribution in your portfolio | OpenHatch"
    return render_to_response('profile/projectexp_add.html', data)
    # }}}

def tags_dict_for_person(person):
    # {{{
    ret = collections.defaultdict(list)
    links = Link_Person_Tag.objects.filter(person=person).order_by('id')
    for link in links:
        ret[link.tag.tag_type.name].append(link.tag)

    return ret
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

def project_icon_url(project_name, actually_fetch = True):
    # {{{
    project_hash = _project_hash(project_name)
    # Check for static path for project icons
    project_icons_root = os.path.join('static', 'project-icons')
    # If no such directory exists, make it
    if not os.path.exists(project_icons_root):
        os.makedirs(project_icons_root)

    # where should the image exist?
    project_icon_path = os.path.join(project_icons_root, project_hash + '.png')

    if actually_fetch:
        # Then verify the image exists
        if not os.path.exists(project_icon_path):
            # See if Ohloh will give us an icon
            oh = ohloh.get_ohloh()
            try:
                icon_data = oh.get_icon_for_project(project_name)
            except ValueError:
                icon_data = open('static/no-project-icon.png').read()
        
            # then mktemp and save the Ohloh icon there, and rename it in
            tmp = tempfile.mkstemp(dir=project_icons_root)
            fd = open(tmp[1], 'w')
            fd.write(icon_data)
            fd.close()
            os.rename(tmp[1], project_icon_path)

    return '/' + project_icon_path
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

def project_icon_web(request, project_name):
    # {{{
    url = project_icon_url(project_name)
    return HttpResponseRedirect(url)
    # }}}

# FIXME: This method is dead
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

#def make_favorite_project_exp(exp_id_obj):

#def make_favorite_project_exp_web(request):

#def make_favorite_tag(exp_id_obj, tag_text):

#def make_favorite_exp_tag_web(request):

#def edit_exp_tag(request, exp_id):

def display_list_of_people(request):
    # {{{
    return render_to_response('profile/search_people.html', {
        'title': 'List of people : OpenHatch',
        'people': Person.objects.all().order_by('user__username')
        })
    # }}}

def login_do(request):
    #{{{
    try:
        username = request.POST['login_username']
        password = request.POST['login_password']
    except KeyError:
        return HttpResponseServerError("Missing username or password.")
    user = django.contrib.auth.authenticate(
            username=username, password=password)
    if user is not None:
        django.contrib.auth.login(request, user)
        return HttpResponseRedirect('/people/%s' % urllib.quote(username))
    else:
        return HttpResponseRedirect('/people/login/?msg=oops')
    #}}}

def login(request):
    #{{{
    notification = notification_id = None
    if request.GET.get('msg', None) == 'oops':
        notification_id = "oops"
        notification = "Couldn't find that pair of username and password. "
        notification += "Did you type your password correctly?"
    if request.GET.get('next', None) is not None:
        notification_id = "next"
        notification = "You've got to be logged in to do that!"
    return render_to_response('profile/login.html', {
        'notification_id': notification_id,
        'notification': notification,
        } )
    #}}}

def logout(request):
    #{{{
    django.contrib.auth.logout(request)
    return HttpResponseRedirect("/?msg=ciao#tab=login")
    #}}}

def signup(request):
    #{{{
    return render_to_response("profile/signup.html", {'user': request.user} )
    #}}}

def signup_do(request):
    # {{{
    password_raw = request.POST.get('login-password', None)
    if password_raw:
        request.user.set_password(password_raw)
        request.user.save()

        # From <http://docs.djangoproject.com/en/1.0/topics/auth/#storing-additional-information-about-users>
        # The method get_profile() does not create the profile, if it does not exist.
        # You need to register a handler for the signal django.db.models.signals.post_save
        # on the User model, and, in the handler, if created=True, create the associated user profile.

        #FIXME: Catch bad (e.g., blank) passwords.
    else:
        fail
    return HttpResponseRedirect("/people/%s" % urllib.quote(request.user.username))
    # }}}

def gimme_json_that_says_that_commit_importer_is_done(request):
    ''' This web controller is called when you want JSON that tells you 
    if the background jobs for the logged-in user have finished.

    It has no side-effects.'''
    # {{{
    person = request.user.get_profile()
    dias = get_list_or_404(DataImportAttempt, person=person)
    json = serializers.serialize('json', dias)
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

def new_user_do(request):
# {{{
    username = request.POST.get('create_profile_username', None)
    password = request.POST.get('create_profile_password', None)
    if username and password:
        # create a user
        user, created = User.objects.get_or_create(username=username)
        if not created:
            # eep, redirect back to the front page with a message
            return HttpResponseRedirect('/?msg=username_taken#tab=create_profile')
        
        # Good, set the user's parameters.
        user.email=''
        user.set_password(password)
        user.save()
        
        # create a linked person
        person = Person(user=user)
        person.save()

        # authenticate and login
        user = django.contrib.auth.authenticate(
                username=username, password=password)
        django.contrib.auth.login(request, user)

        # redirect to profile
        return HttpResponseRedirect('/people/%s/' % urllib.quote(username))
    else:
        fail
        # FIXME: Validate, Catch no username
    # }}}

@login_required
def delete_experience_do(request):
    # {{{
    person = request.user.get_profile()

    try:
        project_exp_id = int(request.POST['id'])
    except KeyError:
        error_msg = "Oops, an error occurred."
        return HttpResponseServerError(error_msg)
    
    exps = ProjectExp.objects.filter(id=project_exp_id,
                                    person=person)

    # this way, if there are no matches, we fail gently.
    # Presumably a crazy-reloading user might run into that,
    # so it's probably be best to allow ourselves to "redelete"
    # a ProjectExp that has already been deleted.
    for exp in exps:
        exp.delete()

    return HttpResponseRedirect('/people/%s/' % urllib.quote(
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
    have accounts named commit_usernames[0], etc."""
    # {{{
    # for each commit_username_*, call some silly controller """
    commit_usernames = []
    for key in request.POST:
        if key.startswith('commit_username_'):
            value = request.POST[key].strip()
            if not value:
                continue # Skip blanks
            commit_usernames.append(value)

    # Side-effects: Create DIAs that a user might want to execute.
    for cu in commit_usernames:
        for source_key, _ in DataImportAttempt.SOURCE_CHOICES:
            # FIXME: "...that a user might want to execute" means,
            # don't show the user DIAs that relate to non-existent
            # accounts on remote networks.
            # And what *that* means is, before bothering the user,
            # ask those networks beforehand if they even have
            # accounts named commit_usernames[0], etc.
            dia = DataImportAttempt(source=source_key,
                    person=request.user.get_profile(), query=cu)
            dia.save()
            dia.do_what_it_says_on_the_tin()

    return HttpResponseRedirect('/people/portfolio/import/')
    # }}}

@login_required
def importer(request):
    """Get the DIAs for the logged-in user's profile. Pass them to the template."""
    # {{{

    data = get_personal_data(request.user.get_profile())
    data.update({
        'title': 'Find your contributions around the web! - OpenHatch',
        'the_user': request.user,
        'body_id': 'importer-body',
        'dias': DataImportAttempt.objects.filter(person=request.user.get_profile()).order_by('id')
        })

    return render_to_response('profile/importer.html', data)
    # }}}

@login_required
def user_selected_these_dia_checkboxes(request):
    """ Input: Request POST contains a list of checkbox IDs corresponding to DIAs.
    Side-effect: Make a note on the DIA that its affiliated person wants it.
    Output: Success?
    """
    # {{{
    try:
        checkbox_ids = request.POST['checkboxIDs']
    except KeyError:
        return HttpResponseServerError('0')

    for checkbox_id in checkbox_ids.split(" "):
        dia_id = int(checkbox_id.rsplit('_', 1)[1])
        dia = DataImportAttempt.objects.get(id=dia_id)
        dia.person_wants_data = True
        dia.save()

        # There may or may not be data waiting,
        # but this function may run unconditionally.
        dia.give_data_to_person()

    return HttpResponse('1')
    # }}}

@login_required
def display_person_edit_name(request, name_edit_mode):
    '''Show a little edit form for first name and last name.

    Why separately handle first and last names? The Django user
    model already stores them separately.
    '''
    # {{{
    data = {}
    data = get_personal_data(
            request.user.get_profile())
    data['name_edit_mode'] = name_edit_mode
    data['editable'] = True
    return render_to_response('profile/main.html', data)
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
def my_account(request):
    data = get_personal_data(
            request.user.get_profile())
    data['the_user'] = request.user
    return render_to_response('profile/edit-self.html',
                              data)
