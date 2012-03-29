=======================================
Getting started with the OpenHatch code
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

    $ git clone git://github.com/openhatch/oh-mainline.git

It will take up to five minutes, depending on your Internet connection. it's
kind of a big repository. (Sixty megabytes, or so.)


How to run a local site
=======================

Read installation.rst inside
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have the repository, open up the `installation.rst`_ file in any text
viewer (like gedit, or your favorite web browser).

Read it, and follow the few short steps to getting your local site going. It
should take about 5 minutes.


.. _installation.rst: installation.html


Next steps
==========

Get in touch
~~~~~~~~~~~~

We really recommend that you get in touch with us. (It's not quite mandatory,
but we'll all be happier if you do)

  1. Join the `Devel mailing list`_ and say hello.
  2. `the #openhatch IRC channel in freenode`_.

  We have weekly meetings, typically on Saturdays at 4pm EST (-5 UTC).


.. _Devel mailing list: http://lists.openhatch.org/mailman/listinfo/devel
.. _the #openhatch IRC channel in freenode: https://openhatch.org/wiki/Chat_with_us_on_IRC


Read more documentation
=======================

Before you start hacking OpenHatch, we strongly advise you to watch
`Learning new codebase`_ talk by Justin Lilly given during `DjangoCon 2010`_.

You can find more tips about hacking OpenHatch in the Category:Hacking_OpenHatch!

You can find things to work on by browsing our `bug tracker`_ or asking us!


.. _Learning new codebase: http://python.mirocommunity.org/video/1882/djangocon-2010-learning-a-new-
.. _DjangoCon 2010: http://python.mirocommunity.org/category/djangocon-2010
.. _bug tracker: http://openhatch.org/bugs/


Start contributing patches!
===========================

We mark issues that are particularly good for new contributors with the
"bitesize" keyword on our bug tracker. You can find the open easy issues `here`_.

If you find an issue you like and it isn't assigned to anyone, assign it to
yourself and start hacking (you'll need an OpenHatch account to log in to the
bug tracker). If it is assigned to someone already, but it looks like they
haven't gotten around to working on it, leave a note on the ticket saying that
you are interested in taking it (you can also try asking on IRC).

When you are ready to submit a patch for an issue, follow the guidelines at
`How we handle patches`_.

If you ever feel like you are getting stuck or could use some design feedback,
don't hesitate to ask for help on the IRC channel, on the devel mailing list,
or on the issue ticket. Attending the weekly development meetings on IRC is a
great time to ask for help or recommendations on issues to work on.


.. _here: https://openhatch.org/bugs/issue?@columns=title,id,activity,status,assignedto&@sort=activity&@group=priority&@filter=status,keyword&@pagesize=50&@startwith=0&status=-1,1,2,3,4,5,6,7,9,10&keyword=1&@dispname=bitesized
.. _How we handle patches: handling_patches.html
