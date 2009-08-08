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
                       ],

    dependency_links = ['http://linode.openhatch.org/~paulproteus/',
                        'http://linode.openhatch.org/~paulproteus/python_apt-0.6.17-py2.6-linux-i686.egg#egg=python-apt',
                       ],

    zip_safe = False,
    include_package_data = True,

    description = "A website",

    author = 'Asheesh Laroia, Raphael Krut-Landau, Karen Rustad',
    author_email = 'all@openhatch.org',

    package_dir = {'': '.'},

)

