# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
# Copyright (C) 2010 John Stumpo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
import xmlrunner.extra.djangotestrunner
import django.test.simple
import tempfile
import os
import sys
import datetime
import random
import subprocess
import signal
import logging
import mysite.base.depends


def generate_safe_temp_file_name():
    fd, name = tempfile.mkstemp()
    os.close(fd)
    return name


def override_settings_for_testing():
    settings.CELERY_ALWAYS_EAGER = True
    settings.SVN_REPO_PATH = tempfile.mkdtemp(
        prefix='svn_repo_path_' +
        datetime.datetime.now().isoformat().replace(':', '.'))
    settings.GITHUB_USERNAME = 'openhatch-api-testing'
    settings.GITHUB_API_TOKEN = '4a48b94a0f16c4483fee4cf6c46425e8'
    settings.POSTFIX_FORWARDER_TABLE_PATH = generate_safe_temp_file_name()

    svnserve_port = random.randint(50000, 50100)
    if mysite.base.depends.svnadmin_available():
        subprocess.check_call(['svnserve',
                               '--listen-port', str(svnserve_port),
                               '--listen-host', '127.0.0.1',
                               '--daemon',
                               '--pid-file', os.path.join(settings.SVN_REPO_PATH,
                                                          'svnserve.pid'),
                               '--root', settings.SVN_REPO_PATH])
    settings.SVN_REPO_URL_PREFIX = 'svn://127.0.0.1:%d/' % svnserve_port


def cleanup_after_tests():
    if mysite.base.depends.svnadmin_available():
        pidfile = os.path.join(settings.SVN_REPO_PATH, 'svnserve.pid')
        pid = int(open(pidfile).read().strip())
        os.kill(pid, signal.SIGTERM)
        os.unlink(pidfile)
    try:
        os.unlink(settings.POSTFIX_FORWARDER_TABLE_PATH)
    except IOError:
        pass


class OpenHatchTestRunner(django.test.simple.DjangoTestSuiteRunner):

    def run_tests(self, *args, **kwargs):
        if not args or not args[0]:
            logging.info(
                "You did not specify which tests to run. I will run all the OpenHatch-related ones.")
            args = (['base', 'profile', 'account', 'project',
                    'missions', 'search', 'customs'],)

        override_settings_for_testing()
        n = 1
        try:
            n = super(OpenHatchTestRunner, self).run_tests(*args, **kwargs)
        finally:
            cleanup_after_tests()
            sys.exit(n)


class OpenHatchXMLTestRunner(xmlrunner.extra.djangotestrunner.XMLTestRunner):

    def run_tests(self, *args, **kwargs):
        if not args or not args[0]:
            logging.info(
                "You did not specify which tests to run. I will run all the OpenHatch-related ones.")
            args = (['base', 'profile', 'account', 'project',
                    'missions', 'search', 'customs'],)

        override_settings_for_testing()
        n = 1
        try:
            n = super(OpenHatchXMLTestRunner, self).run_tests(*args, **kwargs)
        finally:
            cleanup_after_tests()
            sys.exit(n)
