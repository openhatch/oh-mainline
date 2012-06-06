===================
Deploying to Heroku
===================

Overview
========

Heroku is a service that provides web application hosting. They have a
free-of-cost tier. If you want to create a web URL for the changes you've
made to your version of the OpenHatch site, deploying that code to Heroku
is an easy, no-cost way to do that.

Note that, at the moment, the OpenHatch database migrations do not run
properly on Heroku. Therefore, a deployment to Heroku is best-suited for
temporary deployments where you don't mind erasing the database later.

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
app. (In the example here, I've named my app
"better-frobulator". Substitute your own app name!) So, type something
like this::

  heroku apps:create better-frobulator --stack=cedar

You'll see output like this::

  Creating better-frobulator... done, stack is cedar
  http://better-frobulator.herokuapp.com/ | git@heroku.com:better-frobulator.git


Make sure your OpenHatch git repository is configured to use that Heroku app
============================================================================

In order to use "git push" to deploy your app to Heroku, you must configure
Heroku as a "git remote". Notice the git path provided by Heroku in the
above output. Use git remote to add it, for example as follows::

  git remote add heroku git@heroku.com:better-frobulator.git

Once you have done that, you can deploy via "git push".


Using git push to deploy to Heroku
==================================

Now that you have a remote Git repository hosted at Heroku, you
can simply::

  git push heroku HEAD:master

This will push whatever branch you are currently on. The output will
look something like::

  Counting objects: 64469, done.
  Delta compression using up to 4 threads.
  Compressing objects: 100% (22037/22037), done.
  Writing objects: 100% (64469/64469), 67.19 MiB | 2 KiB/s, done.
  Total 64469 (delta 40985), reused 61688 (delta 39048)
  -----> Heroku receiving push

After that, a lot of information from Heroku will scroll by.

Because of the large size of the OpenHatch git repository, the first
git push may take a few minutes.

As you make local changes, you can just use the same "git push"
command to update the code on Heroku. Note that if you end up
rewriting history, you may need to add a plus sign to the above
command, e.g.::

  git push heroku +HEAD:master


Set up the database
===================

Now that your version of the OpenHatch code is on Heroku, you'll have to
create a database for it to use.

To do that, run this command::

  heroku addons:add --app better-frobulator shared-database

(Replace "better-frobulator" with the name of your Heroku app.) This will
add a free-of-cost Postgres database to your app.

Now, populate the database with data::

  heroku run --app better-frobulator python manage.py syncdb --noinput


Visit your app on the web
=========================

Now you can go to the Heroku URL for your app. If you're not sure what
that URL is, you can type (remembering to replace "better-frobulator"
with your app's name)::

  heroku apps:info --app better-frobulator

Look for the "Web URL" at the bottom of the output, and visit that in
your web browser.
