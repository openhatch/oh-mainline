from django.core.mail import send_mail
import socket
from mysite.search.models import Project, ProjectInvolvementQuestion, Answer
from mysite.profile.models import Person
import mysite.project.controllers
import django.template
import mysite.base.decorators
import mysite.profile.views
import mysite.project.forms

from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponsePermanentRedirect, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import random

def create_project_page_do(request):
    project_name = request.POST.get('project_name', None)
    if project_name:
        matches = Project.objects.filter(name__iexact=project_name)
        if matches:
            our_project = matches[0]
        else:
            our_project, was_created = Project.objects.get_or_create(name=project_name)
        return HttpResponseRedirect(our_project.get_url())

    return HttpResponseBadRequest('Bad request')

@mysite.base.decorators.view
def project(request, project__name = None):
    p = get_object_or_404(Project, name=project__name)

    pfentries = p.portfolioentry_set.exclude(project_description='')
    only_good_pfentries = lambda pfe: pfe.project_description.strip()
    pfentries = filter(only_good_pfentries, pfentries)

    context = {}
    if pfentries:
        context['random_pfentry'] = random.choice(pfentries)

    # If description is too popular, and there are alternatives,
    # don't use the popular description. (This avoids a feeling of
    # 'Oh, everybody wrote the same thing.')
    # Calculate popularity case-insensitively.

    context['people'] = [pfe.person for pfe in pfentries]

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

    if request.GET.get('cookies', '') == 'disabled':
        context['cookies_disabled'] = True

    context.update({
        'project': p,
        'contributors': p.get_contributors()[:3],
        'mentors': (mysite.profile.controllers.people_matching(
            'can_mentor', project__name)),
        'language_mentors': (mysite.profile.controllers.people_matching(
            'can_mentor', p.language)),
        'explain_to_anonymous_users': True,
        'wanna_help_form': mysite.project.forms.WannaHelpForm(),
        'user_wants_to_help': request.user.is_authenticated() and request.user.get_profile() in p.people_who_wanna_help.all(),
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

from django.views.decorators.cache import cache_page
@cache_page(60 * 15)

def projects(request):
    data = {}
    query = request.GET.get('q', '')
    matching_projects = []
    project_matches_query_exactly = False
    if query:
        query = query.strip()
        matching_projects = mysite.project.controllers.similar_project_names(
            query)
        project_matches_query_exactly = query.lower() in [p.name.lower() for p in matching_projects]
        if len(matching_projects) == 1 and project_matches_query_exactly:
            return HttpResponseRedirect(matching_projects[0].get_url())
        
    if not query:
        data['projects_with_bugs'] = mysite.search.controllers.get_projects_with_bugs()
        data['cited_projects_lacking_bugs'] = (mysite.search.controllers.
                get_cited_projects_lacking_bugs())

    data.update({
            'query': query,
            'matching_projects': matching_projects,
            'no_project_matches_query_exactly': not project_matches_query_exactly,
            'explain_to_anonymous_users': True
            })
    return mysite.base.decorators.as_view(request, "project/projects.html", data,
            slug=projects.__name__)

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


    answer.project = mysite.search.models.Project.objects.get(pk=request.POST['project__pk'])


    question = ProjectInvolvementQuestion.objects.get(pk=request.POST['question__pk'])
    question.save()
    answer.question = question

    answer.text = request.POST['answer__text']

    answer.title = request.POST.get('answer__title', None)

    # loltrolled--you dont have cookies, so we will throw away your data at the last minute
    if (request.user.is_authenticated() or
        'cookies_work' in request.session):
        suffix = ''
    else:
        suffix = '?cookies=disabled'
        return HttpResponseRedirect(reverse(project, kwargs={'project__name': answer.project.name}) + suffix)

    answer.save()
    if answer.author is None:
        mysite.project.controllers.note_in_session_we_control_answer_id(request.session,
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

def wanna_help_do(request):
    wanna_help_form = mysite.project.forms.WannaHelpForm(request.POST)
    if wanna_help_form.is_valid():
        project = wanna_help_form.cleaned_data['project']
    else:
        return HttpResponseBadRequest("No project id submitted.")

    if request.user.is_authenticated():
        person = request.user.get_profile()
        project.people_who_wanna_help.add(person)
        project.save()

        if request.is_ajax():
            people_to_show = list(project.people_who_wanna_help.exclude(user=request.user))
            people_to_show.insert(0, person)
            
            t = django.template.loader.get_template('project/project-wanna-help-box.html')
            c = django.template.Context({
                'project': project,
                'person': request.user.get_profile(),
                'people_to_show': people_to_show,
                'just_added_myself': True})
            rendered = t.render(c)
            return HttpResponse(rendered)
        else:
            return HttpResponseRedirect(project.get_url() + "?success=1")
    else:
        # Then store a note in the session...
        wanna_help_queue = request.session.get('projects_we_want_to_help_out', [])
        wanna_help_queue.append(project.id)
        request.session['projects_we_want_to_help_out'] = wanna_help_queue
        
        # If user isn't logged in, send them to the login page with next
        # parameter populated.
        url = reverse('oh_login')
        url += "?" + mysite.base.unicode_sanity.urlencode({u'next':
            unicode(project.get_url()) + '?wanna_help=true'})
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
        return HttpResponseRedirect(project.get_url())
    else:
        return HttpResponseBadRequest("No project id submitted.")

