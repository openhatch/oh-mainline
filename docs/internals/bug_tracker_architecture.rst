====================================
Bug tracker import code/architecture
====================================


About this page
===============

This document covers the **architecture** of our bug tracker import code. There
are other documents covering the :ref:`bug_tracker_index`.


One file per style of bug tracker
=================================

Each *style* (like "Bugzilla", "Roundup", and so forth) of bug tracker has its
code in mysite/customs/bugtrackers/*style*.py. We write tests in
mysite/customs/tests.py for each bug tracker type.

The Roundup code is instructive. Look at that in your favorite editor. You'll
see *class RoundupTracker*. Take a look -- the class's __init__() is built so
that an instance has enough data that a call to grab() will start downloading
bug data.

The rest of that file is trivial subclasses that pre-fill the data to
__init__(). We have one subclass per bug tracker we pull data from.


Then, once a day
================

We have a cron job on the server that calls the code in
*mysite/customs/management/commands/customs_daily_tasks.py* every night.


How to add a new bug tracker
============================

That means that if you want to add code pull data from a bug tracker we already
support, you just have to write a very simple subclass. For Roundup, for
example, add a few lines to the end of mysite/customs/bugtrackers/roundup.py.
Then submit a patch.

If you want to write support for an entirely new type of bug tracker, you'll
have to write a new class. Before we merge it, we'll need some tests, but we
can help you write the tests. Submit your patches as you go, and we can
review/merge quickly!

(Wondering how to submit a patch? Read :doc:`/contributor/handling_patches`.)

