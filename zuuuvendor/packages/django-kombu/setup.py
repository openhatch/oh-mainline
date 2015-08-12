#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import codecs

try:
    from setuptools import setup, find_packages, Command
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages, Command

from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import sys

import djkombu

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
src_dir = "djkombu"

install_requires = []


def osx_install_data(install_data):

    def finalize_options(self):
        self.set_undefined_options("install", ("install_lib", "install_dir"))
        install_data.finalize_options(self)


class RunTests(Command):
    description = "Run the django test suite from the testproj dir."

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        this_dir = os.getcwd()
        testproj_dir = os.path.join(this_dir, "testproj")
        os.chdir(testproj_dir)
        sys.path.insert(0, testproj_dir)
        from django.core.management import execute_manager
        os.environ["DJANGO_SETTINGS_MODULE"] = os.environ.get(
                        "DJANGO_SETTINGS_MODULE", "settings")
        settings_file = os.environ["DJANGO_SETTINGS_MODULE"]
        settings_mod = __import__(settings_file, {}, {}, [''])
        execute_manager(settings_mod, argv=[
            __file__, "test"])
        os.chdir(this_dir)


def fullsplit(path, result=None):
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

SKIP_EXTENSIONS = [".pyc", ".pyo", ".swp", ".swo"]


def is_unwanted_file(filename):
    for skip_ext in SKIP_EXTENSIONS:
        if filename.endswith(skip_ext):
            return True
    return False


for dirpath, dirnames, filenames in os.walk(src_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."):
            del dirnames[i]
    for filename in filenames:
        if filename.endswith(".py"):
            packages.append('.'.join(fullsplit(dirpath)))
        elif is_unwanted_file(filename):
            pass
        else:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in
                filenames]])

if os.path.exists("README.rst"):
    long_description = codecs.open("README.rst", "r", "utf-8").read()
else:
    long_description = "See http://pypi.python.org/pypi/django-kombu"

setup(
    name='django-kombu',
    version=djkombu.__version__,
    description=djkombu.__doc__,
    author=djkombu.__author__,
    author_email=djkombu.__contact__,
    url=djkombu.__homepage__,
    platforms=["any"],
    license='BSD',
    packages=packages,
    data_files=data_files,
    cmdclass={"test": RunTests},
    zip_safe=False,
    test_suite="nose.collector",
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    long_description=long_description,
)
