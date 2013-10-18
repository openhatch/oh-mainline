# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2009, 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
from django.contrib.admindocs.tests import fields
from django.core import serializers
from django.core.mail import send_mail
import socket
from django.template import RequestContext
from mysite.base.models import Organization, Skill, Language, Duration
from mysite.project import view_helpers
from mysite.search.models import Project, ProjectInvolvementQuestion, Answer
import mysite.project.view_helpers
import django.template
import mysite.base.decorators
import mysite.profile.views
import mysite.project.forms
from mysite.base.decorators import has_permissions, view

from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponsePermanentRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from django.utils.datastructures import MultiValueDictKeyError

def create_project_page_do(request):
    project_name = request.POST.get('project_name', None)
    if project_name:
        matches = Project.objects.filter(name__iexact=project_name)
        if matches:
            our_project = matches[0]
            # If project exists, go to normal project page
            return HttpResponseRedirect(our_project.get_url())

    return HttpResponseBadRequest('Bad request')


@login_required
@has_permissions(['can_view_projects'])
@mysite.base.decorators.view
def project(request, project__name = None):
    p = get_object_or_404(Project, name=project__name)

    wanna_helpers = p.people_who_wanna_help.all()
    if (request.user.is_authenticated() and
        request.user.get_profile() in wanna_helpers):
        user_wants_to_help = True
    else:
        user_wants_to_help = False

    wanna_help = (bool(request.GET.get('wanna_help', False)) and
                  user_wants_to_help)
    
    context = {}

    context['random_pfentry'] = p.get_random_description()

    # Get or create two paragraph-y questions.
    questions = [
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='where_to_start', is_bug_style=False)[0],
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='non_code_participation', is_bug_style=True)[0],
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='newcomers', is_bug_style=True)[0],
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='stress', is_bug_style=True)[0],
    ]
    context['question2answer'] = [(question, question.get_answers_for_project(p))
        for question in questions]

    if p.buildhelper_set.all():
        buildhelper = p.buildhelper_set.all()[0]
        buildhelper_steps = buildhelper.buildhelperstep_set.all()
    else:
        buildhelper = None
        buildhelper_steps = []
    
    if request.GET.get('cookies', '') == 'disabled':
        context['cookies_disabled'] = True

    people_to_show = wanna_helpers

    contact_form_list = []
    wannahelpernotes = mysite.search.models.WannaHelperNote.objects.filter(person__id__in=wanna_helpers.values_list('id', flat=True), project=p).select_related().order_by('-pk')
    for note in wannahelpernotes:
        # a WannaHelperNote should always exist for all Person objects in people_to_show
        started_checked = bool(note.contacted_on)
        contact_form_list.append({
                'form' : mysite.project.forms.MarkContactedForm(prefix="helper-%d" % (note.person_id,),
                                                                initial= { 'project_id' : p.pk,
                                                                           'person_id' : note.person_id,
                                                                           'checked' : started_checked}),
                'started_checked': started_checked,
                'person' : note.person,
                'note' : note,
                })
    contact_form_list.sort(key=lambda x: (x['started_checked']))

    button_widget_data = mysite.base.view_helpers.get_uri_metadata_for_generating_absolute_links(
            request)
    button_widget_data['project'] = p
    button_as_widget_source = render_to_string(
        'project/button_as_widget.html', button_widget_data)

    context.update({
        'project': p,
        'buildhelper_steps' : buildhelper_steps,
        'contributors': p.get_contributors()[:3],
        'mentors': mysite.profile.view_helpers.TagQuery('can_mentor', project__name).people,
        'language_mentors': mysite.profile.view_helpers.TagQuery('can_mentor', p.language).people,
        'explain_to_anonymous_users': True,
        'wanna_help_form': mysite.project.forms.WannaHelpForm(),
        'user_wants_to_help': request.user.is_authenticated() and request.user.get_profile() in p.people_who_wanna_help.all(),
        'user_just_signed_up_as_wants_to_help': wanna_help,
        'people_to_show': people_to_show,
        'button_as_widget_source': button_as_widget_source,
        'mark_contacted_forms' : contact_form_list,
        })

    question_suggestion_response = request.GET.get('question_suggestion_response', None)
    context['notifications'] = []
    if question_suggestion_response == 'success':
        context['notifications'].append({
            'id': 'question_suggestion_response',
            'text': 'Thanks for your suggestion!'
            })
    elif question_suggestion_response == 'failure':
        context['notifications'].append({
            'id': 'question_suggestion_response',
            'text': "Oops, there was an error submitting your suggested question--we probably couldn't connect to our outgoing mailserver. Try just sending an email to <a href='hello@openhatch.org'>hello@openhatch.org</a>"
            })

    return (request,
            'project/project.html',
            context)


@login_required
@has_permissions(['can_view_projects'])
#@mysite.base.decorators.cache_function_that_takes_request
def projects(request):
    data = {}
    post_data = request.POST
    query = request.POST.get('q', '')
    matching_projects = []
    if query:
        query = query.strip()
        matching_projects = mysite.project.view_helpers.similar_project_names(
            query)
        project_matches_query_exactly = query.lower() in [p.name.lower() for p in matching_projects]
        if len(matching_projects) == 1 and project_matches_query_exactly:
            return HttpResponseRedirect(matching_projects[0].get_url())
        matching_projects = mysite.project.view_helpers.filter_projects(projects=matching_projects, post_data=post_data)
    else:
        matching_projects = Project.objects.all()

    project_ids = []
    for project in matching_projects:
        project_ids.append(int(project.id))

    data.update({
            'project_ids': project_ids,
            'query': query,
            'matching_projects': matching_projects,
            'explain_to_anonymous_users': True,
            'skills': Skill.objects.all(),
            'organizations': Organization.objects.all(),
            'languages': Language.objects.all(),
            'duration': Duration.objects.all()
            })
    return mysite.base.decorators.as_view(request, "project/projects.html", data,
            slug=projects.__name__)

@login_required
@has_permissions(['add_project'])
def add_project(request):
    data = {}
    project_form = mysite.project.forms.ProjectForm()
    data['form'] = project_form

    if request.POST:
        project_data_form = mysite.project.forms.ProjectForm(request.POST)

        if project_data_form.is_valid():
            project = project_data_form.save()
            return HttpResponseRedirect("/projects")
        else:
            data['form'] = project_data_form
            data['has_errors'] = True

    return mysite.base.decorators.as_view(request, "project/add_project.html", data, projects.__name__)

def project_filter(request):
    post_data = request.POST
    project_ids= post_data.getlist(u'project_ids[]')
    projects = Project.objects.filter(pk__in=project_ids).order_by('id')
    filtered_projects = view_helpers.filter_projects(projects, post_data)
    response = render_to_string(template_name='project/project_list.html',
        dictionary={'matching_projects': filtered_projects},
        context_instance=RequestContext(request))
    return HttpResponse(response, mimetype='application/html')

def redirect_project_to_projects(request, project__name):
    new_url = reverse(project, kwargs={'project__name': project__name})
    return HttpResponsePermanentRedirect(new_url)

@login_required
def delete_paragraph_answer_do(request):
    answer__pk = request.POST['answer__pk']
    # grab the answer from the database.  delete it.  done.
    our_answer = Answer.objects.get(pk=answer__pk, author=request.user)
    our_answer.delete()
    return HttpResponseRedirect(reverse(project, kwargs={'project__name': our_answer.project.name}))

def create_answer_do(request):

    if 'is_edit' in request.POST:
        answer = Answer.objects.get(pk=request.POST['answer__pk'])
    else:
        answer = Answer()

    try:
        answer.project = mysite.search.models.Project.objects.get(pk=request.POST['project__pk'])
        question = ProjectInvolvementQuestion.objects.get(pk=request.POST['question__pk'])
        answer.text = request.POST['answer__text']
        answer.title = request.POST.get('answer__title', None)
    except MultiValueDictKeyError, full_error_message:
        return HttpResponseBadRequest("""<p>
            Sorry, an error occurred! This post handler
            (<tt>project.views.create_answer_do</tt>) expects to see all the following
            variables in the POST: <tt>project__pk, question__pk, answer__text,
            answer__title</tt>. One of them was missing.
            </p>
            
            <p>
            The full error message might be helpful: 
            <xmp>%s</xmp>
            </p>
            """ % full_error_message)

    question.save()
    answer.question = question

    # loltrolled--you dont have cookies, so we will throw away your data at the last minute
    if (request.user.is_authenticated() or
        'cookies_work' in request.session):
        suffix = ''
    else:
        suffix = '?cookies=disabled'
        return HttpResponseRedirect(reverse(project,
            kwargs={'project__name': answer.project.name}) + suffix)

    answer.save()
    if answer.author is None:
        mysite.project.view_helpers.note_in_session_we_control_answer_id(request.session,
                                                                        answer.pk)
    if not request.user.is_authenticated():
        # If user isn't logged in, send them to the login page with next
        # parameter populated.
        url = reverse('oh_login')
        url += "?" + mysite.base.unicode_sanity.urlencode({u'next':
            unicode(answer.project.get_url())})
        return HttpResponseRedirect(url)
    else:
        answer.author = request.user

    return HttpResponseRedirect(reverse(project, kwargs={'project__name': answer.project.name}) + suffix)

@login_required
@mysite.base.decorators.view
def suggest_question(request):
    template = "project/suggest_question.html"
    data = {
            'project__pk': request.GET['project__pk']
            }
    return (request, template, data)

@login_required
def suggest_question_do(request):
    project = mysite.search.models.Project.objects.get(pk=request.POST['project__pk'])
    user = request.user
    body = request.POST['suggested_question']
    body += "\nproject name: " + project.name
    body += "\nproject display name: " + project.display_name
    body += "\nproject pk: " + str(project.pk)
    body += "\nuser name: " + user.username
    body += "\nuser pk: " + str(user.pk)
    question_suggestion_response = ""
    #TODO: Asheesh would really rather this be enqueued as a background job
    try:
        send_mail('Project Page Question Suggestion: ', body, 'all@openhatch.org', ['all@openhatch.org'], fail_silently=False)
        question_suggestion_response = "success"
    except socket.error:
        #NOTE: this will probably only happen on a local server (not on the live site)
        question_suggestion_response = "failure"
    template = "project/project.html"
    return HttpResponseRedirect(reverse(mysite.project.views.project, kwargs={'project__name': project.name}) + '?question_suggestion_response=' + question_suggestion_response)

def mark_contacted_do(request):
    #extract person_ids from request.POST.keys()
    project = django.shortcuts.get_object_or_404(Project, pk=request.POST.get('mark_contact-project'))
    for key in request.POST.keys():
        if key.endswith('checked'):
            person_pk = key[7:-8]
            #for each prefix, validate form
            mark_contacted_form = mysite.project.forms.MarkContactedForm(request.POST, prefix="helper-%s" % (person_pk))
            if mark_contacted_form.is_valid():
                project_id = mark_contacted_form.cleaned_data['project_id']
                person_id = mark_contacted_form.cleaned_data['person_id']
                whn = mysite.search.models.WannaHelperNote.objects.get(person__id=person_id, project__id=project_id)
                # add contacted by and date if not already set.
                if not whn.contacted_by:
                    whn.contacted_by = request.user
                    whn.contacted_on = datetime.date.today()
                    whn.save()
    return HttpResponseRedirect(reverse(mysite.project.views.project,
                                        kwargs={'project__name': project.name}) + '#iwh_handler')

def wanna_help_do(request):
    wanna_help_form = mysite.project.forms.WannaHelpForm(request.POST)
    if wanna_help_form.is_valid():
        project = wanna_help_form.cleaned_data['project']
    else:
        return HttpResponseBadRequest("No project id submitted.")

    if request.user.is_authenticated():
        person = request.user.get_profile()
        project.people_who_wanna_help.add(person)
        mysite.search.models.WannaHelperNote.add_person_project(person, project)
        project.save()

     
        return HttpResponseRedirect(project.get_url() + "?success=1")
    else:
        # Then store a note in the session...
        wanna_help_queue = request.session.get('projects_we_want_to_help_out', [])
        wanna_help_queue.append(project.id)
        request.session['projects_we_want_to_help_out'] = wanna_help_queue

        # If the user came from offsite, note that in the session too
        if wanna_help_form.cleaned_data['from_offsite']:
            request.session['from_offsite'] = True
        
        # If user isn't logged in, send them to the login page with next
        # parameter populated.
        url = reverse('oh_login')
        url += "?"
        url += mysite.base.unicode_sanity.urlencode({u'next':
            unicode(project.get_url()) + '?wanna_help=true'})
        if request.is_ajax():
            return HttpResponse("redirect: " + url)
        else:
            return HttpResponseRedirect(url)
        
    if request.is_ajax():
        return HttpResponse("0")
    else:
        return HttpResponseRedirect(project.get_url() + "?success=0")

@login_required
def unlist_self_from_wanna_help_do(request):
    wanna_help_form = mysite.project.forms.WannaHelpForm(request.POST)
    if wanna_help_form.is_valid():
        project = wanna_help_form.cleaned_data['project']
        project.people_who_wanna_help.remove(request.user.get_profile())
        mysite.search.models.WannaHelperNote.remove_person_project(request.user.get_profile(), project)
        return HttpResponseRedirect(project.get_url())
    else:
        return HttpResponseBadRequest("No project id submitted.")

@login_required
@mysite.base.decorators.view
def nextsteps4helpers(request):
    lucky_project = Project.objects.get(name='Ubuntu')
    context = {
            'the_lucky_project': lucky_project,
            'helpers': lucky_project.people_who_wanna_help.exclude(pk__exact=request.user.get_profile().pk)
            }
    return (request, "nextsteps4helpers.html", context)