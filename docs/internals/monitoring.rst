==========
Monitoring
==========


The basics
==========

* *linode.openhatch.org* is the main OpenHatch box, which runs the website.
* *linode2.openhatch.org* is the secondary server for OpenHatch.
  It hosts Nagios!
* *vm3.openhatch.org* is a third server, hosted at GPLHost, that runs the
  Jenkins continuous integration server.
* The Nagios configuration is owned by a user called *nagios* on
  *linode2.openhatch.org*.


Access
======

* We use ssh keys for login.
* If you want SSH access to that account, file a bug requesting it, and attach
  an SSH key. You should hear back within 2 days; if you don't hear back by
  then, try to find paulproteus or jesstess on IRC.
* Then you can do::

    ssh nagios@linode2.openhatch.org

* You'll know it's working if you are logged in. If you see a "Password:"
  prompt, then it is not working.


Notifications
=============

* Nagios notifications go to
  `monitoring@lists.openhatch.org`_. Anyone can
  subscribe to this list or read its archives.


.. _monitoring@lists.openhatch.org:
    http://lists.openhatch.org/mailman/listinfo/monitoring


Making changes
==============

In brief, here's what you need to know:

* Edit files in ~nagios/

* Once you know what changes you want to make, create a local branch with those
  changes::

    git checkout -b my_changes

* As you make changes, make meaningful commits. Also, tell "git commit" to use
  your identity::

    git commit --author="Some Body <some.body@example.com>"

* After you have made the changes, ask someone to review them and merge the
  changes to *master*.

* **Rationale**: If you stick to the above process, it is fairly easy to roll
  back to the "master" branch of the Nagios configuration.

* **History**: We came up with this process during `issue332`_.


.. _issue332: https://openhatch.org/bugs/issue332



Viewing the web interface, and handling the daemon
==================================================

* On *linode2*, *~nagios/secrets/* contains the mailman and Nagios web
  interface passwords.
* View the Nagios web interface at http://linode2.openhatch.org/nagios3/
* To restart the Nagios daemon, run ::

    sudo /etc/init.d/nagios3 restart


In case of emergency
====================

* See :doc:`/internals/emergency_operations`. People with ssh keys set up for
  the Linode Shell (Lish) can reboot the box and have other limited emergency
  capabilities.


TODOs
=====

* Send Nagios notifications to IRC (*#openhatch-auto*?)?
* Make the Nagios web interface world-viewable.
* Version the monitoring configurations.
* Send SMS alerts to people who want them.
* Add historical trending (Munin)?


Related
=======

* See also :doc:`/internals/emergency_operations`
* See also the page about the :doc:`/community/login_team`

