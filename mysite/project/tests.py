from mysite.base.tests import TwillTests
import mysite

class Answer(TwillTests):

    def test_add_answer(self):

        p = Project.create_dummy()
        q = ProjectInvolvementQuestion.create_dummy(project=p)

        self.login_with_client()

        # POST some text to the answer creation post handler
        POST_data = {
                'question__pk': q.pk,
                'text': """Help produce official documentation, share the
                    solution to a problem, or check, proof and test other
                    documents for accuracy.""",
                    }
        self.client.post(reverse(mysite.project.views.create_answer_do), POST_data)

        # check that the db contains a record with this text
        record = Answer.objects.filter(text=POST_data['text'])
        self.assertEqual(record.user, User.objects.get(username='paulproteus'))

        # check that the project page now includes this text
        self.assertContains(self.client.get(project.get_url(), POST_data['text']), 

# vim: set nu ai et ts=4 sw=4 columns=100:
