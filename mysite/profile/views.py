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

def get_person_and_fetch_from_ohloh_web(input_username=None):
    # {{{

    if input_username is None:
        return HttpResponseServerError()

    person = Person.object.get(username=input_username)
    if person.poll_on_next_web_view:
        person.fetch_data_from_ohloh()
        person.poll_on_next_web_view = True
        person.save()

    relationships_with_projects = PersonToProjectRelationship.objects.filter(
            person=self)

    return render_to_response('profile/profile.html',
            person: person,
            relationships_with_projects: relationships_with_projects
            )

    # }}}


# vim: ai ts=4 sts=4 et sw=4
