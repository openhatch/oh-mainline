============ 
Installation 
============

OpenHatch is currently designed to run on Python versions 2.6.0 to 2.7.8.
OpenHatch site does not currently support Python 3 or above. We hope to do
so in the future.

.. note:: These installation instructions are tested nightly on Ubuntu 12.04
          and Debian stable. Last verified on Windows XP 11/7/2013,
          Mac OS X 10.9.5 October 29, 2014, and Mac OS X 10.10 December 15, 2014.

Overview
========

This repository contains (primarily) Python code written on top of Django
and other Python modules. We bundle a copy of all of the essential
dependencies for oh-mainline to run so that you can get started immediately 
(there is no need to download and configure additional software from other
sources).

It should take you about 15 minutes to get the OpenHatch site running locally 
on your computer.

Here are the basic steps you'll follow for installation:

* :ref:`Open a command prompt <open-command-prompt>`
* :ref:`Get the code from the GitHub repository <get-code-github>`
* :ref:`Set up the database <set-up-database>`
* :ref:`Run the site <run-site>`

After running your own instance of the OpenHatch website, you can play
with the code from an interactive shell on your computer.

If you want to work on core backend features, like the bug importer,
or let your local site rescale images, please see `Advanced Installation`_
documentation to learn about optional dependencies and automated testing.

.. _Advanced Installation: ../advanced/advanced_installation.html


Essentials
==========


.. _open-command-prompt:

Open up a command prompt 
~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: Understanding how to open a command prompt for your operating 
          system is an important prerequisite to master before continuing
          with the remaining installation instructions.

For the rest of these instructions, you have to open a command prompt:

* On a *Linux* or similar system, find a program with "terminal" or
  "konsole" in the name. Run it.

* On a *Mac*, click the search icon in the top-right of the screen and
  search for Terminal. This should find the Terminal program, stored in
  /Applications/Utilities. Run it.

* On a *Windows* computer, you'll need to use Git Bash. To do so, download and
  install the .exe at `this link <http://openhatch.org/missions/windows-setup/>`_.  
  (It will ask you a bunch of questions.  You can accept the defaults.)
  Once that is installed, launch Git Bash by going to: 
  `Start -> All Programs -> Git -> Git Bash`


.. _get-code-github:

Get the code from the GitHub repository 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you already have an `oh-mainline` directory on your computer, then
you already have the source code. You may skip to the next step,
:ref:`Set up the database <set-up-database>`.

If you're reading this installation instruction file on the web,
then you will need to clone the repository from GitHub to your local 
computer.

Step 1: Open a command prompt on your computer

Step 2: Create a new directory on your computer::

  mkdir localhatch
  
Step 3: Change to the new directory::

  cd localhatch
  
Step 4: On your personal Github account, fork the OpenHatch repository at
https://github.com/openhatch by clicking on the "Fork" button on the right-hand side.
Github now takes you to your forked repository of the OpenHatch upstream repository.

Step 5: On the command prompt, clone the repository from your fork of the GitHub OpenHatch code to your local computer::

  git clone https://github.com/<YOUR_GITHUB_USERNAME>/oh-mainline.git

If your commands are executed successfully, you may continue to the next
step.

.. note:: For most Django projects, you would need to install the dependencies 
          at this point (using `pip install -r requirements.txt`), but for
          the OpenHatch project, these packages have been bundled for your
          convenience in the `vendor` directory, so they don't need to be
          installed separately.


.. _set-up-database:

Set up the database
~~~~~~~~~~~~~~~~~~~

Before you run the commands in the this section, make sure you have
changed your **present working directory** to the `oh-mainline` directory.::

  cd oh-mainline

Your local OpenHatch site will store data in a SQLite database. 

Run this command to create the database and add tables for our dependencies::

  python manage.py syncdb --migrate --noinput


(We have to pass "--noinput" to request that Django not ask you
questions. This is due to a bad interaction between Django's superuser
creation system and our custom profiles.)

(--migrate creates an empty database, with zero users and zero
projects, ready for you to fill with data as you use your local
version of the site. If you want your site to have a database filled
with data like what is on the main OpenHatch.org site, you can import
a data snapshot. See `Importing data snapshots`_ for more info about
that.)

This will print out *lots* of text. Once all of the text is printed, you
should see something like the output listed in `Output Samples`_ below.
Afterwards, your database tables should be ready. You're ready to run the
site.

.. _maintenance.rst: ../advanced/maintenance.html


If you are using Windows and do not have Python installed, you may get the 
error "Python: command not found."  Follow `these instructions
<https://openhatch.org/wiki/Boston_Python_Workshop_8/Friday/Windows_set_up_Python>`_ 
to install Python.


.. _run-site:

Run the site
~~~~~~~~~~~~
Before you run the commands in the this section, make sure you have
changed your **present working directory** to the `oh-mainline` directory.

Run this command which will start a web server locally on your computer::

  python manage.py runserver

As long as the "runserver" is running, you can visit your local version of
the OpenHatch site in a web browser. So, try surfing to:

http://localhost:8000/

.. note:: Your local version of OpenHatch does not contain any user data in
   its SQLite database. You may add users manually through the user
   interface. If your development needs require a large amount of
   prepopulated data, you can find information about `Importing data
   snapshots`_ in the Advanced Installation documentation.

.. _`Importing data snapshots`: ../advanced/maintenance.html#importing-data-snapshots


You're done
~~~~~~~~~~~

Hooray! That's it for the essentials. You have everything you need to
get the site going, and to start making changes.

Now is a good time to find us on IRC or the email list and say hello!
We can help you make the changes you want to. :doc:`../community/contact`!

If you want to read about some optional dependencies, open up
`Advanced Installation`_ documentation. You can also read about how to
maintain your local site in the `Maintenance`_ documentation.

.. _`Maintenance`: ../advanced/maintenance.html


Output Samples
==============

Here is a sample output from ``python manage.py syncdb --migrate --noinput``::

 Synced:
   > ghettoq
   > django.contrib.auth
   > django.contrib.contenttypes
   > django.contrib.sessions
   > django.contrib.sites
   > django.contrib.webdesign
   > django.contrib.admin
   > registration
   > django_authopenid
   > django_extensions
   > south
   > django_assets
   > invitation
   > voting
   > reversion
   > debug_toolbar
   > sessionprofile
   > model_utils
   > djkombu
 Migrated:
   - mysite.search
   - mysite.profile
   - mysite.customs
   - mysite.account
   - mysite.base
   - mysite.project
   - mysite.missions
