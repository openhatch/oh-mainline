.. _oh-getting-started:

=======================================
Contributor Guide
=======================================

To get your own instance of OpenHatch running, follow these steps and then get
in touch with us.

The code is written in Python. It uses the Django toolkit and tries to stick to
good software testing practices. If you have Python experience, you should be
able to get hacking pretty quickly even if you don't know Django or testing.


Getting the source
==================

OpenHatch source code can be seen through a web interface at
https://github.com/openhatch/oh-mainline

To make contributions, you will need to clone our git repository. This requires
having the git version control system installed. Once you do, type this into a
terminal::

    $ git clone https://github.com/openhatch/oh-mainline.git

It will take up to five minutes, depending on your Internet connection. it's
kind of a big repository. (Sixty megabytes, or so.)


How to run a local site
=======================

Read installation.rst inside getting_started directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have the repository, open up the installation.rst file in any
text viewer (like gedit, or your favorite web browser).
(This is the same file as :doc:`installation`.)


Read it, and follow the few short steps to getting your local site going. It
should take about 5 minutes.


Next steps
==========

Get in touch
~~~~~~~~~~~~

We really recommend that you get in touch with us. (It's not quite mandatory,
but we'll all be happier if you do)

  1. Join the `Devel mailing list`_ and say hello.
  2. :doc:`the #openhatch IRC channel in freenode </community/contact>`.


OpenHatch holds development meetings on IRC; our goal is to hold these meetings weekly. The meetings are announced on `devel@openhatch.org`. Please join us on IRC and share your ideas or ask questions.

.. _Devel mailing list: http://lists.openhatch.org/mailman/listinfo/devel


Read more documentation
=======================

Before you start hacking OpenHatch, we strongly advise you to watch
`Learning new codebase`_ talk by Justin Lilly given during `DjangoCon 2010`_.

You can find more tips about hacking OpenHatch in the Category:Hacking_OpenHatch!

You can find things to work on by browsing our `bug tracker`_ or asking us!


.. _Learning new codebase: http://pyvideo.org/video/40/djangocon-2010--learning-a-new-codebase
.. _DjangoCon 2010: http://pyvideo.org/category/23/djangocon-2012
.. _bug tracker: http://openhatch.org/bugs/


Start contributing!
===========================

We mark issues that are particularly good for new contributors with the
"bitesize" keyword on our bug tracker. You can find the open easy issues `here`_.

If you find an issue you like and it isn't assigned to anyone, assign it to
yourself and start hacking (you'll need an OpenHatch account to log in to the
bug tracker). If it is assigned to someone already, but it looks like they
haven't gotten around to working on it, leave a note on the ticket saying that
you are interested in taking it (you can also try asking on IRC).

When you are ready to submit a contribution for an issue, follow the guidelines at
:doc:`/getting_started/handling_contributions`.

If you ever feel like you are getting stuck or could use some design feedback,
don't hesitate to ask for help on the IRC channel, on the devel mailing list,
or on the issue ticket. Attending the weekly development meetings on IRC is a
great time to ask for help or recommendations on issues to work on.


.. _here: https://openhatch.org/bugs/issue?@columns=title,id,activity,status,assignedto&@sort=activity&@group=priority&@filter=status,keyword&@pagesize=50&@startwith=0&status=-1,1,2,3,4,5,6,7,9,10&keyword=1&@dispname=bitesized
