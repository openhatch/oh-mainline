==============
Testing Basics
==============

OpenHatch strives to follow best practices for testing. One
common practice in the Python community is Test Driven Development (TDD).
In TDD, a developer will write a test for a new feature before creating
the feature's source code.


Running the OpenHatch test suite
################################

You may run the test suite to see if all tests pass before you begin
making changes to the code. To run the test suite,::

    python manage.py test

The test suite begin running all of the tests and will display the test
progress in the console window.


Running a subset of tests
#########################

If you are working on a particular area of the source code, you may find
it helpful to run a subset of the tests. You may pass an argument after
the ``python manage.py test`` command.

Currently, you may pass one or more of the following arguments: `account`,
`base`, `missions`, `project`, `search`, and `customs`. For example,::

    python manage.py test missions

will run all the tests related to the OpenHatch missions.


Additional testing information
##############################

The Internals section of this documentation contains more detailed information
about the test suite, testing, and `continuous integration`_.

.. _continuous integration: ../internals/continuous_integration.html
