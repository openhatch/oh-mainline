from mysite.search.models import Project, Answer, ProjectInvolvementQuestion
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

    questions = [q for q in p.questions.all()]
    return (request,
            'project/project.html',
            {
                'project': p,
                'contributors': p.get_contributors()[:3],
                'mentors': (mysite.profile.controllers.people_matching(
                    'can_mentor', project__name)),
                'language_mentors': (mysite.profile.controllers.people_matching(
                        'can_mentor', p.language)),
                'explain_to_anonymous_users': True,
                'questions': questions,
                'old_questions': {
                    'I want to join this project. Where do I begin?': 
                        {
                            'answers': [

                                (   """If you're interested in development, you can contribute
                                    by writing new software, packaging additional software, or
                                    fixing bugs in existing software.""",
                                    Person.objects.all()[0]),

                                (   """Join the Bug Squad! Help make Ubuntu even better by
                                    working with bug reports to ensure they're complete, 
                                    understandable and if possible, reproducable. Anyone can
                                    help!""",
                                    Person.objects.all()[0]),

                                (   """Help produce official documentation, share the solution
                                    to a problem, or check, proof and test other documents
                                    for accuracy.""",
                                    Person.objects.all()[0]),

                                ],

                            'input_note': 'Be sure to discuss coders and non-coders alike.'

                        },

                    "What sort of skills is this project looking for?":
                    
                        {

                            'answers': [

                                (   """Anyone can join! We just need gumption and pizzazz.""",
                                    Person.objects.all()[0]),

                                (   """@jsk, hhhactually non-coder clowns are quite annoying,
                                    can we have sum talent up in hiiya??""",
                                    Person.objects.all()[0]),

                                (   """We need smart, motivated people with a passion for
                                    learning and helping their communities. Also, more hot
                                    chicks..""",
                                    Person.objects.all()[0]),

                            ],

                            #'input_note': None

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
def create_answer_do(request):
    answer = Answer()

    question = ProjectInvolvementQuestion.objects.get(pk=request.POST['question__pk'])
    question.save()
    answer.question = question

    answer.text = request.POST['text']

    answer.author = request.user

    answer.save()
    
    return HttpResponse('1')
