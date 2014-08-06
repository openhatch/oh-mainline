============ 
Installation 
============

*These installation instructions are tested nightly on 
Ubuntu 12.04 and Debian stable.  Last verified on Windows XP 11/7/2013 and on 
Mac OS X 10.9.2 May 11, 2014.*

OpenHatch is currently designed to run on Python 2.x versions Python 2.6 or above.  OpenHatch will not work on Python 3 or above.

Overview
========

This repository contains (primarily) Python code written on top of Django
and other Python modules. We bundle a copy of all of the essential
dependencies for oh-mainline to run so that you can get started immediately 
(there is no need to download and configure additional software from other sources).

It should take you about 15 minutes to get the OpenHatch site running locally on
your computer.

Here are the basic steps you'll follow for installation:

* Open a command prompt 
* Get the code from the GitHub repository
* Set up the database
* Run the site

After running your own instance of the OpenHatch website, you can play
with the code from an interactive shell on your computer.

Note: If you want to work on core backend features, like the bug importer,
or let your local site rescale images, please read the `advanced_installation.rst`_ file
to learn about optional dependencies and automated testing.

.. _advanced_installation.rst: ../advanced/advanced_installation.html


Essentials
==========

Open up a command prompt 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

Note: Understanding how to open a command prompt for your operating 
system is an important prerequisite to master before continuing with the remaining installation instructions.

For the rest of these instructions, you have to open a command prompt:

* On a Linux or similar system, find a program with "terminal" or
  "konsole" in the name. Run it.

* On a Mac, click the search icon in the top-right of the screen and
  search for Terminal. This should find the Terminal program, stored in
  /Applications/Utilities. Run it.

* On a Windows computer, you'll need to use Git Bash.  To do so, download and install the .exe at `this link <http://openhatch.org/missions/windows-setup/>`_.  (It will ask you a bunch of questions.  You can accept the defaults.)  Once that is installed, launch Git Bash by going to: Start -> All Programs -> Git -> Git Bash


Get the code from the GitHub repository 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you already have an "oh-mainline" directory on your computer, then
you already have the code. You may skip to the next step.

If you're reading this installation instruction file on the web,
then you will need to clone the repository from GitHub to your local 
computer.

Step 1: Open a command prompt on your computer

Step 2: Create a new directory on your computer::

  mkdir localhatch
  
Step 3: Change to the new directory::

  cd localhatch
  
Step 4: Clone the repository from GitHub to your local computer::

  git clone https://github.com/openhatch/oh-mainline.git

If your commands are executed successfully, you may continue to the next
step.

**Note:** For most Django projects, you would need to install the dependencies 
at this point (using `pip install -r requirements.txt`), but for the OpenHatch 
project, these packages have been bundled for your convenience in the `vendor` 
directory, so they don't need to be installed separately.

Set up the database
~~~~~~~~~~~~~~~~~~~

Important note: Before you run the commands in the this section, make sure you have
changed your present working directory to the oh-mainline directory.

Your local OpenHatch site will store data in a SQLite database. 

Step 1: Create the database file and add tables for our dependencies

Run this command::

  python manage.py syncdb --migrate --noinput

(We have to pass "--noinput" to request that Django not ask you
questions. This is due to a bad interaction between Django's superuser
creation system and our custom profiles.)

(--migrate creates an empty database, with zero users and zero
projects, ready for you to fill with data as you use your local
version of the site. If you want your site to have a database filled
with data like what is on the main OpenHatch.org site, you can import
a data snapshot. See `maintenance.rst`_ for more info about that.)

This will print out *lots* of text. Once all of the text is printed, you should see something like the output listed in `Output Samples`_ below. Afterwards, your tables should be ready. You're ready to run the site.

.. _maintenance.rst: ../advanced/maintenance.html


If you are using Windows and do not have Python installed, you may get the 
error "Python: command not found."  You can follow `these instructions 
<https://openhatch.org/wiki/Boston_Python_Workshop_8/Friday/Windows_set_up_Python>`_ 
to install Python.


Run the site
~~~~~~~~~~~~
Important note: Before you run the commands in the this section, make sure you have
changed your present working directory to the oh-mainline directory.

Run this command which will start a web server locally on your computer::

  python manage.py runserver

As long as the "runserver" is running, you can visit your local version of
the OpenHatch site in a web browser. So, try surfing to:

http://localhost:8000/


You're done
~~~~~~~~~~~

Hooray! That's it for the essentials. You have everything you need to
get the site going, and to start making changes.

Now is a good time to find us on IRC or the email list and say hello!
We can help you make the changes you want to. :doc:`../community/contact`!

If you want to read about some optional dependencies, open up
`advanced_installation.rst`_. You can also read about how to maintain
your local site in `maintenance.rst`_.


Output Samples
==============

Here is a sample output from python manage.py syncdb --migrate --noinput ::

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
   - djcelery
