# vim: ai ts=4 sts=4 et sw=4

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from mysite.profile.models import Person, PersonToProjectRelationship

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

        ppr = PersonToProjectRelationship(
                project=project,
                url=url,
                description=contrib_text)
        ppr.save()

    return HttpResponseRedirect('/profile/')
    #}}}

def get_data_dict_for_display_person(username):

    person, bool_created = Person.objects.get_or_create(
            username=username)
    # Not doing anything with bool_created at the moment.

    if person.poll_on_next_web_view:
        person.fetch_data_from_ohloh()
        person.poll_on_next_web_view = False
        person.save()

    rels_to_projects = PersonToProjectRelationship.objects.filter(
            person=person)

    return { 'person': person, 'rels_to_projects': rels_to_projects, }

def display_person(request, input_username=None):
    # {{{

    if input_username is None:
        input_username = request.GET.get('u', None)
        if input_username is None:
            return HttpResponseServerError()

    context = get_data_dict_for_display_person(input_username)

    return render_to_response('profile/profile.html', context)

    # }}}
def get_data_for_email(request):
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

