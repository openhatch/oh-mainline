from mysite.base.tests import make_twill_url, TwillTests
from mysite.search.models import Project, ProjectInvolvementQuestion, Answer
from mysite.profile.models import Person
from django.core.urlresolvers import reverse

class CreateAnswer(TwillTests):
    fixtures = ['user-paulproteus']

    def test_create_answer(self):

        p = Project.create_dummy()
        q = ProjectInvolvementQuestion.create_dummy(project=p)

        # POST some text to the answer creation post handler
        POST_data = {
                'question__pk': q.pk,
                'text': """Help produce official documentation, share the
                    solution to a problem, or check, proof and test other
                    documents for accuracy.""",
                    }
        response = self.login_with_client().post(reverse(mysite.project.views.create_answer_do), POST_data)
        self.assertEqual(response.content, '1')

        # check that the db contains a record with this text
        try:
            record = Answer.objects.get(text=POST_data['text'])
        except Answer.DoesNotExist:
            print "All Answers:", Answer.objects.all()
            raise Answer.DoesNotExist 
        self.assertEqual(record.author, Person.get_by_username('paulproteus'))

        # check that the project page now includes this text
        project_page = self.client.get(q.project.get_url())
        self.assertContains(project_page, POST_data['text'])

# vim: set nu ai et ts=4 sw=4 columns=100:
