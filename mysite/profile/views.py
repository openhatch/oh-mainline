# vim: ai ts=4 sts=4 et sw=4

# Imports {{{
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag
from mysite.search.models import Project
import StringIO
import datetime
import urllib
import simplejson
import re
from odict import odict
import collections
import difflib
# }}}

# Add a contribution {{{

def person_involvement_add_input(request, username):
    # {{{
    project_name = request.GET.get('project_name', '')
    description = request.GET.get('description', '')
    url = request.GET.get('url', '')
    alteration_type = request.GET.get('alteration_type', 'add')

    return render_to_response('profile/involvement/add.html', {
        'person': Person.objects.get(username=username),
        'project_name': project_name,
        'description': description,
        'url': url,
        'alteration_type': alteration_type,
        'title': '+involvement / ' + username + ' / openhatch'
        })
    # }}}

def person_involvement_add(request):
    # {{{
    username = request.POST.get('u', '')
    project_name = request.POST.get('project_name', '')
    description = request.POST.get('description', '')
    url = request.POST.get('url', '')
    format = request.POST.get('format', 'html')

    notification = ''
    if username and project_name and description and url:
        ProjectExp.create_from_text(username, project_name, description, url)
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

    return HttpResponseRedirect('/people/%s?' % urllib.quote(username) +
            urllib.urlencode({'tab': 'inv'}))
    #}}}

"""
def project_exp_update_web(request):
    # {{{
    username = request.POST.get('u', '')
    project_name = request.POST.get('project_name', '')
    description = request.POST.get('description', '')
    url = request.POST.get('url', '')
    format = request.POST.get('format', 'html')

    notification = ''
    if username and project_name and description and url:
        person = Person.objects.get(username=username)
        project, _ = Project.objects.get_or_create(name=project_name)
        exp, _ = ProjectExp.objects.get_or_create(
                person=person,
                project=project)
        exp.description = description
        exp.url = url
        exp.save()
        notification = "Updated %s's experience with %s." % (
                username, project_name)
    else:
        notification = "Unexpectedly imperfect input: {project_name: %s, username: %s}" % (
                project_name, username)
        if format == 'json':
            dict = {'notification': notification}
            return HttpResponse(simplejson.dumps([dict]))

    data = profile_data_from_username(username)
    data['notification'] = notification

    return HttpResponseRedirect('/people/?' +
            urllib.urlencode({'u': username, 'tab': 'inv'}))
    # }}}
"""

def add_contribution(username, project_name, url='', description=''):
    pass

# }}}

# XP slurper {{{
def xp_slurper_display_input_form(request):
    # {{{
    notification = None
    error = request.GET.get('error', None)
    if error == 'missing_username':
        notification = "Please enter a username."
    return render_to_response('profile/xp_slurper.html', {'notification': notification})
    # }}}

def exp_scraper_scrape_web(request):
    # {{{
    # Check input
    input_username = request.POST.get('u', None)

    if input_username is None or input_username == '':
        return HttpResponseRedirect('xp_slurp?' + urllib.urlencode(
            {'error': 'missing_username'}))
    
    person, _ = Person.objects.get_or_create(username=input_username)

    exp_scraper_scrape(person)

    return HttpResponseRedirect('/people/?' + urllib.urlencode(
        {'u': input_username, 'tab': 'main'}))
    # }}}

def exp_scraper_scrape(person):
    # {{{
    #person.fetch_projects_from_sourceforge()
    #Execute script on server: person.fetch_contrib_data_from_ohloh_for_user_and_projects()
    person.fetch_contrib_data_from_ohloh()
    person.save()
    # }}}
# }}}

# Display profile {{{
def profile_data_from_username(username, fetch_ohloh_data = False):
    # {{{
    person, person_created = Person.objects.get_or_create(
            username=username)

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

    return {
            'person': person,
            'interested_in_working_on_list': interested_in_working_on_list, 
            'projects': projects_extended
            } 
    # }}}

def display_person_web(request, input_username=None):
    if input_username is None:
        input_username = request.GET.get('u', None)
        if input_username is None:
            return render_to_response('profile/profile.html')

    edit = False
    if request.GET.get('edit', 0) == '1':
        edit = True

    tab = request.GET.get('tab', None)

    person, _ = Person.objects.get_or_create(username=input_username)

    return display_person(person, tab, edit)

def display_person(person, tab, edit):
    # {{{

    data_dict = data_for_person_display_without_ohloh(person)

    data_dict['edit'] = edit

    title = person.username + " / %s : openhatch"
    if tab == 'inv':
        data_dict['title'] = title % "community involvement"
        return render_to_response('profile/participation.html', data_dict)
    if tab == 'tags':
        data_dict['title'] = title % "tags"
        data_dict['tags'] = tags_dict_for_person(person)
        data_dict['tags_flat'] = dict(
            [ (key, ', '.join([k.text for k in data_dict['tags'][key]]))
              for key in data_dict['tags'] ])
        return render_to_response('profile/tags.html', data_dict)
    if tab == 'tech':
        data_dict['title'] = title % "tech"
        return render_to_response('profile/tech.html', data_dict)
    else:
        data_dict['title'] = title % "profile"
        data_dict['projects'] = dict(data_dict['projects'].items()[:4])
        data_dict['tags'] = tags_dict_for_person(person)
        data_dict['tags_flat'] = dict(
            [ (key, ', '.join([k.text for k in data_dict['tags'][key]]))
              for key in data_dict['tags'] ])
        return render_to_response('profile/main.html', data_dict)

    # }}}

def tags_dict_for_person(person):
    # {{
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
            time_record_was_created = datetime.datetime.now(),
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
        import ohloh
        oh = ohloh.get_ohloh()
        from_ohloh = oh.get_contribution_info_by_email(email)
        for data in from_ohloh:
            person, created = Person.objects.get_or_create(
                    username=username)
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
def add_tag_to_project_exp_web(request):
    # {{{
    # Get data
    username = request.POST.get('username', None)
    project_name = request.POST.get('project_name', None)
    big_tag_text = request.POST.get('tag_text', '')
    format = request.POST.get('format', 'html')

    useful_tags = filter(None, map(lambda s: s.strip(),
        big_tag_text.split(',')))

    # Validate data
    if not username or not project_name or not big_tag_text:
        return HttpResponseServerError()

    for tag_text in useful_tags:
        # Great, we have all we need:
        add_tag_to_project_exp(username, project_name, tag_text)
    notification = "You tagged %s's experience with %s as %s" % (
            username, project_name, ','.join(useful_tags))
    request_GET = {
            'u': username,
            'notification': notification
            }
    query_str = "?" + urllib.urlencode(request_GET)
    return HttpResponseRedirect('/people/%s' % query_str)
    # }}}

# FIXME: rename to project_exp_tag__add
def add_tag_to_project_exp(username, project_name,
        tag_text, tag_type_name='user_generated'):
    # {{{
    tag_type, created = TagType.objects.get_or_create(
            name=tag_type_name)

    tag, tag_created = Tag.objects.get_or_create(
            text=tag_text, tag_type=tag_type)

    person = Person.objects.get(username=username)
    # FIXME: Catch when no such person exists.

    project = Project.objects.get(name=project_name)
    # FIXME: Catch when no such project exists.

    project_exp = ProjectExp.objects.filter(
            person=person, project=project)[0]
    # FIXME: Catch when no such project exp exists.
    # Not using get; the error of multiple
    # project_exps with the same person and project
    # need not be caught here.

    # Does it already exist? If so, we're golden.
    # FIXME: Use get_or_create
    old_links = list(Link_ProjectExp_Tag.objects.filter(
        tag=tag, project_exp=project_exp))
    if not old_links:
        new_link = Link_ProjectExp_Tag.objects.create(
                tag=tag, project_exp=project_exp)
        # FIXME: Move to Link_ProjectExp_Tag.create_from_strings
    # }}}

def project_exp_tag__remove(username, project_name,
        tag_text, tag_type_name='user_generated'):
    # {{{
    # FIXME: Maybe don't actually delete, but merely disable (e.g. deleted=yes),
    # in case we want to run stats on what tags people are deleting, etc.
    tag_link = Link_ProjectExp_Tag.get_from_strings(username, project_name, tag_text)
    tag_link.delete()
    return tag_link
    # }}}

def project_exp_tag__remove__web(request):
    # {{{
    username = request.POST.get('username', None)
    project_name = request.POST.get('project_name', None)
    tag_text = request.POST.get('tag_text', None)
    format = request.POST.get('format', 'html')
    tag_type_name = request.POST.get('tag_type_name', 'user_generated')

    if username and project_name and tag_text:
        # Collect errors in this list
        errors = []

        # Verify person with that username exists
        if Person.objects.filter(username=username).count() == 0:
            errors.append("No person found with username: %s" % username)

        # Verify project with that name exists
        if Project.objects.filter(name=project_name).count() == 0:
            errors.append("No project found with name: %s" % project_name)

        # Verify tag with that text exists
        if Tag.objects.filter(text=tag_text).count() == 0:
            errors.append("No project found with name: %s" % project_name)

        if errors:
            if format == 'json':
                return HttpResponse(simplejson.dumps([{'errors': errors}]))
            else:
                return HttpResponseRedirect('/people/?' + urllib.urlencode(
                    {'u': username, 'errors': errors}))

        project_exp_tag__remove(username, project_name, tag_text)

        notification = "Successfully removed tag: {username: %s, project_name: %s, tag_text: %s}" % (username, project_name, tag_text)

        if format == 'json':
            return HttpResponse(simplejson.dumps([
                {'notification': notification}
                ]))
        else:
            return HttpResponseRedirect('/people/?' + urllib.urlencode(
                {'u': username, 'notification': notification}))
    else:
        errors = ["You're missing some crucial input."]
        if format == 'json':
            return HttpResponse(simplejson.dumps([{'errors': errors}]))
        else:
            return HttpResponseRedirect('/people/?' + urllib.urlencode(
                {'u': username, 'errors': errors}))

    # }}}

# }}}

# Specify what you like working on {{{

def change_what_like_working_on(username, new_like_working_on):
    # {{{
    if username is None:
        return
    if new_like_working_on is None:
        return

    person = get_object_or_404(Person, username=username)
    person.interested_in_working_on = new_like_working_on
    person.save()
    return person
    # }}}

def change_what_like_working_on_web(request):
    # {{{
    username = request.POST.get('username')
    new_like = request.POST.get('like-working-on')
    person = change_what_like_working_on(username, new_like)
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u': username, 'tab': 'tags'}))
    # }}}

def DISABLE_display_person_redirect(username):
    # {{{
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u': username}))
    # }}}

def make_favorite_project_exp(exp_id_obj):
    # {{{
    if exp_id_obj is None:
        return
    exp_id = int(exp_id_obj)
    desired_pe = ProjectExp.objects.get(id=exp_id)
    desired_pe.favorite = True
    desired_pe.save()
    return
    # }}}

def make_favorite_project_exp_web(request):
    # {{{
    exp_id = request.POST.get('exp_id', None)
    username = request.POST.get('username', '')
    make_favorite_project_exp(exp_id)
    return HttpResponseRedirect('/people/?' + urllib.urlencode(
        {'u': username, 'tab': 'inv'}))
    # }}}

def make_favorite_tag(exp_id_obj, tag_text):
    # {{{
    if exp_id_obj is None:
        return
    exp_id = int(exp_id_obj)
    desired_tag = Link_ProjectExp_Tag.objects.get(project_exp__id=exp_id,
            tag__text=tag_text)
    desired_tag.favorite = True
    desired_tag.save()
    return
    # }}}

def make_favorite_exp_tag_web(request):
    # {{{
    exp_id = request.POST.get('exp_id', None)
    tag_text = request.POST.get('tag_text', None)
    username = request.POST.get('username', None)
    make_favorite_tag(exp_id, tag_text)
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u': username}))
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
    PREFIX='_project_hash_2136870e40a759b56b9ba97a0d7f60b84dbc90097a32da284306e871105d96cd' # sha256 of 1MiB of /dev/urandom
    import hashlib
    hashed = hashlib.sha256(PREFIX + project_name)
    return hashed.hexdigest()

import os
import tempfile
def project_icon_url(project_name, actually_fetch = True):
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
            import ohloh
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

def edit_exp_tag(request, exp_id):
    project_exp = ProjectExp.objects.get(id=exp_id)
    
    text = request.POST.get('text', None)
    if text is None:
        return render_to_response('profile/edit_exp_tags.html',
                                  {'text': ''})
    else:
        # set the tags to this thing
        tags = text.split(',')
        tags = [tag.strip() for tag in tags]
        # Now figure out what tags there in the DB
        tag_type, _ = TagType.objects.get_or_create(name='user_generated')
        tag_links = Link_ProjectExp_Tag.objects.filter(tag__tag_type=tag_type,
                                                       project_exp__id=exp_id)
        tag_texts = [l.tag.text for l in tag_links]

        to_be_added = []
        to_be_removed = []
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
        map(lambda thing: thing.delete(),
            Link_ProjectExp_Tag.objects.filter(tag__tag_type=tag_type,
                                               project_exp__id=exp_id,
                                               tag__text=tag))
        for tag in to_be_added:
            new_tag, _ = Tag.objects.get_or_create(tag_type=tag_type, text=tag)
            new_tag.save()
            new_link, _ = Link_ProjectExp_Tag.objects.get_or_create(tag=new_tag,
                                              project_exp=project_exp)
            new_link.save()
            #import pdb
            #pdb.set_trace()
            
        return HttpResponseRedirect('/people/%s?tab=inv' %
                                    urllib.quote(project_exp.person.username))

def edit_person_tags(request, username):
    person = Person.objects.get(username=username)

    # We can map from some strings to some TagTypes
    for known_tag_type in ('understands', 'understands_not',
                           'studying', 'seeking', 'can_mentor'):
        tag_type, _ = TagType.objects.get_or_create(name=known_tag_type)

        text = request.POST.get('edit-tags-' + known_tag_type, '')
        # set the tags to this thing
        tags = text.split(',')
        tags = [tag.strip() for tag in tags]
        # Now figure out what tags there in the DB
        tag_links = Link_Person_Tag.objects.filter(tag__tag_type=tag_type,
                                                   person=person)
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
                                                                person=
                                                                person)
            
    return HttpResponseRedirect('/people/%s?tab=tags' %
                                urllib.quote(person.username))

def project_icon_web(request, project_name):
    url = project_icon_url(project_name)
    return HttpResponseRedirect(url)

def exp_scraper_display_for_person_web(request):
    username = request.GET.get('u', None)
    nobgtask_s = request.GET.get('nobgtask', False)

    involved_projects = []
    
    try:
        nobgtask = bool(nobgtask_s)
    except ValueError:
        nobgtask = False
    
    if username is None:
        return HttpResponseServerError()

    # get the person
    person = get_object_or_404(Person, username=username)

    # Find the existing ProjectExps
    project_exps = ProjectExp.objects.filter(person=person)
    involved_projects.extend([exp.project.name for exp in project_exps])

    # if we are allowed to make bgtasks, create background tasks
    # to pull in this user's data (just the one huge one)
    if nobgtask:
        pass
    else:
        from tasks import FetchPersonDataFromOhloh
        result = FetchPersonDataFromOhloh.delay(username=username)
        
    return HttpResponse(person.username + '\n'.join(involved_projects))

def exp_scraper_handle_ohloh_results(username, ohloh_results):
    '''Input: A sequence of Ohloh ContributorInfo dicts.
    Side-effect: Create matching structures in the DB.'''
    person = Person.objects.get(username=username)
    for c_i in ohloh_results:
        for ohloh_contrib_info in ohloh_results:
            exp = ProjectExp()
            exp.person = person
            exp = exp.from_ohloh_contrib_info(ohloh_contrib_info)
            exp.last_polled = datetime.datetime.now()
            exp.last_touched = datetime.datetime.now()
            exp.save()
        person.last_polled = datetime.datetime.now()
        person.save()

# }}}
