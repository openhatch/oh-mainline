# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag
from mysite.search.models import Project
import StringIO
import datetime
import urllib
import simplejson

# Add a contribution {{{

def add_project_exp_web(request):
    # {{{
    username = request.POST.get('u', '')
    project_name = request.POST.get('project_name', '')
    description = request.POST.get('description', '')
    url = request.POST.get('url', '')
    format = request.POST.get('format', 'html')

    notif = ''
    if username and project_name and description and url:
        ProjectExp.create_from_text(username, project_name, description, url)
        notif = "Added experience with %s to %s's profile." % (
                project_name, username)
    else:
        notif = "Er, like, bad input: {project_name: %s, username: %s}" % (
                project_name, username)

    if format == 'json':
        return HttpResponse(simplejson.dumps([{'notification': notif}]))

    data = profile_data_from_username(username)
    data['notification'] = notif

    return HttpResponseRedirect('/people/?' +
            urllib.urlencode({'u': username}))
    #}}}
add_contribution_web = add_project_exp_web

def add_contribution(username, project_name, url='', description=''):
    # {{{
    pass
    # }}}

# }}}

def exp_scraper__display_input_form(self, request):
    return render_to_response('profile/exp_scraper_input.html')

def exp_scraper__check_input_and_scrape(request):
    return HttpResponse('')
    
    # Check input
    input_username = request.GET.get('u', None)
    if input_username is None:
        return response(request)
    
    exp_scraper__scrape(input_username)

    return display_person(request, input_username)

def exp_scraper__scrape(self, username):

        #person.fetch_projects_from_sourceforge()
        #Execute script on server: person.fetch_contrib_data_from_ohloh_for_user_and_projects()
        person.fetch_contrib_data_from_ohloh()
        person.save()

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

    return { 'person': person, 'exp_taglist_pairs': exp_taglist_pairs } 
    # }}}

def display_person_web(request, input_username=None):
    if input_username is None:
        input_username = request.GET.get('u', None)
        if input_username is None:
            return render_to_response('profile/profile.html')

    tab = request.GET.get('tab', None)

    return display_person(input_username, tab)

def display_person(username, tab):
    # {{{

    data_dict = profile_data_from_username(username)

    if tab == 'inv':
        return render_to_response('profile/participation.html', data_dict)
    if tab == 'tags':
        return render_to_response('profile/tags.html', data_dict)
    if tab == 'tech':
        return render_to_response('profile/tech.html', data_dict)
    else:
        return render_to_response('profile/main.html', data_dict)

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
                username=username) # FIXME: Later we'll have to be
                                   # able to merge user objects
            pe = ProjectExp(person=person)
            pe.from_ohloh_contrib_info(data)
            pe.save()
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u':
                                                                username}))
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
    return HttpResponseRedirect('/people/?' +
                                urllib.urlencode({'u': username,
                                                  'notification': notification}))
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
    return display_person_redirect(username)

def display_person_redirect(username):
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u': username}))
    # }}}

def make_favorite_project_exp(exp_id_obj):
    if exp_id_obj is None:
        return
    exp_id = int(exp_id_obj)
    desired_pe = ProjectExp.objects.get(id=exp_id)
    desired_pe.favorite = True
    desired_pe.save()
    return

def make_favorite_project_exp_web(request):
    exp_id = request.POST.get('exp_id', None)
    username = request.POST.get('username', '')
    make_favorite_project_exp(exp_id)
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u': username}))

def make_favorite_tag(exp_id_obj, tag_text):
    if exp_id_obj is None:
        return
    exp_id = int(exp_id_obj)
    desired_tag = Link_ProjectExp_Tag.objects.get(project_exp__id=exp_id,
                                                  tag__text=tag_text)
    desired_tag.favorite = True
    desired_tag.save()
    return

def make_favorite_exp_tag_web(request):
    exp_id = request.POST.get('exp_id', None)
    tag_text = request.POST.get('tag_text', None)
    username = request.POST.get('username', None)
    make_favorite_tag(exp_id, tag_text)
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u': username}))

# }}}
