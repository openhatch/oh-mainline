==================================
Continuous integration with Hudson
==================================


Overview
========

The OpenHatch code has a suite of tests. It's important that when we deploy the
code to the website, the tests all pass.

Hudson is a "continuous integration" tool (read `more on Wikipedia`_). It wakes
up once an hour, checks the git repository for new commits, and runs the test
suite.


.. _more on Wikipedia: https://secure.wikimedia.org/wikipedia/en/wiki/Continuous_integration


Specifics of the OpenHatch setup
================================

Hudson on the web: http://vm3.openhatch.org:8080/


Configuration
=============

There are three "projects" in Hudson. Different ones run different suites of
tests in the OpenHatch codebase. They include or exclude different Django apps
from the OpenHatch codebase.

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

* Go to http://linode2.openhatch.org:8080/
* Choose a project (for example, `Test the search app`_)
* Click on "Latest Test Result"


.. _Test the search app: http://linode2.openhatch.org:8080/job/Test%20the%20%22search%22%20app/


Permissions
===========

Right now, only Raffi and Asheesh can modify the configuration of Hudson.

Anyone can enqueue a run of the test suite by clicking a "Build" link within
Hudson. That's a good thing.


IRC
===

It hangs out on #openhatch as openhatch_hudson. Type !hudsonhelp to find out the
bot's commands.


Future work
===========

It would be nice if Hudson notified us on IRC when we "break the build"
(introduce changes that break tests). `Bug filed`_.

It would be super nice if, whenever there was a commit to Github master that
passed all the tests, Hudson automatically deployed it.


.. _Bug filed: https://openhatch.org/bugs/issue173
