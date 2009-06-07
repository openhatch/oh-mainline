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
        response = self.client.get('/search/')
        self.failUnlessEqual(response.context['start'], 1)
        self.failUnlessEqual(response.context['end'], 10)
        

