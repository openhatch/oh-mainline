# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag
from mysite.search.models import Project
import StringIO
import datetime
import urllib

def index(request):
    #{{{
    return render_to_response('profile/index.html', {
        'saved_data': request.session.get('saved_data', [])})
    #}}}

def add_contribution(request):
    # {{{
    input_contrib_username = request.POST.get('username', '')
    input_contrib_project = request.POST.get('project', '')
    input_contrib_description = request.POST.get('contrib_text', '')
    input_contrib_url = request.POST.get('url', '')

    if username and project and contrib_text and url:

        ppr = ProjectExp(
                project=project,
                url=url,
                description=contrib_text)
        ppr.save()

    return HttpResponseRedirect('/people/')
    #}}}

def get_data_dict_for_display_person(username):
    # {{{
    person, person_created = Person.objects.get_or_create(
            username=username)

    if person.poll_on_next_web_view:
        person.fetch_contrib_data_from_ohloh()
        person.poll_on_next_web_view = False
        person.save()

    project_exps = ProjectExp.objects.filter(
            person=person)

    exps_to_tags = {}
    for exp in project_exps:
        tag_links = Link_ProjectExp_Tag.objects.filter(project_exp=exp)
        exps_to_tags[exp] = [link.tag for link in tag_links]

    # {
    #   Experience1:
    #   ["awesome", "fun", "illuminating", "helped_me_get_laid"],
    # }

    exp_taglist_pairs = exps_to_tags.items()

    return { 'person': person, 'exp_taglist_pairs': exp_taglist_pairs } 
    # }}}

def display_person(request, input_username=None):
    # {{{

    if input_username is None:
        input_username = request.GET.get('u', None)
        if input_username is None:
            return render_to_response('profile/profile.html')

    data_dict = get_data_dict_for_display_person(input_username)

    return render_to_response('profile/profile.html', data_dict)

    # }}}

def add_one_debtag_to_project(project_name, tag_text):
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

def list_debtags_of_project(project_name):
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

def import_debtags(cooked_string = None):
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

def get_data_for_email(request):
    # {{{
    # FIXME: Hard-coded username
    username='paulproteus'
    email = request.POST.get('email', '')
    if email:
        import ohloh
        oh = ohloh.get_ohloh()
        from_ohloh = oh.get_contribution_info_by_email(email)
        for data in from_ohloh:
            person, created = Person.objects.get_or_create(
                username=username) # FIXME: Which username?
            pe = ProjectExp(person=person)
            pe.from_ohloh_contrib_info(data)
            pe.save()
    return HttpResponseRedirect('/people/?' + urllib.urlencode({'u':
                                                                username}))
    # }}}

def add_tag_to_project_exp_web(request):
    # {{{
    # Get data
    username = request.GET.get('username', None)
    project_name = request.GET.get('project_name', None)
    tag_text = request.GET.get('tag_text', None)
    format = request.GET.get('format', 'html')

    # Validate data
    if username and project_name and tag_text:
        add_tag_to_project_exp(username, project_name, tag_text)
        notification = "You tagged %s's experience with %s as %s" % (
                username, project_name, tag_text)
        if format == 'json':
            return HttpResponse("({'notification': '%s'})" % notification)
        else:
            data_dict = get_data_dict_for_display_person(username)
            data_dict['notification'] = notification
            return render_to_response('profile/profile.html', data_dict)
    else:
        return HttpResponseServerError()
    # }}}

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

    new_link = Link_ProjectExp_Tag.objects.create(
            tag=tag, project_exp=project_exp)
    # FIXME: Catch when link already exists.
    # }}}
