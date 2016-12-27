===================
Deploying to Heroku
===================

Overview
========

Heroku is a service that provides web application hosting. They have a
free-of-cost tier. If you want to create a web URL for the changes you've
made to your version of the OpenHatch site, deploying that code to Heroku
is an easy, no-cost way to do that.

The steps are all listed below. Keep reading to start following
them. Note that many of the instructions require typing commands into
a command prompt.


Install the Heroku toolbelt and log in
======================================

To use the Heroku service, you'll need to create an account on their
website and install software that makes it easy to interact with their
service.

Read `their instructions`_ to do that. Be sure to configure your SSH
key with the service. (If you need help with that, read their docs or
find OpenHatch people on IRC.) Finally, make sure you have run the
"heroku login" command.

If you don't see instructions for your operating system, look in this page's
`Troubleshooting`_ section.

.. _their instructions: https://devcenter.heroku.com/articles/quickstart


Create a Heroku app
===================

On the Heroku service, individual sites are called "apps". You'll need
to create an app corresponding to the code you want to deploy
there. At the time of writing, you are permitted to create an unlimited
number of apps for free. Therefore, I personally recommend creating an
app whose name is similar to the branch name on your computer.

This app name appears in public as part of the domain name, so choose
something you don't mind other people reading! (If you leave out the app
name, Heroku will pick a random cute name for your app.)

On your computer, within a terminal, change directory into your clone
of oh-mainline. You'll use the "heroku" command to create your
app. (In the example here, I've named my app "openhatch". 
Substitute your own app name!) So, type something like this::

  $ heroku create openhatch

You should see this output::

  Creating openhatch... done, stack is cedar
  http://openhatch.herokuapp.com/ | git@heroku.com:openhatch.git
  Git remote heroku added

Now push your local git repo to Heroku with this command::

  $ git push heroku master

You should see this output::

  Initializing repository, done.
  Counting objects: 70870, done.
  Delta compression using up to 8 threads.
  Compressing objects: 100% (23526/23526), done.
  Writing objects: 100% (70870/70870), 78.90 MiB | 103 KiB/s, done.
  Total 70870 (delta 43536), reused 70870 (delta 43536)

  -----> Removing .DS_Store files
  -----> Python app detected
  -----> No runtime.txt provided; assuming python-2.7.4.
  -----> Preparing Python runtime (python-2.7.4)
  -----> Installing Distribute (0.6.36)
  -----> Installing Pip (1.3.1)
  -----> Installing dependencies using Pip (1.3.1)
         Downloading/unpacking psycopg2 (from -r requirements.txt (line 2))

  ...

         Successfully installed psycopg2 PIL
         Cleaning up...

  -----> Discovering process types
         Procfile declares types -> web

  -----> Compressing... done, 70.5MB
  -----> Launching... done, v5
         http://openhatch.herokuapp.com deployed to Heroku

  To git@heroku.com:openhatch.git
   * [new branch]      master -> master


Because of the large size of the OpenHatch git repository, the first
git push may take a few minutes.

As you make local changes, you can just use the same "git push"
command to update the code on Heroku. Note that if you end up
rewriting history, you may need to add a plus sign to the above
command, e.g.::

  $ git push heroku +HEAD:master


Set up the database
===================

Now that your version of the OpenHatch code is on Heroku, you'll have to
initialize the database that Heroku automatically created for you.

Now, initialize the database with::

  $ heroku run python manage.py syncdb --noinput

More information from Heroku will scroll by. You may notice ::

  ( INFO     Some parts of the OpenHatch site may fail because the lxml
    library is not installed. Look in ADVANCED_INSTALLATION.mkd for
    information about lxml )

At this point, this is not an issue.

You'll also need to run the migrate command::

  $ heroku run python manage.py migrate

Visit your app on the web
=========================

Now you can go to the Heroku URL for your app. If you're not sure what
that URL is, you can type::

  $ heroku apps:info

Look for the "Web URL" at the bottom of the output, and visit that in
your web browser.

Now, celebrate! Your OpenHatch instance is on the web. Go get yourself
a strawberry smoothie (making substitutions as necessary for your
dietary restrictions).


Troubleshooting
===============

* If Heroku doesn't have instructions for your operating system, and you
  have a package manager, try installing *git* and *rubygems* from your
  package manager. For example, on Fedora and other systems that use yum,
  you could type::

    $ sudo yum install git rubygems

  Then run::

    $ sudo gem install heroku


* You can verify the status of your application with::

   $ heroku ps
   === web (1X): `./mysite/manage.py runserver 0.0.0.0:$PORT`
   web.1: up 2014/01/04 13:48:55 (~ 17m ago)


* From time to time things might not work as expected. In those times, Heroku
  provides with a nice log facility::

    $ heroku logs

  More documentation on how to use Heroku's `log facility`_ and `processes`_ is
  available to you.

.. _log facility: https://devcenter.heroku.com/articles/logging
.. _processes: https://devcenter.heroku.com/articles/procfile

