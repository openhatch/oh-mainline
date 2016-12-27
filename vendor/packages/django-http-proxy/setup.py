from setuptools import setup, find_packages
import versioneer


packages = find_packages()

versioneer.VCS = 'git'
versioneer.versionfile_source = '{0}/_version.py'.format(packages[0])
versioneer.tag_prefix = ''
versioneer.parentdir_prefix = ''

setup(
    name='django-http-proxy',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='A simple HTTP proxy for the Django framework.',
    author='Yuri van der Meer',
    author_email='contact@yvandermeer.net',
    url='http://django-http-proxy.readthedocs.org/',
    packages=find_packages(),
    install_requires=[
        'Django>=1.1',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
