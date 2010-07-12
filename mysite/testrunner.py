from django.conf import settings
import xmlrunner.extra.djangotestrunner
from django.test.simple import run_tests
import tempfile
import os
import datetime

def override_settings_for_testing():
    settings.CELERY_ALWAYS_EAGER = True
    settings.SVN_REPO_PATH = tempfile.mkdtemp(
        prefix='svn_repo_path_' +
        datetime.datetime.now().isoformat().replace(':', '.'))

def run(*args, **kwargs):
    override_settings_for_testing()

    if os.environ.get('USER', 'unknown') == 'hudson':
        # Hudson should run with xmlrunner because he consumes
        # JUnit-style xml test reports.
        return xmlrunner.extra.djangotestrunner.run_tests(*args, **kwargs)
    else:
        # Those of us unfortunate enough not to have been born
        # Hudson should use the normal test runner, because
        # xmlrunner swallows input, preventing interaction with
        # pdb.set_trace(), which makes debugging a pain!
        return run_tests(*args, **kwargs)
