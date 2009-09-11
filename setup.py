import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "mysite",
    version = "3",
    packages = ['mysite',],
    url = 'http://openhatch.org/',
    license = 'Proprietary',

    install_requires = ['setuptools',
                        'python-distutils-extra',
                        'twill==0.9.1-cc',
                        'invitation',
                        'celery==0.6.0',
                        'south==0.6-rc1',
                        'multiprocessing==2.6.2.1-oh',
                       ],

    dependency_links = ['http://linode.openhatch.org/~paulproteus/',
                        'http://linode.openhatch.org/~paulproteus/python_apt-0.6.17-py2.6-linux-i686.egg#egg=python-apt',
                        'http://linode.openhatch.org/~paulproteus/invitation-1.0.tar.gz#egg=invitation',
                        'http://linode.openhatch.org/~paulproteus/multiprocessing-2.6.2.1-oh.tar.gz#egg=multiprocessing',
                        'http://linode.openhatch.org/~paulproteus/South-0.6_pre-py2.6.egg#egg=south',
                       ],

    zip_safe = False,
    include_package_data = True,

    description = "A website",

    author = 'Asheesh Laroia, Raphael Krut-Landau, Karen Rustad',
    author_email = 'all@openhatch.org',

    package_dir = {'': '.'},

)

