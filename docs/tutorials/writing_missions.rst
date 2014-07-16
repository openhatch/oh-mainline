===========================
 Writing Training Missions
===========================

Training Missions are tools which help people learn the skills needed
to contribute to open source projects without burning their fingers.
They can be background information (`Windows Setup`_), or more
involved (`Subversion Training`_, which creates repositories for each
user to work on).

Missions are made up of some Python code ("views"), and some HTML
("templates"). OpenHatch uses some conventions to make developing new
training missions as simple as possible.

.. note::

   This document currently covers Simple (non-interactive) Training
   Missions. We are working to update it to describe interactive
   missions, as well.

Simple Training Missions
========================

Simple Training Missions provide users with step by step
documentation. As an example we'll start a new mission to document how
to make missions (how meta!), cunningly named "Make a Mission".

To begin developing a new mission, we need to create two directories:
one for the mission code, and one for the mission templates. Both are
stored in sub-directories of the OpenHatch repository
(``oh-mainline``; see :ref:`oh-getting-started` for more information).

To create the new directories::

  $ cd oh-mainline/mysite/missions
  $ mkdir makeamission
  $ mkdir templates/missions/makeamission

The first directory we create is the code directory. The second is the
template directory.

It will help other developers work on your code if you use the same
name for both directories. Note that we're making directories named
``makeamission``, not "Make a Mission". That's because the directory
name needs to be a valid Python package name, which means no spaces or
non-alphanumeric characters.

Within the code directory (``makeamission``), you'll need
to create an empty file named ``__init__.py``; this tells Python that
this directory is a `package`_. On Mac OS X and Linux, you can do this
by running the ``touch`` command::

  $ touch makeamission/__init__.py

On Windows, just create the file with your favorite (or second
favorite) text editor.

Defining Steps
--------------

Missions are made up of a sequence of steps: each step has a little
bit of Python code and an HTML template.

.. note::

   It may be helpful to refer to existing Mission code as you work on
   yours: examples are a great way to learn. The *Windows Setup*
   mission (in the ``setup`` directories) is an especially simple
   example.

Create a file named ``views.py`` in your code directory; we'll start
writing the Mission steps there.

The simplest type of Mission Step just renders a template. That's what
we'll start with. In ``views.py``, start with the following code::

  from mysite.missions.base import MissionBaseView


  class StepOne(MissionBaseView):
      url = '/'
      template_name = 'missions/makeamission/index.html'
      view_name = 'main-page'
      title = 'Setting up Your Mission'

This Python code defines the first step in our new Mission. There are
a few things to note:

* ``StepOne`` is the name of the step's *class*. This needs to be
  unique for your steps in the Mission.
* ``MissionBaseView`` is the basic building block of Mission Steps and
  provides some helpers you can use in the template.
* The ``url`` defines what the URL of this mission will be **within
  the Mission**. This must begin with a ``/``.
* The ``view_name`` (``main-page`` in this case) allows us to refer to
  this view in other views.
* The ``title`` will be displayed in the sidebar of the Mission.

After you've added the first step, let's add a second step::

  class StepTwo(MissionBaseView):
      url = '/templates'
      template_name = 'missions/makeamission/steptwo.html'
      title = 'Writing Mission Templates'

Note that here we've omitted ``view_name``. When it's omitted
OpenHatch uses the ``url`` setting (omitting the leading ``/``) for
the view name.


Step Templates
--------------

Each of the Steps we've defined refer to a template: these templates
will contain the text content for each step. OpenHatch uses `Django
templates`_, which add some logical functionality to plain HTML.

Let's start with the first step, ``StepOne``. In a new file
(``templates/missions/makeamission/index.html``), add the following
content::

  {% extends 'missions/mission_base.html' %}
  {% load base_extras %}

  {% block mission_main %}
  <div class='submodule fat'>
    <div class='head'>
      <h3>{{ title }}</h3>
    </div>
    <div class="body">

      <p>Real content here, please!</p>

      <p class="next_mission_link">
          <a href="{{ next_step_url }}">Go forward and make a template!</a></p>
    </div>
  </div>

  {% endblock mission_main %}

There are a few interesting things here:

* The first line tells OpenHatch that this page should be based on the
  common Mission template.
* ``{{ title }}`` and ``{{ next_step_url }}`` are substitutions:
  Mission views provide several conveniences so you don't have to
  repeat yourself. These include ``title`` (the step title),
  ``next_step_url`` (the URL of the next step), and ``prev_step_url``
  (the URL of the previous step).

The template for the second step should be named ``steptwo.html``,
which is what you specified in the class (``StepTwo``) above.


Mission Information
-------------------

Missions are made up of a sequence of steps, so we need to define what
order those steps come in. Missions also have some information of
their own, like their name and an identifier.

We'll define the sequence of steps and the metadata by adding the
following to our mission's ``views.py``::

    class MakeAMission(Mission):

        mission_id = 'make-a-mission'
        name = 'Writing New Missions'

        view_classes = (
            StepOne,
            StepTwo,
        )

We also need to modify the import at the top of that file to read::

    from mysite.missions.base import Mission, MissionBaseView


Making it Accessible
--------------------

The final step to writing your Mission is to make it accessible on the
site by telling OpenHatch how to route the URLs. Django projects define 
URL routing in a file cunningly named ``urls.py``. You can find this 
in the ``mysite`` directory. The first step to making your mission accessible 
is to tell ``urls.py`` where the file ``views.py`` for your new mission 
lives by adding an ``import`` statement near the top of ``urls.py`` right 
after the ``import`` statements for the existing training missions like so::

    import mysite.missions.makeamission.views

Next, if you open ``urls.py``, you'll find a list of URL patterns -- regular 
expressions which Django will use to match URLs and figure out where to 
send requests. The second and final step to making your mission accessible 
is to add the new mission by adding a new item after the other missions::

     (r'^missions/makeamission',
         include(mysite.missions.makeamission.views.MakeAMission.urls())),

Two important things to note:

* ``makeamission`` in the ``include`` and ``import`` statements above refer 
  to the directory you created, so you'll need to make sure the name matches.
* ``MakeAMission`` is the name you give your Mission class.

Once you've added it to the URLs, you can start the server and visit
http://localhost:8000/missions/makeamission/ to see your new mission!



.. _`Windows Setup`: http://openhatch.org/missions/windows-setup/
.. _`Subversion Training`: http://openhatch.org/missions/svn
.. _`package`: http://docs.python.org/tutorial/modules.html#packages
.. _`django templates`: https://docs.djangoproject.com/en/1.3/topics/templates/
