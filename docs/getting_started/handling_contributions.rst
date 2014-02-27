===========================
How we handle contributions
===========================

We use git/Github to handle contributions.  If you're new to git, you may
appreciate `this guide <https://openhatch.org/wiki/Git_Basics#Create_pull_request>`_.

As a pull request submitter
===========================

Creating a pull request
~~~~~~~~~~~~~~~~~~~~~~~

Get the latest version of master
################################

Before creating a pull request, update the master branch of your local
repository with the latest version of the OpenHatch-owned repository. In
git, you can achieve this by `developing on a branch`_ and rebasing your
branch commits on top of master with `git rebase master`_. You can also use
git rebase -i master for an interactive rebase, in which you can reorder
and edit commits. We prefer rebasing to merging because rebasing preserves
a linear commit history, which can be easier to keep track of and reason
about.

Test your changes
#################

    1. Add unit tests with your functionality changes or additions.
    2. Use docstrings and comments where appropriate. Spell-check your
       additions. Try to apply `pep8`_ standards.
    3. Test your changes on a local instance of the website. Prove to yourself
       that your changes address the issue they are supposed to address.
    4. Run the `test suite <internals/continuous_integration.html>`_, and make sure your unit tests pass and all tests that
       passed before your changes still pass.
    5. Use a tool like `PyChecker`_ to check for bugs.


.. _pep8: http://pypi.python.org/pypi/pep8
.. _PyChecker: http://pypi.python.org/pypi/PyChecker/0.8.12


Generate a pull request
#######################

Generate a pull request by pushing your changes to your personal remote.
You can then create a pull request to the OpenHatch repository. In the commit
message, include the issue the pull request addresses. For example: "Closes:
http://openhatch.org/bugs/issue398"

.. _developing on a branch: http://www.kernel.org/pub/software/scm/git/docs/gittutorial.html#_managing_branches
.. _git rebase master: http://www.kernel.org/pub/software/scm/git/docs/git-rebase.html
.. _How to generate patches with git format-patch: https://openhatch.org/wiki/How_to_generate_patches_with_git_format-patch


Submitting a pull request
~~~~~~~~~~~~~~~~~~~~~~~~~

    1. Add a link to the pull request in the issue ticket at https://openhatch.org/bugs.
    2. Change the issue status to "need-review".
    3. Join IRC and say that you have an issue ready for review.

If the reviewer says it's ready to go, your request will get merged in short
order. If the reviewer has feedback he/she wants addressed, make the necessary
revisions and start back at the "Check/test your changes" section.

Permit us to share your work
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    1. Join our Devel email list by entering your email address into the form at
       http://lists.openhatch.org/mailman/listinfo/devel
    2. Send an email to devel@lists.openhatch.org with a message like:

        The work I contribute to OpenHatch is work I have permission to share.
        I permit anyone to re-use it under the terms of the Affero GPL,
        version 3 or later. Additionally, contributions in the docs/ directory
        can be shared under the terms of CC Zero 1.0.


As a contribution reviewer
==========================

Apply the pull request to your local repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find the URL of the pull request by going to the main pull request page on
Github and clicking on the link named 'command line'.  Github will give you
instructions, including the URL of the pull request.  Follow all of the
instructions except the last one, which tells you to push back to the origin.

Review the pull request for correctness and cleanliness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Things to think about:

    1. Does the pull request make sense? Does it look readable?::

        git log -p

    2. If the author hasn't already done this: tell the author
       "Please email devel@lists.openhatch.org saying that you're okay with
       your work being under the Affero GPL, version 3. If you're willing, it
       is preferable that you say 'the Affero GPL, version 3 or later, at your
       option'."

    3. If you have revisions you'd like to see made, change the issue status to
       "in-progress", re-assign the issue to the pull request submitter if
       it isn't already, and leave your review feedback on the pull request.


Push and deploy
~~~~~~~~~~~~~~~

If you want to deploy the changes, and you have push access to the repository, you 
can do so by following the steps listed in the section labeled `Deployment <http://openhatch.readthedocs.org/en/latest/advanced/deployment.html>`_.

If you don't have push access, you will need to rope someone else in for this. Anyone 
in the `Login team <http://openhatch.readthedocs.org/en/latest/community/login_team.html>`_ 
can do a push as well as deploy access. Asheesh Laroia (paulproteus) is the traditional 
person to do this, but it's good to ask someone else so they get practice!

Things to know:

    * If you push to origin/master, Jenkins will test it.
    * Once you're happy, you can run the deploy script, but note that will push
      the current HEAD to origin/master. ::

        cd mysite
        ./scripts/deploy


    * When you deploy, check a page or two to make sure things are okay.

For more details on how we use Jenkins and how to force a Jenkins build, see
`Continuous integration with Jenkins and Travis CI`_.

.. _Login team: https://openhatch.org/wiki/Login_team
.. _Continuous integration with Jenkins and Travis CI: ../internals/continuous_integration.html
