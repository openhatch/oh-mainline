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
                        'BeautifulSoup',
                        'twill',
                        'lxml',
                        'python-dateutil',
                        'decorator',
                        'MySQL-python',
                        'simplejson',
                        'pytz',
                        'python-apt',
                        'python-openid',
                        'windmill',
                        'south',
                        'typecheck',
                        'celery',
                        'odict',
                        'python-launchpad-bugs',
                        'mock',
                        'django-registration',
                        'django-authopenid',
                       ],

    dependency_links = ['http://linode.openhatch.org/~paulproteus/',
                        ],

    zip_safe = False,
    include_package_data = True,

    description = "A website",

    author = 'Asheesh Laroia, Raphael Krut-Landau, Karen Rustad',
    author_email = 'all@openhatch.org',

    package_dir = {'': '.'},

)

