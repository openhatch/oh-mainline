import django.test
from search.models import Project

class NonJavascriptSearch(django.test.TestCase):
    fixtures = ['bugs-for-two-projects.json']

    def testSearch(self):
        response = self.client.get('/search/')
        for n in range(1, 11):
            self.assertContains(response, 'Title #%d' % n)
            self.assertContains(response, 'Description #%d' % n)

    def testMatchingBugsFromMtoN(self):
        # FIXME: This should test for 1 to 10, not 0 to 10
        response = self.client.get('/search/')
        self.assertContains(response, '0 to 10')

    

