============
Installation
============

Overview
========

This repository contains (mostly) Python code written on top of Django
and other Python modules. We bundle a copy of all of the essential
dependencies so that you can get started immediately.

It should take you 15 minutes or fewer to get the OpenHatch site running.

Here are the steps you'll have to follow:

* Get the code. (You've probably already done this.)
* Open a command prompt
* Set up the database
* Run the site

Then you can run your own instance of the OpenHatch website and play
with the code from an interactive shell.

That's all you need to get the site going. If you want to work on core
backend features like the bug importer, or let your local site rescale
images, then you can also read the `advanced_installation.rst`_ file to
learn about optional dependencies and automated testing.

OpenHatch is currently designed to run on Python 2.6 or above.


.. _advanced_installation.rst: advanced_installation.html


Essentials
==========

Get the code
~~~~~~~~~~~~

If you already have an "oh-mainline" directory on your computer, then
you already have the code. If you're reading this file on the web,
then you need to run::

  git clone https://github.com/openhatch/oh-mainline.git

You probably have already done this, though, and can jump to the next
step.


Open up a command prompt
~~~~~~~~~~~~~~~~~~~~~~~~

For the rest of these instructions, you have to open a command prompt.

On a Linux or similar system, find a program with "terminal" or
"konsole" in the name. Run it.

On a Mac, click the search icon in the top-right of the screen and
search for Terminal. This should find the Terminal program, stored in
/Applications/Utilities. Run it.

On a Windows computer, click the Start icon, and find the Run
box. Enter "cmd" into it, and press enter.

Make sure you have changed directory into the oh-mainline directory
before you run the rest of the commands.


Set up the database
~~~~~~~~~~~~~~~~~~~

Your local OpenHatch site will store data in a SQLite database. This
must be done in two steps.

Step 1: Create the database file and add tables for our dependencies

Run this command::

  python manage.py syncdb --noinput

This will print some messages and eventually give you your prompt
back. If you would like to know if what you got was correct, check
in the bottom of the file in the section Output Samples.

(We have to pass "--noinput" to request that Django not ask you
questions. This is due to a bad interaction between Django's superuser
creation system and our custom profiles.)

Step 2: Run the "migrations" to create the OpenHatch tables

Run this command::

  python manage.py migrate

This will print out *lots* of text, at the end of which, your tables
should be ready. You're ready to run the site.

(Note that this creates an empty database, with zero users and zero
projects, ready for you to fill with data as you use your local
version of the site. If you want your site to have a database filled
with data like what is on the main OpenHatch.org site, you can import
a data snapshot. See `maintenance.rst`_ for more info about that.)


.. _maintenance.rst: maintenance.html


Run the site
~~~~~~~~~~~~

Run this command::

  python manage.py runserver

As long as the "runserver" is running, you can visit your version of
the site in a web browser. So, try surfing to:

http://localhost:8000/


You're done
~~~~~~~~~~~

Hooray! That's it for the essentials. You have everything you need to
get the site going, and to start making changes.

Now is a good time to find us on IRC or the email list and say hello!
We can help you make the changes you want to. See `README.rst`_ for how
to find us!

If you want to read about some optional dependencies, open up
`advanced_installation.rst`_. You can also read about how to maintain
your local site in `maintenance.rst`_.


.. _README.rst: README.html


Output Samples
==============

Here is a sample from the output from python manage.py syncdb --noinput ::

  2012-01-17 12:16:57,136 <module>:46 INFO     Some parts of the OpenHatch site may fail
  because the lxml library is not installed. Look in `advanced_installation.rst`_ for
  information about lxml.
  Syncing...
  Creating tables ...
  Creating table ghettoq_queue
  Creating table ghettoq_message
  Creating table auth_permission
  ......
  Creating table djkombu_message
  Installing custom SQL ...
  Installing indexes ...
  No fixtures found.
  ......
  Synced:
   > ghettoq
   > django.contrib.auth
   > django.contrib.contenttypes
  .....
  Not synced (use migrations):
   - mysite.search
   - mysite.profile
   - mysite.customs
  .....
  (use ./manage.py migrate to migrate these)
