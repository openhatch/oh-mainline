======================
Continuous Integration
======================


Overview
========

The OpenHatch code has a suite of tests. It's important that when we deploy
the code changes to the website that all tests are passing.

`Continuous integration`_ helps our developers see if their code changes are
passing all tests or are failing a test and additional code changes are
needed.

.. _Continuous integration: http://www.aosabook.org/en/integration.html


Travis CI
=========

`Travis CI`_ is a hosted, distributed "continuous integration" system (read
`more on Wikipedia about Travis CI`_). The GitHub page for the `oh-mainline`
indicates whether our tests currently are passing.

.. _more on Wikipedia about Travis CI: https://en.wikipedia.org/wiki/Travis_CI
.. _Travis CI: https://travis-ci.org

Using Travis CI
---------------
There are multiple ways that Travis CI communicates the source code's current
build status and whether tests are passing:

* The first is the "build" badge on the `oh-mainline` GitHub page displayed
  at the top of the README. Clicking on the "build" badge will display
  Travis CI's status page for OpenHatch.

* OpenHatch's Travis CI status page can be directly found at
  `<https://travis-ci.org/openhatch/oh-mainline>`_.

* GitHub also provides information on every pull request about Travis CI's
  testing and status related to the individual pull request. This is very
  helpful for developers and reviewers.


  .. note:: Currently, Travis CI is showing that our tests are not passing
            when tested with a MySQL database. Details can be found in the
            OpenHatch issue tracker. We hope to have this issue resolved soon.


Configuration for Travis CI
---------------------------

The `.travis.yml` file in the `oh-mainline` directory contains configuration
information used by Travis CI.


Jenkins
=======

Jenkins is a "continuous integration" tool (read `more on Wikipedia`_). It
wakes up once an hour, checks the git repository for new commits, and runs the
test suite. For additional information about Jenkins, read `more on Jenkins`_.

.. _more on Wikipedia: https://en.wikipedia.org/wiki/Continuous_integration
.. _more on Jenkins: https://jenkins-ci.org


Status information about continuous integration projects can be found on 
OpenHatch's Jenkins dashboard : http://vm3.openhatch.org


Jenkins configuration
---------------------
There are a number of "projects" in Jenkins. Different ones run different
suites of tests in the OpenHatch codebase. They include or exclude different
Django apps from the OpenHatch codebase.

For example,

* Test the "installation" instructions

  - This tests the OpenHatch developer instructions for building OpenHatch.

* Test the "customs" app

  - The tests for the customs app often go out to the network and can
    break if the remote servers change their APIs.

* Test the "search" app

  - The volunteer opportunity finder ("search") tests can take a while to
    run, so we separate them out.

* Test all apps except customs and search

  - This is the catchall that tests the rest of the code.

Status information about continuous integration projects can be found on
OpenHatch's Jenkins dashboard.

Jenkins administration
----------------------

Right now, only Raffi and Asheesh can modify the configuration of Jenkins.

Anyone can enqueue a run of the test suite by clicking a "Build" link within
a Jenkins project. That's a good thing.


Future work
===========

It would be super nice if, whenever there was a commit to GitHub master that
passed all the tests, it would be automatically deployed.


.. _Bug filed: https://openhatch.org/bugs/issue173
