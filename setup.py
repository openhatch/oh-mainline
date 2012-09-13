# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 Jeff Welling
# Copyright (C) 2009, 2010, 2011 OpenHatch
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

# This file:
# 1. Provides metadata about the openhatch codebase. This metadata creates a Python "package". This is done by the call to the setup() function -- for example, the "name" parameter sets the name of the package.
# 2. In doing so, it declares the most urgent dependencies without which the code will not function. That is done through the "install_requires" parameter to setup().
# 3. We hard-code URLs to retrieve some of those dependencies. This is usually because the upstream project has put a broken URL on pypi.python.org, or because we host a specially-patched version.

__version__ = '0.11.12'

import os, sys
from setuptools import setup

# If we host a copy of a package for any reason, we typically
# host it here:
dependency_path = 'http://linode.openhatch.org/~paulproteus/'


# This is a common idiom for setup.py files.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def main(argv=None):
    if argv is None:
        argv = sys.argv

    # The call to setup() is the important part of the file.
    setup(
        name = "mysite",
        version = "0.11.12",
        packages = ['mysite',],
        url = 'https://openhatch.org/',
        license = 'AGPLv3',

        install_requires = ['setuptools',
                            'python-distutils-extra',
                            'twill==0.9.1-cc',
                            'invitation',
                            'django-authopenid==1.0.1-openhatch2',
                            'celery==2.2.7',
                            'launchpadlib',
                            'django-assets==0.2.1',
                            'django-kombu==0.9.4',
                            'python-github2==0.1.1',
                            'pygeoip==0.1.3',
                            'django-debug-toolbar==0.8.4',
                            'mechanize',
                            'keyring==0.5.0.1',
                            'pysolr',
                            'South>=0.7.3.1',
                            'sisynala',
                            'hexagonit.recipe.download',
                            'django-registration>0.7',
                            'django-voting',
                            'staticgenerator==1.4.1.2-openhatch',
                            'python-otp',
                            'python-launchpad-bugs==0.3.6.openhatch1',
                            'html2text',
                            'lockfile>=0.9', # as of this writing, pypi only has version 0.8
                            'python-openid==2.2.5-openhatch1', # as of this writing, upstream has an HTML file where a tar.gz should be
                            'sessionprofile==1.0',
                            'django-model-utils',
                            'tastypie',
                           ],

        # dependency_links is a list of URLs. If you need to override the URL
        # for a package called "foo", specify a URL like
        # "http://example.com/#egg=foo in this list.
        # You might wonder why it's #egg=foo not #name=foo. It's because
        # Python packages are called "eggs.
        # For dependencies that don't have a special path listed here,
        # buildout will search for the code on http://pypi.python.org/.
        # You might have noticed that some dependencies are listed here,
        # whereas *all* are listed in buildout.cfg. We list some here so we
        # can override their download URL.
        dependency_links = [dependency_path,
                            'http://pylockfile.googlecode.com/files/lockfile-0.9.tar.gz#egg=lockfile',
                            'http://pygeoip.googlecode.com/files/pygeoip-0.1.3.zip#egg=pygeoip',
                            'http://linode.openhatch.org/~paulproteus/django-debug-toolbar-0.8.4.tar.gz#egg=django-debug-toolbar',
                            'http://pypi.python.org/packages/source/d/django-model-utils/django-model-utils-0.6.0.tar.gz#egg=django-model-utils',
                           ],

        # FIXME: Write a reasonable comment about zip_safe and include_package_data
        zip_safe = False,
        include_package_data = True,

        description = "A website",

        author = 'The OpenHatch team <http://openhatch.org/about/> <http://openhatch.org/+projects/OpenHatch>',
        author_email = 'all@openhatch.org',

        package_dir = {'': '.'},

    )

if __name__ == "__main__":
    sys.exit(main())
