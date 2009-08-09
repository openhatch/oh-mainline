# {{{ Imports
from mysite.base.tests import make_twill_url, TwillTests
# }}}

class Form(TwillTests):
    fixtures = ['person-paulproteus.json', 'user-paulproteus.json']

    def test_form_post_handler(self):
        client = self.login_with_client()
        bug_data = {'before': 'I was singing "Ave Maria" to a potful of dal.', 
                    'expected_behavior': 'I expected the dal to be stirred.', 
                    'actual_behavior': 'Instead, burnination.'}
        json = client.post('/senseknocker/handle_form', bug_data)

        # Check there exists at least one bug with the given characteristics
        # in the DB. (There can be more than one, hypothechnically.)
        self.assert_(list(senseknocker.Bug.objects.filter(
                before=bug_data['before'], 
                expected_behavior=bug_data['expected_behavior'],
                actual_behavior=bug_data['actual_behavior']
                )))
        self.assertEqual(json.content, '[{"success": 1}]')
