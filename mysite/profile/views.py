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

def get_data_for_username(request):
    # {{{
    username = request.POST.get('username', '')

    if username:
        saved = request.session.get('saved_data', [])
        # always append the data
            saved.append(new_values)
            request.session['saved_data'] = saved
    return HttpResponseRedirect('/profile/')

def get_data_for_person(_person):
    if not _person:
        pass # implement fail

    import ohloh
    oh = ohloh.get_ohloh()
    person_to_project_rels = [PersonToProjectRelationship(**vals) for vals in ]
    contrib_info_list = oh.get_contribution_info_by_username(person.username)
    for contrib_info in contrib_info_list:
        ppr = PersonToProjectRelationship(person=_person)

def person_to_project_rels_ohloh_style
# vim: ai ts=4 sts=4 et sw=4
