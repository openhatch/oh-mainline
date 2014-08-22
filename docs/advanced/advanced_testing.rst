================
Advanced testing
================

Note: This was recently migrated from OpenHatch wiki. Documentation updates
      are under active development.


The '''purpose of this page''' is to show you how to write automated tests
within the OpenHatch codebase.

If you already know how software testing works, skip to
'''[[Automated testing#Details specific to OpenHatch|Details specific to OpenHatch]]'''.

Tests: An overview
==================

When you run:

 python manage.py test

and you'll see a bunch of dots. Dots mean success.

This runs the many tests that are part of the OpenHatch code.

In general, you really should write a test if you add new functionality. This
page explains how and when to write new tests and how to run the tests we
have.


What a basic test looks like
============================

Imagine this is in mysite/base/views.py:

 def multiply(x, y):
     return x * y

Then this would be in mysite/base/tests.py:

 import mysite.base.views

 class TestMultiplication(django.test.TestCase):
     def test_return_one(self):
         self.assertEqual(35,
                          mysite.base.views.multiply(7, 5))

When a test fails
=================

When a test fails you will see "FAILED" followed by the
test_name, along with the Traceback and the failure summary
at the end (e.g. FAILED (failures=2, errors=1, skipped=9))

To force a failure, maybe you are just curious to see what it will
look like, you can add: <code> self.assertTrue(False) </code>
to a test case that you are interested in running.

== Getting your local dev OpenHatch set up to run tests ==

To run tests correctly you'll need to have subversion installed -

 $ apt-get install subversion

Then run the full suite of tests --

 $ python manage.py test

Read the official Django testing guide
======================================

The official guide on Django testing is quite good. It says,
"The best part [about writing tests for Django code] is, it's really easy."

We use the Django "unit test" style of writing tests.

* Go '''[http://docs.djangoproject.com/en/dev/topics/testing/ read the official Django testing guide]'''.

General testing tips
====================

How to write code that is easy to test
--------------------------------------


If you are writing a function, make it '''accept arguments''' for its data, rather having it calculate the input itself. For example:

'''Good'''

 def multiply(x, y):
     return x * y

'''Less good'''

 def multiply(x):
     y = settings.MULTIPLICATION_FACTOR
     return x * y

It's okay to rely on things like system settings and database content, but in general if your functions are simpler, they are easier to test.

Details specific to OpenHatch
=============================

We regularly run Automated Testing
==================================

OpenHatch's Automated Testing is run by Jenkins, with the interface on the virtual machine donated by GPLHost @ http://vm3.openhatch.org:8080/

Where to write your tests
=========================

In general, add tests to the same Django ''app'' as you are editing. For example, if you made
changes to '''base/views.py''', then add a test in '''base/tests.py'''.

The test files are kind of ''sprawling''. It doesn't really matter where within the ''tests.py'' file
you add your test. I would suggest adding it to the end of the file.

The OpenHatch test case helper class
====================================

In '''mysite/base/tests.py''' there is a TwillTests class. It offers the following convenience methods:

* '''login_with_client'''
* '''login_with_twill'''

About fixtures
==============

If you inherit from TwillTests, you get some data in your database.
You can rely on it. (TODO: fix me with WebTest)

To run your tests
-----------------

What app did you write your test in? Let's pretend it was in '''base''':

 python manage.py test base

To run just a few specific tests
--------------------------------

 python manage.py test base.Feed base.Unsubscribe.test_unsubscribe_view

The structure here is '''app'''.'''class'''.'''method'''. So if you want to just run
your own new test, you can do it that way.

Mocking and patching
====================

This section is important, but we haven't written it yet. Oops.

Testing with Twill, versus the Django test client
=================================================
[Note: Twill is going away in the OpenHatch code base and is being replaced by
       WebTest (yay!).


To make a long story short:

The Django test client is good at introspecting how the function worked internally.

Twill tests are good because they let you say "Click on the link called '''log in'''".

We should write more about this. Maybe you, dear reader, can say some more.
