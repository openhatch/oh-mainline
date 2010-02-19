from mysite.search.models import Project, ProjectInvolvementQuestion, Answer
from mysite.profile.models import Person
import django.template
import mysite.base.decorators
import mysite.profile.views

from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponsePermanentRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

import random

@mysite.base.decorators.view
def project(request, project__name = None):
    p = get_object_or_404(Project, name=project__name)

    pfentries = p.portfolioentry_set.exclude(project_description='')
    only_good_pfentries = lambda pfe: pfe.project_description.strip()
    pfentries = filter(only_good_pfentries, pfentries)

    context = {}
    if pfentries:
        context['random_pfentry'] = random.choice(pfentries)

    context['people'] = [pfe.person for pfe in pfentries]

    # Get or create two paragraph-y questions.
    questions = [
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='non_code_participation', is_bug_style=False)[0],
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='where_to_start', is_bug_style=False)[0],
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='stress', is_bug_style=True)[0],
            ProjectInvolvementQuestion.objects.get_or_create(
                    key_string='newcomers', is_bug_style=True)[0]
    ]
    context['question2answer'] = [(question, question.get_answers_for_project(p))
        for question in questions]

    context.update({
        'project': p,
        'contributors': p.get_contributors()[:3],
        'mentors': (mysite.profile.controllers.people_matching(
            'can_mentor', project__name)),
        'language_mentors': (mysite.profile.controllers.people_matching(
            'can_mentor', p.language)),
        'explain_to_anonymous_users': True,
        })
    return (request,
            'project/project.html',
            context
            )

@mysite.base.decorators.view
def projects(request):
    template = "project/projects.html"
    projects_with_bugs = mysite.search.controllers.get_projects_with_bugs()
    cited_projects_lacking_bugs = (mysite.search.controllers.
            get_cited_projects_lacking_bugs())
    data = {
            'projects_with_bugs': projects_with_bugs,
            'cited_projects_lacking_bugs': cited_projects_lacking_bugs,
            'explain_to_anonymous_users': True
            }
    return (request, template, data)


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

@login_required
def create_answer_do(request):
    if 'is_edit' in request.POST:
        answer = Answer.objects.get(pk=request.POST['answer__pk'])
    else:
        answer = Answer()

    question = ProjectInvolvementQuestion.objects.get(pk=request.POST['question__pk'])
    question.save()
    answer.question = question

    answer.text = request.POST['answer__text']

    answer.title = request.POST.get('answer__title', None)

    answer.author = request.user
    
    answer.project_id = request.POST['project__pk']

    answer.save()
    
    return HttpResponseRedirect(reverse(project, kwargs={'project__name': answer.project.name}))
