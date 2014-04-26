==============================================================
Checking Coding Style Errors in Pull Requests with lint-review
==============================================================

Overview
========

We use `lint-review`_, an automated code linting bot that checks pull requests for code style errors (such as pep8 violations). It uses the Github API to fetch the changes, runs linters against them and comments on the pull request if any code style errors are there in the changes.

.. _lint-review: https://github.com/markstory/lint-review

Configuration
=============

The ``.lintrc`` file stores the configurations for the lint-review bot. You can find the ``.lintrc`` file for this project `here`_.

.. _here: https://github.com/openhatch/oh-mainline/blob/master/.lintrc
