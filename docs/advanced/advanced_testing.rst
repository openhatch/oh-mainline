================
Advanced testing
================

.. note:: Twill is going away in the OpenHatch code base and is being
          replaced by WebTest (yay!).

The purpose of this page is to show you how to write automated tests
within the OpenHatch codebase.

If you already know how software testing works, skip to the section
`Details specific to OpenHatch`_.

Tests: An overview
##################

You can run the many tests that are part of the OpenHatch code::

    $ python manage.py test

During the test run, you'll see a bunch of dots. Dots mean success.

**Tip** You really should write a test if you add new functionality.
        This page explains how and when to write new tests and how to
        run the tests we have.

What a basic test looks like
****************************

Imagine this is in ``mysite/base/views.py``::

    def multiply(x, y):
        return x * y

Then this would be in ``mysite/base/tests.py``::

    import mysite.base.views

    class TestMultiplication(django.test.TestCase):
        def test_return_one(self):
            self.assertEqual(35, mysite.base.views.multiply(7, 5))

When a test fails
*****************

When a test fails you will see:

    * **FAILED** followed by the test_name
    * the Traceback
    * the failure summary (e.g. **FAILED (failures=2, errors=1, skipped=9)**)

To force a failure, maybe you are just curious to see what it will
look like, you can add to the test code::

    self.assertTrue(False)

This assertion will fail and so will the test containing this code.


General testing tips
####################

Read the official Django testing guide
**************************************

The `official guide on Django testing`_ is quite good. It says:

    *The best part [about writing tests for Django code] is, it's really
    easy.*

OpenHatch contributors use the Django "unit test" style of writing tests.

..  _`official guide on Django testing`: http://docs.djangoproject.com/en/dev/topics/testing/

How to write code that is easy to test
**************************************

If you are writing a function, have it "accept arguments" for its data,
rather than having it calculate the input itself. For example:

*Good*::

    def multiply(x, y):
        return x * y

*Less good*::

     def multiply(x):
        y = settings.MULTIPLICATION_FACTOR
        return x * y

It's okay to rely on things like system settings and database content, but
in general if your functions are simpler, they are easier to test.

Details specific to OpenHatch
#############################

We regularly run Automated Testing
**********************************

OpenHatch's Automated Testing is run by Jenkins, with the interface on the
virtual machine donated by GPLHost @ http://vm3.openhatch.org:8080/

Where to write your tests
*************************

In general, add tests to the same Django app as you are editing. For
example, if you made changes to `base/views.py`, then add a test in
`base/tests.py`.

The test files are kind of 'sprawling'. It doesn't really matter where
within the `tests.py` file you add your test. I would suggest adding it to
the end of the file.

The OpenHatch test case helper class
************************************
.. note:: Twill is going away in the OpenHatch code base and is being
          replaced by WebTest (yay!).

In `mysite/base/tests.py` there is a TwillTests class. It offers the
following convenience methods:

    * `login_with_client`
    * `login_with_twill`

The subversion missions test cases
**********************************
When running or testing the subversion mission locally, subversion (svn
and svnadmin) must be installed on the local system. If subversion is
not installed, the tests will not be run. 

Settings information related to subversion, such as path locations, can
be found in the `settings.py`.

About fixtures
##############
.. note:: Twill is going away in the OpenHatch code base and is being
          replaced by WebTest (yay!).

To run your tests
*****************

What Django app did you write your test in? Let's pretend it was in the
``base`` module. To run all the tests in ``base``::

    $ python manage.py test base

To run just a few specific tests
********************************

You can run just one test. For example, a test named *base.Feed*::

    $ python manage.py test base.Feed

Or you can run two (or more) tests::

    $ python manage.py test base.Feed base.Unsubscribe.test_unsubscribe_view

The structure here is *app.class.method*. If you want to just run your own
new test, you can do so.

Mocking and patching
####################
.. note::  This section is important, but we haven't written it yet. Please
          consider helping us write this section.
          See Documentation_

..  _Documentation: ..getting_started/documentation.html

Testing with Twill, versus the Django test client
#################################################
.. note:: Twill is going away in the OpenHatch code base and is being
          replaced by WebTest (yay!).

To make a long story short:

    - The Django test client is good at introspecting how the function worked
      internally.
    - Twill tests are good because they let you say "Click on the link
      called 'log in'".
