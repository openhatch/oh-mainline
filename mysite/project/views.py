from mysite.search.models import Project, ProjectInvolvementQuestion, Answer, BugAnswer
from mysite.profile.models import Person
import django.template
import mysite.base.decorators
import mysite.profile.views

from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponsePermanentRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

@mysite.base.decorators.view
def project(request, project__name = None):
    p = get_object_or_404(Project, name=project__name)

    question_answer_mappings_non_bug = []
    questions = ProjectInvolvementQuestion.objects.filter(is_bug_style=False)
    for question in questions:
        question_answer_mappings_non_bug.append((question, question.get_answers_for_project(p)))

    question_answer_mappings_bug = []
    questions = ProjectInvolvementQuestion.objects.filter(is_bug_style=True)
    for question in questions:
        question_answer_mappings_bug.append((question, question.get_answers_for_project(p)))

    return (request,
            'project/project.html',
            {
                'project': p,
                'question_answer_mappings_non_bug': question_answer_mappings_non_bug,
                'question_answer_mappings_bug': question_answer_mappings_bug,
                'contributors': p.get_contributors()[:3],
                'mentors': (mysite.profile.controllers.people_matching(
                    'can_mentor', project__name)),
                'language_mentors': (mysite.profile.controllers.people_matching(
                        'can_mentor', p.language)),
                'explain_to_anonymous_users': True,
                'query': {'terms': []}, # hack to make the bug result template inclusion work
                'old_questions': {
                    'I want to join this project. Where do I begin?': 
                        {

                            'input_note': 'Be sure to discuss coders and non-coders alike.'

                        },

                    "What sort of skills is this project looking for?":
                    
                        {


                        }

                    }
                },
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
def delete_bug_answer_do(request):
    pass

@login_required
def delete_paragraph_answer_do(request):
    answer__pk = request.POST['answer__pk']
    # grab the answer from the database.  delete it.  done.
    our_answer = Answer.objects.get(pk=answer__pk, author=request.user)
    our_answer.delete()
    return HttpResponseRedirect(reverse(project, kwargs={'project__name': our_answer.project.name}))

@login_required
def create_bug_answer_do(request):
    answer = BugAnswer()

    question = ProjectInvolvementQuestion.objects.get(pk=int(request.POST['question__pk']))
    question.save()
    answer.question = question

    answer.url = request.POST['bug__url']
    answer.title = request.POST['bug__title']
    answer.details = request.POST['bug__details']

    answer.author = request.user
    
    answer.project_id = int(request.POST['project__pk'])

    answer.save()
    
    return HttpResponseRedirect(reverse(project, kwargs={'project__name': answer.project.name}))

@login_required
def create_answer_do(request):
    answer = Answer()

    question = ProjectInvolvementQuestion.objects.get(pk=request.POST['question__pk'])
    question.save()
    answer.question = question

    answer.text = request.POST['answer__text']

    answer.author = request.user
    
    answer.project_id = request.POST['project__pk']

    answer.save()
    
    return HttpResponseRedirect(reverse(project, kwargs={'project__name': answer.project.name}))
