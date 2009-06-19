# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag
from mysite.search.models import Project

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

    return HttpResponseRedirect('/profile/')
    #}}}

def get_data_dict_for_display_person(username):
    # {{{
    person, person_created = Person.objects.get_or_create(
            username=username)

    if person.poll_on_next_web_view:
        person.fetch_data_from_ohloh()
        person.poll_on_next_web_view = False
        person.save()

    project_exps = ProjectExp.objects.filter(
            person=person)

    return { 'person': person, 'project_exps': project_exps, }
    # }}}

def display_person(request, input_username=None):
    # {{{

    if input_username is None:
        input_username = request.GET.get('u', None)
        if input_username is None:
            return HttpResponseServerError()

    data_dict = get_data_dict_for_display_person(input_username)

    return render_to_response('profile/profile.html', data_dict)

    # }}}

def get_data_for_email(request):
    # {{{
    email = request.POST.get('email', '')
    if email:
        saved = request.session.get('saved_data', [])
        # FIXME: This is faked out
        new_values = dict(project='ccHost',
                          url='whatever',
                          contrib_text='whatever')
        saved.append(new_values)
        request.session['saved_data'] = saved
    return HttpResponseRedirect('/profile/')
    # }}}

def add_tag_to_project_exp_web(request):
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
            return render_to_response('profile/profile.html', {
                'notification': notification })
    else:
        return HttpResponseServerError()

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

    project_exp = ProjectExp.objects.get(
            person=person, project=project)
    # FIXME: Catch when no such project exp exists.

    new_link = Link_ProjectExp_Tag.objects.create(
            tag=tag, project_exp=project_exp)
    # FIXME: Catch when link already exists.
    # }}}
