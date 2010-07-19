from django.conf import settings
import xmlrunner.extra.djangotestrunner
from django.test.simple import run_tests
import tempfile
import os
import datetime
import random
import subprocess
import signal

def override_settings_for_testing():
    settings.CELERY_ALWAYS_EAGER = True
    settings.SVN_REPO_PATH = tempfile.mkdtemp(
        prefix='svn_repo_path_' +
        datetime.datetime.now().isoformat().replace(':', '.'))
    settings.GITHUB_USERNAME='openhatch-api-testing'
    settings.GITHUB_API_TOKEN='4a48b94a0f16c4483fee4cf6c46425e8'

    svnserve_port = random.randint(50000, 50100)
    subprocess.check_call(['svnserve',
        '--listen-port', str(svnserve_port),
        '--listen-host', '127.0.0.1',
        '--daemon',
        '--pid-file', os.path.join(settings.SVN_REPO_PATH, 'svnserve.pid'),
        '--root', settings.SVN_REPO_PATH])
    settings.SVN_REPO_URL_PREFIX = 'svn://127.0.0.1:%d/' % svnserve_port

def cleanup_after_tests():
    pidfile = os.path.join(settings.SVN_REPO_PATH, 'svnserve.pid')
    pid = int(open(pidfile).read().strip())
    os.kill(pid, signal.SIGTERM)
    os.unlink(pidfile)

def run(*args, **kwargs):
    override_settings_for_testing()

    try:
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
    finally:
        cleanup_after_tests()
