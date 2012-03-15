=====================
How we handle patches
=====================

This is a page about improving or modifying OpenHatch. We call that
"Hacking OpenHatch," and there is a whole `category of pages about that`_.


.. _category of pages about that: index.html


As a patch submitter
====================

Before creating a patch series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    1. Add unit tests with your functionality changes or additions.
    2. Use docstrings and comments where appropriate. Spell-check your
       additions. Try to apply `pep8`_ standards.
    3. Test your changes on a local instance of the website. Prove to yourself
       that your changes address the issue they are supposed to address.
    4. Run the test suite, and make sure your unit tests pass and all tests that
       passed before your changes still pass.
    5. Use a tool like `PyChecker`_ to check for bugs. 


.. _pep8: http://pypi.python.org/pypi/pep8
.. _PyChecker: http://pypi.python.org/pypi/PyChecker/0.8.12


While creating a patch series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    1. Before creating the patch, update the master branch of your local
       repository checkout, and make sure your commits apply cleanly on top of
       master. In git, you can achieve this by `developing on a branch`_ and
       rebasing your branch commits on top of master with `git rebase master`_.
       You can also use git rebase -i master for an interactive rebase, in
       which you can reorder and edit commits. We prefer rebasing to merging
       because rebasing preserves a linear commit history, which can be easier
       to keep track of and reason about.
    2. Generate the patch set for your changes. Our preferred patch submission
       form is a patch series generated with "git format-patch". Read about
       `How to generate patches with git format-patch`_. Add on a line of its own,
       at the bottom of the commit, what the patch fixes. For example:
       "Closes: http://openhatch.org/bugs/issue398"


.. _developing on a branch: http://www.kernel.org/pub/software/scm/git/docs/gittutorial.html#_managing_branches
.. _git rebase master: http://www.kernel.org/pub/software/scm/git/docs/git-rebase.html
.. _How to generate patches with git format-patch: https://openhatch.org/wiki/How_to_generate_patches_with_git_format-patch


Permit us to share your work
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    1. Join our Devel email list by entering your email address into the form at
       http://lists.openhatch.org/mailman/listinfo/devel
    2. Send an email to devel@lists.openhatch.org with a message like:
        
        The work I contribute to OpenHatch is work I have permission to share.
        I permit anyone to re-use it under the terms of the Affero GPL,
        version 3 or later. 


Submitting your patch series for review
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    1. Attach your patches to the issue ticket at https://openhatch.org/bugs.
    2. Change the issue status to "in-review".
    3. Join IRC and say that you have an issue ready for review. 

If the reviewer says it's ready to go, your patch set will get deployed in short
order. If the reviewer has feedback he/she wants addressed, make the necessary
revisions and start back at the "Before creating a patch series" section.


As a patch reviewer
===================

Apply the patch to your local repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    1. Find the URL of the patch, e.g. http://git.jackgrigg.com/openhatch/patch/?id=5645afd46de0f0b7ba3a3c7035ff0711b5db9202
    2. Import the patch into your local repository. For example::

        wget -O- http://git.jackgrigg.com/openhatch/patch/?id=5645afd46de0f0b7ba3a3c7035ff0711b5db9202 | git am --3way

       It's important that you pass the --3way argument to "git am". 


Review the patch for correctness and cleanliness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Things to think about:

    1. Does the patch make sense? Does it look readable?::

        git log -p 

    2. If the author hasn't already done this: tell the author
       "Please email devel@lists.openhatch.org saying that you're okay with
       your work being under the Affero GPL, version 3. If you're willing, it
       is preferable that you say 'the Affero GPL, version 3 or later, at your
       option'."
    3. If you have revisions you'd like to see made, change the issue status to
       "in-progress", re-assign the issue to the patch submitter if it isn't
       already, and leave your review feedback on the ticket. 


Push and deploy
~~~~~~~~~~~~~~~

You might need to rope someone else in for this. Anyone in the `Login team`_ 
can do a push as well as deploy access. Asheesh Laroia (paulproteus) is the
traditional person to do this, but it's good to ask someone else so they get
practice!

Things to know:

    * If you push to origin/master, Hudson will test it.
    * Once you're happy, you can run the deploy script, but note that will push
      the current HEAD to origin/master. ::

        cd mysite
        ./scripts/deploy


    * When you deploy, check a page or two to make sure things are okay. 

For more details on how we use Hudson and how to force a Hudson build, see
`Continuous integration with Hudson`_. 

.. _Login team: https://openhatch.org/wiki/Login_team
.. _Continuous integration with Hudson: continuous_integration.html
