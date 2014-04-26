=====================
Advanced installation
=====================

This file contains information on things that you don't have to do! If
you're a completionist or really just like installing dependencies or
reading the OpenHatch documentation, keep reading.

Overriding local settings
=========================

If you wish to override the default settings, you may create a
separate file with individual settings you wish to change.
There is a hook at the end of the in mysite/settings.py that allows
contributors to override indiviual settings. To override settings,
create a new file in the mysite directory and name it local_settings.py.
You can place any settings you wish to override in this file.

Automated testing
=================

The OpenHatch code comes with automated tests that you can run to make
sure that it is set up To execute all tests, run this command::

  python manage.py test

For more about tests visit: http://openhatch.org/wiki/Automated_testing

Postfix, postmap and testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The code for site creates a configuration file for an email service,
Craigslist-style, that lets all users have an anonymous inbound email
address that goes to them. In particular, the code configures a
Postfix-based alias map for this. When that alias map changes, we notify
Postfix by calling postmap.

If the postmap binary (/usr/sbin/postmap) is not available on the system,
it is better not to try running that binary during testing. So before
tests we check for presence of the postmap binary and log a warning if
it is not present on the system.

Optional dependencies
=====================

You will probably see some warnings when you run the site, providing
you information about extra dependencies.

These extra dependencies require compiled code, AKA Python C
extensions. Depending on your operating system, you might install
these using a GUI installer, the program "pip", or a package manager
like apt-get.

For each dependency, we specify how to get it with pip *or*
apt-get. If you have a Debian or Ubuntu system, use the apt-get
instructions. Otherwise, try pip. (And if it doesn't work, ask for
help quickly.)


Re-scaling images
~~~~~~~~~~~~~~~~~

When you add a profile photo, and at other times, the site attempts to
rescale the image to fit into the visual constraints of the
page. Django and the OpenHatch code work together with PIL (the Python
Imaging Library) to transform images.

PIL requires some C dependencies, so the site can function without
it. If you want image rescaling to work, you must install PIL.

To do that, run one of these commands::

  $ sudo apt-get install python-imaging
  $ pip install PIL


Bug import dependencies
~~~~~~~~~~~~~~~~~~~~~~~

If you want to modify the code that downloads bugs (AKA "volunteer
opportunities") from other projects, you need these dependencies:

lxml: An XML and HTML parsing library ::

  $ sudo apt-get install python-lxml
  $ pip install lxml


Bug Importers
~~~~~~~~~~~~~

If you want to use the customs bug importers, they will need to be installed.
You can do this in one of the following ways:

* pip install https://github.com/openhatch/oh-bugimporters.git  # (readonly)
* Clone the repo into a folder at the same level as oh-mainline.


Training missions: System tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most of the training missions work fine without installing any extra
dependencies. There are two exceptions.

The Subversion training mission requires that you have the 'svnadmin'
tool installed. To get it on Debian or Ubuntu, do::

  $ sudo apt-get install subversion

Subversion repositories for the svn training missions are stored in
mysite/missions-userdata/svn. This directory must be available via
svnserve for users to be able to do the svn missions.  See
mysite/missions-userdata/svn/README to read how to set up svnserve.

On Windows and Mac, the code currently can't find svnadmin.

The git training mission expects to find "git" on your system path. On
Debian/Ubuntu systems, do::

  $ sudo apt-get install git-core


Maintenance
===========

You may want to read about how to maintain an OpenHatch site. `maintenance.rst`_ tells
you about that.


.. _maintenance.rst: maintenance.html
