try:
    import ez_setup
    ez_setup.use_setuptools()

    from setuptools import setup
except ImportError:
    from distuils.core import setup

setup(
    name = 'typecheck',
    version = '0.3.5',
    description = 'A runtime type-checking module for Python',
    
    long_description = """A runtime type-checking module for Python supporting both parameter-type checking and return-type checking for functions, methods and generators.

The main workhorses of this module, the functions `accepts` and `returns`, are used as function/method decorators. A `yields` decorator provides a mechanism to typecheck the values yielded by generators.

Four utility classes, IsAllOf(), IsOneOf(), IsNoneOf() and IsOnlyOneOf() are provided to assist in building more complex signatures by creating boolean expressions based on classes and/or types.

A number of other utility classes exist to aid in type signature creation; for a full list, see the README.txt file or the project's website.
    
The module also includes support for type variables, a concept borrowed from languages such as Haskell.""",
    
    author = 'Collin Winter',
    author_email = 'collinw@gmail.com',
    url = 'http://oakwinter.com/code/typecheck/',
    license = 'MIT License',
    classifiers = [     
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',       
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords = 'python decorator type-check typesafe typesafety type typing static',    
    packages = ['typecheck']
)
