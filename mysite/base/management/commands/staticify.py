import logging
import sys
import os
import urllib

from django.core.management.base import BaseCommand
from django.http import Http404, HttpRequest
import django.contrib.auth.models
from django.test import Client
import tempfile
import datetime
import time
import email.utils

logger = logging.getLogger(__name__)

import UserDict
class FakeSession(UserDict.UserDict):
    def set_test_cookie(self, *args, **kwargs):
        pass
    def test_cookie_worked(self):
        return True
    def delete_test_cookie(self, *args, **kwargs):
        pass

def mkdirp(fulldir):
    sofar = ''
    for subdir in fulldir.split('/'):
        sofar += subdir + '/'
        if os.path.exists(sofar):
            continue
        else:
            os.mkdir(sofar)

class Command(BaseCommand):
    help = 'Generates, then serves, a static version of this website'

    @staticmethod
    def is_redirect(pattern):
        try:
            response = pattern.callback(None)
        except (AttributeError, TypeError, AssertionError, Http404):
            return False
        if response.status_code in [301, 302]:
            return True
        return False

    @staticmethod
    def get_urls():
        import mysite.urls  # late import to avoid circular import breakage
        import random
        random.seed(0)  # For predictability when we shuffle mysite.urls
        patterns = list(mysite.urls.urlpatterns)  # copy, so we can shuffle safely
        random.shuffle(patterns)

        # Get rid of django debug toolbar
        patterns = [p for p in patterns if getattr(p, 'app_name', None) != 'djdt']

        # Get rid of intentionally-crashing urls
        patterns = [p for p in patterns if p.regex.pattern not in [
            '^account/catch-me$',
            '^test_404$',
        ]]

        # Get rid of unintentionally crashing URLs, either because they require query string
        # data, or because of partial refactors that never completed.
        patterns = [p for p in patterns if p.regex.pattern not in [
            r'^\+landing/import$',
            r'^\+landing/projects$',
            r'^\+landing/opps$',
            r'^profile/views/replace_icon_with_default$',
        ]]

        # Get rid of weird things with no .callback
        patterns = [p for p in patterns if p.callback]

        # Get rid of unsubscribe system URL
        patterns = [p for p in patterns if p.regex.pattern != '^-profile.views.unsubscribe_do']

        # For now, get rid of URLs with matching in their regex
        patterns = [p for p in patterns if '(' not in p.regex.pattern]

        # Get rid of redirects
        patterns = [p for p in patterns if not Command.is_redirect(p)]

        return patterns

    @staticmethod
    def response_to_html(response):
        if response.status_code == 200:
            if hasattr(response, 'render'):
                response.render()
                return response.rendered_content
            else:
                return response.content
        if response.status_code in [301, 302]:
            loc = response['Location']
            return '''<meta http-equiv="refresh" content="0;URL='%s'">''' % (
                urllib.quote(loc),)

    @staticmethod
    def path_to_dirname_and_filename(path):
        if path.endswith('/'):
            path = path + 'index.html'
        return (os.path.dirname(path), path)


    @staticmethod
    def save_urls(patterns):
        import sre_yield  # Note: This is not packaged in oh-mainline! You need to pip install it.
        OUT_DIR = tempfile.mkdtemp(dir='./', prefix=str(email.utils.formatdate(time.mktime(datetime.datetime.now().timetuple()))) + '.')
        failed = []
        for pattern in patterns:
            # Generate an output URL
            p = pattern.regex.pattern

            # Strip anchors b/c sre_yield is confused by them.
            if p[0] == '^':
                p = p[1:]
            if p[-1] == '$':
                p = p[:-1]
            try:
                one_string = iter(sre_yield.AllStrings(p)).next()
            except StopIteration:
                raise ValueError, "Could not generate a matching string for pattern", p
            one_string = one_string.replace('\x00', '.')  # sre_yield generates null bytes, but we meant literal dots
            if one_string == '':
                one_string = '/'

            if not one_string[0] == '/':
                one_string = '/' + one_string # all URL paths start with /

            c = Client()
            try:
                response = c.get(one_string)
            except:
                failed.append(pattern.regex.pattern)
                continue

            if response.status_code == 400:
                continue
            if response.status_code == 500 and response.content.strip() == "Oops, you're not logged in.":
                continue

            ADD_SLASHES = set([
                '/missions/svn/diff',
                '/missions/shell/cd',
                '/missions/git/checkout',
                '/missions/git/rebase',
                '/missions/git/description',
                '/missions/shell/create-and-remove',
                '/missions/pipvirtualenv/installing_packages',
                '/missions/git/diff',
            ])
            if one_string in ADD_SLASHES:
                one_string = one_string + '/'

            if one_string == '/missions/shell/ls':
                # TODO: Remove this hack
                one_string = 'missions/shell/ls/'
            if one_string == '/missions/pipvirtualenv':
                # TODO: Remove this hack
                one_string = 'missions/pipvirtualenv/'
            if one_string == '/missions/pipvirtualenv/removing_packages':
                # TODO: Remove this hack
                one_string = 'missions/pipvirtualenv/removing_packages/'
            if one_string == '/missions/tar':
                # TODO: Remove this hack
                one_string = 'missions/tar/'
            if one_string == '/missions/diffpatch':
                # TODO: Remove this hack
                one_string = 'missions/diffpatch/'
            if one_string == '/missions/svn/commit':
                # TODO: Remove this hack
                one_string = 'missions/svn/commit/'
            if one_string == '/missions/svn/checkout':
                # TODO: Remove this hack
                one_string = 'missions/svn/checkout/'
            if one_string == '/missions/irc':
                # TODO: Remove this hack
                one_string = 'missions/irc/'
            if one_string == '/missions/shell/copy-and-move':
                # TODO: Remove this hack
                one_string = 'missions/shelll/copy-and-move/'
            if one_string == '/missions/git':
                # TODO: Remove this hack
                one_string = 'missions/git/'
            if one_string == '/missions/svn':
                # TODO: Remove this hack
                one_string = 'missions/svn/'


            # r = HttpRequest()
            # r.path = one_string
            # r.user = django.contrib.auth.models.AnonymousUser()
            # r.method = 'GET'
            # r.META['SERVER_NAME'] = 'openhatch.org'
            # r.META['SERVER_PORT'] = 443
            # r.REQUEST = {}
            # r.session = FakeSession()
            # response = pattern.callback(r)
            dirname, filename = Command.path_to_dirname_and_filename(one_string)
            page_content = Command.response_to_html(response)
            try:
                mkdirp(OUT_DIR + '/' + dirname)
            except:
                failed.append(dirname)
                continue
            try:
                with open(OUT_DIR + '/' + filename, 'w') as fd:
                    fd.write(page_content)
            except IOError:
                failed.append(filename)
        print 'failures', failed


    def handle(self, *args, **options):
        patterns = self.get_urls()
        self.save_urls(patterns)
