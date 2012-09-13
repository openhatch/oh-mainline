========================
Backups of the live site
========================


Overview
========

We have a free, donated account from rsync.net that lets us store 50GB of data
there.

We use duplicity (as per the rsync.net `official document`_). We do full backups
weekly and incrementals daily. We encrypt these backups.

The only server essential to continued operation of the site is
linode.openhatch.org. The other servers do unimportant things that do not keep
state. It would be convenient to have backups for them, but it is not
essential, so for now I suggest we simply skip it.

.. _official document: http://www.rsync.net/resources/howto/duplicity.html


Details
=======

We use this script to run backups. It runs via root's crontab, and emails the
results to Asheesh daily.

* do_backup.sh: `in git`_

.. _in git: https://github.com/openhatch/oh-restore/blob/master/do_backup.sh


Restoring
=========

duplicity has a built-in "verify" feature, which checksums the data, but that
doesn't help us ensure that our backup was complete.

Therefore, weekly, we automatically restore and test the virtual machine, via a
Jenkins job. http://openhatch.org/bugs/issue530 describes that.


More info about encryption
==========================

This backup is encrypted with a GPG key that has been emailed to hello
@openhatch.org on Thu, Jan 26.

