==========================================
Adding a new bug tracker via git
==========================================

(You can also add a bug tracker `via the website <http://openhatch.readthedocs.org/en/latest/tutorials/adding_new_bug_tracker_web.html>`_.)

Clone the repository
====================

You will need to have a local copy of our git repository. You can read about
that in the :doc:`/getting_started/getting_started`.

You will also need a local copy of a sister project,
"oh-bugimporters". You can get that from https://github.com/openhatch/oh-bugimporters .

Overview of steps
=================

You will need to achieve all the following things:

* Adjust oh-bugimporters so that it generates output with data from your bug tracker of choice.

* Ensure the data imports properly, by running:

  python manage.py import_bugimporter_data < output_from_bugimporters.jsonlines

* Ensure the web UI shows an option for the new kind of bug tracker. To do that, take a look at mysite/customs/models.py.

Sorry this isn't more vebose. If you get stuck, please email the list or ping paulproteus or others in IRC!

Submit a patch
==============

This is the easiest part. See :doc:`/getting_started/handling_patches`!

