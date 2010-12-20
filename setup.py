# This file:
# 1. Provides metadata about the openhatch codebase. This metadata creates a Python "package". This is done by the call to the setup() function -- for example, the "name" parameter sets the name of the package.
# 2. In doing so, it declares the most urgent dependencies without which the code will not function. That is done through the "install_requires" parameter to setup().
# 3. We hard-code URLs to retrieve some of those dependencies. This is usually because the upstream project has put a broken URL on pypi.python.org, or because we host a specially-patched version.

import os
from setuptools import setup

# This is a common idiom for setup.py files.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# If we host a copy of a package for any reason, we typically
# host it here:
dependency_path = 'http://linode.openhatch.org/~paulproteus/'

# The call to setup() is the important part of the file.
setup(
    name = "mysite",
    version = "3", # We don't really do releases, so every version is version 3.
    packages = ['mysite',],
    url = 'https://openhatch.org/',
    license = 'AGPLv3',

    install_requires = ['setuptools',
                        'python-distutils-extra',
                        'twill==0.9.1-cc',
                        'invitation',
                        'django-authopenid==1.0.1-openhatch1',
                        'celery==1.0.5',
                        'south==0.6-rc1',
                        'launchpadlib',
                        'django-assets==0.2.1',
                        'python-github2==0.1.1',
                        'pygeoip==0.1.3',
                        'django-debug-toolbar==0.8.1',
                        'keyring==0.5.0.1',
                        'pysolr',
                        'sisynala',
                        'django-haystack',
                        'hexagonit.recipe.download',
                        'django-registration>0.7',
                        'django-voting',
                        'staticgenerator==1.4.1.2-openhatch',
                        'python-otp',
                        'python-launchpad-bugs',
                        'html2text',
                        'lockfile>=0.9', # as of this writing, pypi only has version 0.8
                        'python-openid==2.2.5', # as of this writing, upstream has an HTML file where a tar.gz should be
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
                        dependency_path + 'python-openid-2.2.5.tar.gz#egg=python-openid',
                        dependency_path + 'keyring-0.5.0.1.tar.gz#egg=keyring',
                        dependency_path + 'python_apt-0.6.17-py2.6-linux-i686.egg#egg=python-apt',
                        dependency_path + 'invitation-1.0.tar.gz#egg=invitation',
                        dependency_path + 'django-assets-0.2.1.tar.gz#egg=django-assets',
                        dependency_path + 'South-0.6_pre-py2.6.egg#egg=south',
                        dependency_path + 'django-authopenid-1.0.1-openhatch1.tar.gz#egg=django-authopenid',
                        dependency_path + 'python-launchpad-bugs-0.3.6.tar.gz#egg=python-launchpad-bugs',
                        'http://linode.openhatch.org/~paulproteus/python-github2-0.1.1.tar.gz#egg=python-github2',
                        'http://pygeoip.googlecode.com/files/pygeoip-0.1.3.zip#egg=pygeoip',
                        'http://linode.openhatch.org/~rafpaf/django-debug-toolbar-0.8.1.tar.gz#egg=django-debug-toolbar',
                        'http://linode.openhatch.org/~parker/django-voting-0.1.tar.gz#egg=django-voting',
                        dependency_path + 'staticgenerator-1.4.1.2-openhatch.tar.gz#egg=staticgenerator',
                        dependency_path + 'python-otp.tar.gz#egg=python-otp',
                       ],

    # FIXME: Write a reasonable comment about zip_safe and include_package_data
    zip_safe = False,
    include_package_data = True,

    description = "A website",

    author = 'The OpenHatch team <http://openhatch.org/about/> <http://openhatch.org/+projects/OpenHatch>',
    author_email = 'all@openhatch.org',

    package_dir = {'': '.'},

)
