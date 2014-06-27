=================================================
Continuous Integration with Jenkins and Travis CI
=================================================


Overview
========

The OpenHatch code has a suite of tests. It's important that when we deploy the
code to the website, all tests pass.

Jenkins is a "continuous integration" tool (read `more on Wikipedia`_). It wakes
up once an hour, checks the git repository for new commits, and runs the test
suite. For additional information about Jenkins, read `more on Jenkins`_.

.. _more on Wikipedia: https://en.wikipedia.org/wiki/Continuous_integration
.. _more on Jenkins: https://jenkins-ci.org

Travis CI is a hosted, distributed "continuous integration" system (read 
`more on Wikipedia about Travis CI`_). For additional information about 
Travis CI, read `more on Travis CI`_.

.. _more on Wikipedia about Travis CI: https://en.wikipedia.org/wiki/Travis_CI
.. _more on Travis CI: https://travis-ci.org


Jenkins Dashboard for OpenHatch
===============================

Status information about continuous integration projects can be found on 
OpenHatch's Jenkins dashboard : http://vm3.openhatch.org


Configuration
=============

There are a number of "projects" in Jenkins. Different ones run different suites of
tests in the OpenHatch codebase. They include or exclude different Django apps
from the OpenHatch codebase.

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


How to see the list of tests that failed or passed
==================================================

* Go to http://vm3.openhatch.org
* Choose a project (for example, `Test the search app`_)
* Click on "Latest Test Result"


.. _Test the search app: http://vm3.openhatch.org/job/Test%20the%20%22search%22%20app/


Permissions
===========

Right now, only Raffi and Asheesh can modify the configuration of Jenkins.

Anyone can enqueue a run of the test suite by clicking a "Build" link within
a Jenkins project. That's a good thing.


IRC
===

It hangs out on #openhatch as openhatch_hudson. Type !hudsonhelp to find out the
bot's commands.


Configuration for Travis CI
===========================

The `.travis.yml` file in the `oh-mainline` directory contains configuration
information used by Travis CI.


Future work
===========

It would be super nice if, whenever there was a commit to Github master that
passed all the tests, Jenkins automatically deployed it.


.. _Bug filed: https://openhatch.org/bugs/issue173
