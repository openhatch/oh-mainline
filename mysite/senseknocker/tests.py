from mysite.base.tests import make_twill_url, TwillTests
from mysite import senseknocker

class Form(TwillTests):
    fixtures = ['person-paulproteus.json', 'user-paulproteus.json']

    def test_form_post_handler(self):
        client = self.login_with_client()
        bug_data = {'background': 'I was singing "Ave Maria" to a potful of dal.', 
                    'expected_behavior': 'I expected the dal to be stirred.', 
                    'actual_behavior': 'Instead, burnination.'}
        json = client.post('/senseknocker/handle_form', bug_data)

        # Check there exists at least one bug with the given characteristics
        # in the DB. (There can be more than one, hypothechnically.)
        bugs = list(senseknocker.models.Bug.objects.filter(
            background=bug_data['background'], 
            expected_behavior=bug_data['expected_behavior'],
            actual_behavior=bug_data['actual_behavior']
            ))
        import pdb
        pdb.set_trace()
        self.assert_(bugs)
        self.assertEqual(json.content, '[{"success": 1}]')
