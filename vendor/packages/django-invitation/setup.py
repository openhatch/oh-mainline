from setuptools import setup, find_packages
 
setup(
    name='django-invitation',
    version='1.0',
    description='Built on top of django-registration, it restricts registration to a given number of invited person per active user (strategy introduced by GMail to involve 2.0 users).',
    author='David Larlet',
    author_email='david@larlet.fr',
    url='http://code.welldev.org/django-invitation/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    # Make setuptools include all data files under version control,
    # svn and CVS by default
    include_package_data=True,
    zip_safe=False,
    # Tells setuptools to download setuptools_hg before running setup.py so
    # it can find the data files under Hg version control.
    setup_requires=['setuptools_hg'],
)
