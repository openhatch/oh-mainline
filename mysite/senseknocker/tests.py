# {{{ Imports
from mysite.base.tests import make_twill_url, TwillTests
# }}}

class Form(TwillTests):
    fixtures = ['person-paulproteus.json', 'user-paulproteus.json']

    def test_form_post_handler(self):
        client = self.login_with_client()
        json = client.post('/senseknocker/handle_form', {
                    'before': 'I was singing "Ave Maria" to a potful of dal.', 
                    'expected_behavior': 'I expected the dal to be stirred.', 
                    'actual_behavior': 'Instead, burnination.'})
        # Once we have a bug tracker,
        # check that the POST handler actually added a bug.
        self.assertEqual(json.content, '[{"success": 1}]')
