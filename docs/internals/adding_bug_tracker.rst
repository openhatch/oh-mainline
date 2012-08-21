==========================================
Step-by-step guide on adding a bug tracker
==========================================

There are other documents about our :ref:`bug_tracker_index`.


Clone the repository
====================

You will need to have a local copy of our git repository. You can read about
that at :doc:`/contributor/getting_started`.


Figure out what kind of bug tracker you're importing
====================================================

To find the bug tracker import code, do::

  cd mysite/customs/bugtrackers/

All our code lives inside "mysite". "customs" contains code that handles the
*importing* of data from other places on the Internet. (Get it? It's a pun.)
"bugtrackers" holds one file per type of bug tracker.

You'll find one file per *type* of bug tracker. For example, if you're adding
code to cause us to import data from a bug tracker that runs the *Roundup*
software, you'll need to be editing *roundup.py*.


Edit the right file
===================

Each file has several parts...

* **The raw code that goes out to the network and fetches data**:
  This is probably not what you want.
* **A general Python class for all project bug trackers of a particular type**:
  Also probably not what you want. This contains all the methods that every
  project bug tracker requires, to simplify the code structure.
* **One simple bit of code per project bug tracker we download data from**:
  This is what you want. It's a Python class that sub-classes the general one
  and contains the bits of code specific to each project bug tracker (such as
  the project name).

To add a new bug tracker, go to the very end of the file for the correct
tracker *type* and copy the generic class. Paste it just above and then edit as
necessary. There are several things that you will definitely need to change in
the class, like the project name and the URLs for fetching a list of bugs to
import, and there are a few things that are optional - read the comments, and
look at other project bug trackers in the file, to understand what each bit
does.


Make sure it works
==================

If you run::

  ./bin/mysite customs_daily_tasks

you should trigger your code. In your local version of OpenHatch, you'll see
the new volunteer opportunities listed at http://127.0.0.1:8000/search/.

You can monitor diagnostics about the bug importer in two ways. A quick
interface for checking the number of stale bugs (bugs older than one or two
days) is the diagnostic page at http://127.0.0.1:8000/+meta/.

For more in-depth analysis you can use the customs debugger, which contains
several handy methods for managing Bug objects - useful if, for example, you
always end up with ten stale bugs at the end of an import and want to find out
what they are. Just run::

  ./bin/mysite customs_debugger help

to see available options.

If your new bug tracker code doesn't get called, make sure you set
*enabled = True* in the subclass.

If you have problems getting it working, reach out to us for help!


Submit a patch
==============

This is the easiest part. See :doc:`/contributor/handling_patches`!

