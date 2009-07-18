# vim: ai ts=3 sts=4 et sw=4 nu

# Imports {{{
import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag
from mysite.search.models import Project
import profile.controllers
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

    data = profile_data_from_username(username)
    data['notification'] = notification

    url_that_displays_project_exp = '/people/%s/projects/%s/' % (
            urllib.quote(username), urllib.quote(project_name))
    return HttpResponseRedirect(url_that_displays_project_exp)
    #}}}

# }}}

# XP slurper {{{

def display_test_page_for_commit_importer(request, input_username):
    # {{{
    return render_to_response('profile/test_commit_importer.html', {
        'username': input_username})
    # }}}

# }}}

# Display profile {{{
def profile_data_from_username(username, fetch_ohloh_data = False):
    # {{{
    person = Person.objects.get(
            user__username=username)

    project_exps = ProjectExp.objects.filter(
            person=person)

    if fetch_ohloh_data and person.poll_on_next_web_view:
        person.fetch_contrib_data_from_ohloh()
        person.poll_on_next_web_view = False
        person.save()

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

def data_for_person_display_without_ohloh(person):
    "This replaces profile_data_from_username"
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

    return data_dict

    # }}}

def display_person_edit_web(request, input_username=None, tab=None):
    # {{{
    return display_person_web(request, input_username, tab, True)
    # }}}

def display_person_web(request, input_username=None, tab=None, edit=None):
    # {{{
    if input_username is None:
        input_username = request.GET.get('u', None)
        if input_username is None:
            return render_to_response('profile/profile.html')

    if edit is None:
        edit = False
        if request.GET.get('edit', 0) == '1':
            edit = True

    if tab is None:
        tab = request.GET.get('tab', None)

    user = django.contrib.auth.models.User.objects.get(username=input_username)

    return display_person(user, request.user, tab, edit)
    # }}}

def projectexp_display(request, user_to_display__username, project__name):
    # {{{
    person = get_object_or_404(Person, user__username=user_to_display__username)
    data = data_for_person_display_without_ohloh(person)
    data['project'] = get_object_or_404(Project, name=project__name)
    data['exp'] = get_object_or_404(ProjectExp,
            person__user__username=user_to_display__username, project__name=project__name)
    return render_to_response('profile/projectexp.html', data)
    # }}}

def projectexp_edit(request, user_to_display__username, project__name):
    # {{{
    person = get_object_or_404(Person, user__username=user_to_display__username)
    data = data_for_person_display_without_ohloh(person)
    data['exp'] = get_object_or_404( ProjectExp,
            person__user__username=user_to_display__username,
            project__name=project__name)
    data['form'] = forms.ProjectExpForm()
    data['edit_mode'] = True
    return render_to_response('profile/projectexp.html', data)
    # }}}

def projectexp_add_form(request):
    person = request.user.get_profile()
    data = data_for_person_display_without_ohloh(person)
    return render_to_response('profile/projectexp_add.html', data)

def display_person(user, logged_in_user, tab, edit):
    # {{{

    person = user.get_profile()

    data_dict = data_for_person_display_without_ohloh(person)

    data_dict['edit'] = edit
    data_dict['the_user'] = user

    title = 'openhatch / %s' % user.username
    title += ' %s'
    if tab == 'inv' or tab == '/ involvement':
        data_dict['title'] = title % "community involvement"
        return render_to_response('profile/participation.html', data_dict)
    if tab == 'tags':
        data_dict['title'] = title % "/ tags"
        return render_to_response('profile/tags.html', data_dict)
    if tab == 'tech':
        data_dict['title'] = title % "/ tech"
        return render_to_response('profile/tech.html', data_dict)
    else:
        data_dict['title'] = title % ""
        #Don't use a short list, for now, since we don't have that much stuff on this page.
        #data_dict['projects'] = dict(data_dict['projects'].items()[:4])
        data_dict['tags'] = tags_dict_for_person(person)
        data_dict['tags_flat'] = dict(
            [ (key, ', '.join([k.text for k in data_dict['tags'][key]]))
              for key in data_dict['tags'] ])
        return render_to_response('profile/main.html', data_dict)

    # }}}

def tags_dict_for_person(person):
    # {{{
    ret = collections.defaultdict(list)
    links = Link_Person_Tag.objects.filter(person=person)
    for link in links:
        ret[link.tag.tag_type.name].append(link.tag)

    return ret
    # }}}

def display_person_old(request, input_username=None):
    # {{{
    if input_username is None:
        input_username = request.GET.get('u', None)
        if input_username is None:
            return render_to_response('profile/profile.html')

    data_dict = profile_data_from_username(input_username, fetch_ohloh_data = True)

    return render_to_response('profile/profile.html', data_dict)
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

def get_data_for_email(request):
    # {{{
    # FIXME: Hard-coded username
    email = request.POST.get('email', '')
    username=email
    if email:
        oh = ohloh.get_ohloh()
        from_ohloh = oh.get_contribution_info_by_email(email)
        for data in from_ohloh:
            person, created = Person.objects.get_or_create(
                    user__username=username)
            # FIXME: Later we'll have to be
            # able to merge user objects
            pe = ProjectExp(person=person)
            pe.from_ohloh_contrib_info(data)
            pe.save()
    request_GET = {'u': username}
    query_str = "?" + urllib.urlencode(request_GET)
    return HttpResponseRedirect('/people/%s' % query_str)
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

def sf_projects_by_person_web(request):
    # {{{
    sf_username = request.GET.get('u', None)
    if sf_username is None:
        return HttpResponseServerError()

    projects = Link_SF_Proj_Dude_FM.objects.filter(
            person__username=sf_username).all()
    project_names = [p.project.unixname for p in projects]
    return HttpResponse('\n'.join(project_names))
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

def edit_person_tags(request, username):
    # {{{
    person = Person.objects.get(user__username=username)

    # We can map from some strings to some TagTypes
    for known_tag_type in ('understands', 'understands_not',
                           'studying', 'seeking', 'can_mentor'):
        tag_type, _ = TagType.objects.get_or_create(name=known_tag_type)

        text = request.POST.get('edit-tags-' + known_tag_type, '')
        # set the tags to this thing
        tags = text.split(',')
        tags = [tag.strip() for tag in tags]
        # Now figure out what tags there in the DB
        tag_links = Link_Person_Tag.objects.filter(
                tag__tag_type=tag_type, person=person)
        tag_texts = [l.tag.text for l in tag_links]

        to_be_added = []
        to_be_removed = []
        import difflib
        for modification in difflib.ndiff(tag_texts, tags):
            first_two, rest = modification[:2], modification[2:]
            if first_two == '  ':
                continue
            elif first_two == '+ ':
                to_be_added.append(rest)
            elif first_two == '- ':
                to_be_removed.append(rest)
            else:
                raise ValueError, "Weird."
        for tag in to_be_removed:
            map(lambda thing: thing.delete(),
                Link_Person_Tag.objects.filter(tag__tag_type=tag_type,
                                               person=person,
                                               tag__text=tag))
        for tag in to_be_added:
            new_tag, _ = Tag.objects.get_or_create(tag_type=tag_type, text=tag)
            new_link, _ = Link_Person_Tag.objects.get_or_create(tag=new_tag,
                                                                person=person)
            
    return HttpResponseRedirect('/people/%s/' %
                                urllib.quote(person.user.username))
    # }}}

def project_icon_web(request, project_name):
    # {{{
    url = project_icon_url(project_name)
    return HttpResponseRedirect(url)
    # }}}

def import_commits_by_commit_username(request):
    # {{{

    commit_username = request.POST.get('commit_username', None)

    if not commit_username:
        fail

    nobgtask_s = request.GET.get('nobgtask', False)

    cooked_data = None
    cooked_data_password = request.POST.get('cooked_data_password', None)
    cooked_data_string = request.POST.get('cooked_data', None)
    if cooked_data_string:
        if cooked_data_password == settings.cooked_data_password:
            cooked_data = simplejson.loads(cooked_data_string)
        else:
            note = """Oops, that cooked data password didn't match.
            If you weren't expecting this error, please file a bug at 
            <a href='http://openhatch.org/bugs'>http://openhatch.org/bugs</a>."""
            raise ValueError(note)

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

    # finally, check for an attempt sitting in the queue
    if not person.poll_on_next_web_view:
        # if this is set, it means someone created a background job
        # if said job is less than two minutes old, then let it run
        now_epoch = int(datetime.datetime.now().strftime('%s'))
        then_epoch = int(person.last_polled.strftime('%s'))
        if (now_epoch - then_epoch) < 120:
            do_it = False

    if nobgtask:
        do_it = False

    if person.ohloh_grab_completed:
        do_it = False
    
    if do_it:
        username= request.user.username
        import tasks 
        # say we're trying
        person.poll_on_next_web_view = False
        person.last_polled = datetime.datetime.now()
        person.save()
        if cooked_data is None:
            result = tasks.FetchPersonDataFromOhloh.delay(
                    username=username, 
                    commit_username=commit_username)
        else:
            task = tasks.FetchPersonDataFromOhloh()
            task.run(username=username,
                    commit_username=commit_username,
                    cooked_data=cooked_data)
    # }}}

def ohloh_grab_done_web(request, username):
# {{{
    # get the person
    person = get_object_or_404(Person, user__username=username)

    return HttpResponse(bool(person.ohloh_grab_completed))
# }}}

def exp_scraper_handle_ohloh_results(username, ohloh_results):
    # {{{
    '''Input: A sequence of Ohloh ContributorInfo dicts.
    Side-effect: Create matching structures in the DB
    and mark our success in the database.'''
    person = Person.objects.get(user__username=username)
    for c_i in ohloh_results:
        for ohloh_contrib_info in ohloh_results:
            exp = ProjectExp()
            exp.person = person
            exp = exp.from_ohloh_contrib_info(ohloh_contrib_info)
            exp.last_polled = datetime.datetime.now()
            exp.last_touched = datetime.datetime.now()
            exp.save()
    person.last_polled = datetime.datetime.now()
    person.ohloh_grab_completed = True
    person.try_to_get_name_from_ohloh()
    person.save()
    # }}}

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
        'people': profile.controllers.queryset_of_people()
        })
    # }}}

def login_do(request):
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

def login(request):
    notification = notification_id = None
    if request.GET.get('msg', None) == 'oops':
        notification_id = "oops"
        notification = "Couldn't find that pair of username and password. "
        notification += "Did you type your password correctly?"
    return render_to_response('profile/login.html', {
        'notification_id': notification_id,
        'notification': notification,
        } )

def logout(request):
    django.contrib.auth.logout(request)
    return HttpResponseRedirect("/?msg=ciao")

def signup(request):
    return render_to_response("profile/signup.html", {'user': request.user} )

def signup_do(request):
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

def gimme_json_that_says_that_commit_importer_is_done(request):
    ''' This web controller is called when you want JSON that tells you 
    if the background job we started has finished. It has no side-effects.'''
    person = request.user.get_profile()
    success = person.ohloh_grab_completed
    list_of_dictionaries = [{'success': success}]
    return HttpResponse(simplejson.dumps(list_of_dictionaries))

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
    if username:
        #FIXME: Catch username collisions

        # create a user
        user = django.contrib.auth.models.User.objects.create_user(
                username=username, 
                email='', password='qwertyuiop')

        # create a linked person
        person = Person(user=user)
        person.save()

        # authenticate and login
        user = django.contrib.auth.authenticate(
                username=username, password='qwertyuiop')
        django.contrib.auth.login(request, user)

        user.set_unusable_password()

        user.save()

        # redirect to profile
        return HttpResponseRedirect('/people/%s/' % urllib.quote(username))
    else:
        pass
        # FIXME: Validate, Catch no username
    # }}}

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
