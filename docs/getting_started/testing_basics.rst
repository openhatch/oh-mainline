==============
Testing Basics
==============

OpenHatch strives to follow best practices for testing. One
common practice in the Python community is Test Driven Development (TDD).
In TDD, a developer will write a test for a new feature before creating
the feature's source code.


Running the OpenHatch test suite
================================

You may run the test suite to see if all tests pass before you begin
making changes to the code. To run the test suite,::

    python manage.py test

The test suite begin running all of the tests and will display the test
progress in the console window.


Running the test suite without warnings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may run the test suite and turn off warnings, such as "deprecation
warnings", being output to your screen. To run the test suite without
warnings,::

    python -Wignore manage.py test

The test suite will display its progress on the console but will not display
any warnings.


Running a subset of tests
~~~~~~~~~~~~~~~~~~~~~~~~~

If you are working on a particular area of the source code, you may find
it helpful to run a subset of the tests. You may pass an argument after
the ``python manage.py test`` command.

Currently, you may pass one or more of the following arguments: `account`,
`base`, `missions`, `project`, `search`, and `customs`. For example,::

    python manage.py test missions

will run all the tests related to the OpenHatch missions.


Controlling detail of test output
#################################

You can use ``--verbosity`` or ``-v`` to specify the amount of notification and
debug information that should be printed to the console.

* 0 means minimal output.
* 1 means normal output (default).
* 2 means verbose output.
* 3 means very verbose output.

For example,::

    python manage.py test -v2

will run all the tests and display a more verbose output.


Additional testing information
==============================

The Internals section of this documentation contains more detailed information
about the test suite, `advanced testing`_, and `continuous integration`_.

If you'd like to learn more about testing, we strongly recommend going through
`Ned Batchelder's`_ blog post `Getting Started Testing`_.

.. _advanced testing: ../advanced/advanced_testing.html
.. _continuous integration: ../internals/continuous_integration.html
.. _Ned Batchelder's: http://nedbatchelder.com/
.. _Getting Started Testing: http://nedbatchelder.com/text/test0.html
