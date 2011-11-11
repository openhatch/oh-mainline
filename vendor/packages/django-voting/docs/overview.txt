==============
Django Voting
==============

A generic voting application for Django projects, which allows
registering of votes for any ``Model`` instance.


Installation
============

Google Code recommends doing the Subversion checkout like so::

    svn checkout http://django-voting.googlecode.com/svn/trunk/ django-voting

But the hyphen in the application name can cause issues installing
into a DB, so it's really better to do this::

    svn checkout http://django-voting.googlecode.com/svn/trunk/ voting

If you've already downloaded, rename the directory before installing.

To install django-voting, do the following:

    1. Put the ``voting`` folder somewhere on your Python path.
    2. Put ``'voting'`` in your ``INSTALLED_APPS`` setting.
    3. Run the command ``manage.py syncdb``.

The ``syncdb`` command creates the necessary database tables and
creates permission objects for all installed apps that need them.

That's it!


Votes
=====

Votes are represented by the ``Vote`` model, which lives in the
``voting.models`` module.

API reference
-------------

Fields
~~~~~~

``Vote`` objects have the following fields:

    * ``user`` -- The user who made the vote. Users are represented by
      the ``django.contrib.auth.models.User`` model.
    * ``content_type`` -- The ContentType of the object voted on.
    * ``object_id`` -- The id of the object voted on.
    * ``object`` -- The object voted on.
    * ``vote`` -- The vote which was made: ``+1`` or ``-1``.

Methods
~~~~~~~

``Vote`` objects have the following custom methods:

    * ``is_upvote`` -- Returns ``True`` if ``vote`` is ``+1``.

    * ``is_downvote`` -- Returns ``True`` if ``vote`` is ``-1``.

Manager functions
~~~~~~~~~~~~~~~~~

The ``Vote`` model has a custom manager that has the following helper
functions:

    * ``record_vote(obj, user, vote)`` -- Record a user's vote on a
      given object. Only allows a given user to vote once on any given
      object, but the vote may be changed.

      ``vote`` must be one of ``1`` (up vote), ``-1`` (down vote) or
      ``0`` (remove vote).

    * ``get_score(obj)`` -- Gets the total score for ``obj`` and the
      total number of votes it's received.

      Returns a dictionary with ``score`` and ``num_votes`` keys.

    * ``get_scores_in_bulk(objects)`` -- Gets score and vote count
      details for all the given objects. Score details consist of a
      dictionary which has ``score`` and ``num_vote`` keys.

      Returns a dictionary mapping object ids to score details.

    * ``get_top(Model, limit=10, reversed=False)`` -- Gets the top
      ``limit`` scored objects for a given model.

      If ``reversed`` is ``True``, the bottom ``limit`` scored objects
      are retrieved instead.

      Yields ``(object, score)`` tuples.

    * ``get_bottom(Model, limit=10)`` -- A convenience method which
      calls ``get_top`` with ``reversed=True``.

      Gets the bottom (i.e. most negative) ``limit`` scored objects
      for a given model.

      Yields ``(object, score)`` tuples.

    * ``get_for_user(obj, user)`` -- Gets the vote made on the given
      object by the given user, or ``None`` if no matching vote
      exists.

    * ``get_for_user_in_bulk(objects, user)`` -- Gets the votes
      made on all the given objects by the given user.

      Returns a dictionary mapping object ids to votes.

Basic usage
-----------

Recording votes and retrieving scores
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Votes are recorded using the ``record_vote`` helper function::

    >>> from django.contrib.auth.models import User
    >>> from shop.apps.products.models import Widget
    >>> from voting.models import Vote
    >>> user = User.objects.get(pk=1)
    >>> widget = Widget.objects.get(pk=1)
    >>> Vote.objects.record_vote(widget, user, +1)

The score for an object can be retrieved using the ``get_score``
helper function::

    >>> Vote.objects.get_score(widget)
    {'score': 1, 'num_votes': 1}

If the same user makes another vote on the same object, their vote
is either modified or deleted, as appropriate::

    >>> Vote.objects.record_vote(widget, user, -1)
    >>> Vote.objects.get_score(widget)
    {'score': -1, 'num_votes': 1}
    >>> Vote.objects.record_vote(widget, user, 0)
    >>> Vote.objects.get_score(widget)
    {'score': 0, 'num_votes': 0}


Generic Views
=============

The ``voting.views`` module contains views to handle a couple of
common cases: displaying a page to confirm a vote when it is requested
via ``GET`` and making the vote itself via ``POST``, or voting via
XMLHttpRequest ``POST``.

The following sample URLconf demonstrates using a generic view for
voting on a model, allowing for regular voting and XMLHttpRequest
voting at the same URL::

    from django.conf.urls.defaults import *
    from voting.views import vote_on_object
    from shop.apps.products.models import Widget

    widget_dict = {
        'model': Widget,
        'template_object_name': 'widget',
        'allow_xmlhttprequest': True,
    }

    urlpatterns = patterns('',
        (r'^widgets/(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/?$', vote_on_object, widget_dict),
    )

``voting.views.vote_on_object``
--------------------------------

**Description:**

A view that displays a confirmation page and votes on an object. The
given object will only be voted on if the request method is ``POST``.
If this view is fetched via ``GET``, it will display a confirmation
page that should contain a form that ``POST``\s to the same URL.

**Required arguments:**

    * ``model``: The Django model class of the object that will be
      voted on.

    * Either ``object_id`` or (``slug`` *and* ``slug_field``) is
      required.

      If you provide ``object_id``, it should be the value of the
      primary-key field for the object being voted on.

      Otherwise, ``slug`` should be the slug of the given object, and
      ``slug_field`` should be the name of the slug field in the
      ``QuerySet``'s model.

    * ``direction``: The kind of vote to be made, must be one of
      ``'up'``, ``'down'`` or ``'clear'``.

    * Either a ``post_vote_redirect`` argument defining a URL must
      be supplied, or a ``next`` parameter must supply a URL in the
      request when the vote is ``POST``\ed, or the object being voted
      on must define a ``get_absolute_url`` method or property.

      The view checks for these in the order given above.

**Optional arguments:**

    * ``allow_xmlhttprequest``: A boolean that designates whether this
      view should also allow votes to be made via XMLHttpRequest.

      If this is ``True``, the request headers will be check for an
      ``HTTP_X_REQUESTED_WITH`` header which has a value of
      ``XMLHttpRequest``. If this header is found, processing of the
      current request is delegated to
      ``voting.views.xmlhttprequest_vote_on_object``.

    * ``template_name``: The full name of a template to use in
      rendering the page. This lets you override the default template
      name (see below).

    * ``template_loader``: The template loader to use when loading the
      template. By default, it's ``django.template.loader``.

    * ``extra_context``: A dictionary of values to add to the template
      context. By default, this is an empty dictionary. If a value in
      the dictionary is callable, the generic view will call it just
      before rendering the template.

    * ``context_processors``: A list of template-context processors to
      apply to the view's template.

    * ``template_object_name``:  Designates the name of the template
      variable to use in the template context. By default, this is
      ``'object'``.

**Template name:**

If ``template_name`` isn't specified, this view will use the template
``<app_label>/<model_name>_confirm_vote.html`` by default.

**Template context:**

In addition to ``extra_context``, the template's context will be:

    * ``object``: The original object that's about to be voted on.
      This variable's name depends on the ``template_object_name``
      parameter, which is ``'object'`` by default. If
      ``template_object_name`` is ``'foo'``, this variable's name will
      be ``foo``.

    * ``direction``: The argument which was given for the vote's
      ``direction`` (see above).

``voting.views.xmlhttprequest_vote_on_object``
-----------------------------------------------

**Description:**

A view for use in voting on objects via XMLHttpRequest. The given
object will only be voted on if the request method is ``POST``. This
view will respond with JSON text instead of rendering a template or
redirecting.

**Required arguments:**

    * ``model``: The Django model class of the object that will be
      voted on.

    * Either ``object_id`` or (``slug`` *and* ``slug_field``) is
      required.

      If you provide ``object_id``, it should be the value of the
      primary-key field for the object being voted on.

      Otherwise, ``slug`` should be the slug of the given object, and
      ``slug_field`` should be the name of the slug field in the
      ``QuerySet``'s model.

    * ``direction``: The kind of vote to be made, must be one of
      ``'up'``, ``'down'`` or ``'clear'``.

**JSON text context:**

The context provided by the JSON text returned will be:

    * ``success``: ``true`` if the vote was successfully processed,
      ``false`` otherwise.

    * ``score``: an object containing a ``score`` property, which
      holds the object's updated score, and a ``num_votes`` property,
      which holds the total number of votes cast for the object.

    * ``error_message``: if the vote was not successfully processed,
      this property will contain an error message.


Template tags
=============

The ``voting.templatetags.voting_tags`` module defines a number of
template tags which may be used to retrieve and display voting
details.

Tag reference
-------------

score_for_object
~~~~~~~~~~~~~~~~

Retrieves the total score for an object and the number of votes
it's received, storing them in a context variable which has ``score``
and ``num_votes`` properties.

Example usage::

    {% score_for_object widget as score %}

    {{ score.score }} point{{ score.score|pluralize }}
    after {{ score.num_votes }} vote{{ score.num_votes|pluralize }}

scores_for_objects
~~~~~~~~~~~~~~~~~~

Retrieves the total scores and number of votes cast for a list of
objects as a dictionary keyed with the objects' ids and stores it in a
context variable.

Example usage::

    {% scores_for_objects widget_list as scores %}

vote_by_user
~~~~~~~~~~~~

Retrieves the ``Vote`` cast by a user on a particular object and
stores it in a context variable. If the user has not voted, the
context variable will be ``None``.

Example usage::

    {% vote_by_user user on widget as vote %}

votes_by_user
~~~~~~~~~~~~~

Retrieves the votes cast by a user on a list of objects as a
dictionary keyed with object ids and stores it in a context
variable.

Example usage::

    {% votes_by_user user on widget_list as vote_dict %}

dict_entry_for_item
~~~~~~~~~~~~~~~~~~~

Given an object and a dictionary keyed with object ids - as returned
by the ``votes_by_user`` and ``scores_for_objects`` template tags -
retrieves the value for the given object and stores it in a context
variable, storing ``None`` if no value exists for the given object.

Example usage::

    {% dict_entry_for_item widget from vote_dict as vote %}

confirm_vote_message
~~~~~~~~~~~~~~~~~~~~

Intended for use in vote confirmatio templates, creates an appropriate
message asking the user to confirm the given vote for the given object
description.

Example usage::

    {% confirm_vote_message widget.title direction %}

Filter reference
----------------

vote_display
~~~~~~~~~~~~

Given a string mapping values for up and down votes, returns one
of the strings according to the given ``Vote``:

=========  =====================  =============
Vote type   Argument               Outputs
=========  =====================  =============
``+1``     ``'Bodacious,Bogus'``  ``Bodacious``
``-1``     ``'Bodacious,Bogus'``  ``Bogus``
=========  =====================  =============

If no string mapping is given, ``'Up'`` and ``'Down'`` will be used.

Example usage::

    {{ vote|vote_display:"Bodacious,Bogus" }}