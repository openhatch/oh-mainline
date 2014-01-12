==========
Deployment
==========

This is a quick-and-dirty page explaining how to deploy new versions of the
OpenHatch code.


Prerequisites
=============

* You must be part of the :doc:`/contributor/login_team` (so your SSH key is available in Github
  and you're in the openhatch-committers group, and also that your SSH key is in
  the deploy@linode.openhatch.org account's .ssh/authorized_keys)
* You must be at a computer with that SSH key
* Deploying takes about 3 minutes, maybe less if things go well. (If there are
  database migrations to run, it can take dramatically longer.)


How the deploy script works
===========================

You need to have these programs installed: **ssh**, **git**.

The script does two things:

* Push your current git HEAD onto origin/master.
* SSHs (once) to the linode, where it runs mysite/scripts/deploy_myself.sh which
  updates the site.


Recommended way to use the deploy script
========================================

::

    # Make sure .git/config has these 2 lines
    [remote "origin"]
	url = git@github.com:openhatch/oh-mainline.git
     
    git fetch  # get the latest

    git checkout origin/master -b deploy_me  # create a deploy_me branch

    # Then get the patch file with e.g. wget, and do:
    # Import the patch into current branch, probably called deploy_me
    git am /path/to/the/patch.file

    git log  # and sanity-check it

    # If you like it, do:
    cd mysite
    ./scripts/deploy

It's really important to make the separate branch so that you don't accidentally
push random local work into the live site.

Notes about the deployment
==========================

Here are some relevant details of how web requests get routed to the OpenHatch code.

* Web requests hit CloudFlare, which proxies them to linode.openhatch.org.

* linode.openhatch.org has an nginx that dispatches them to Apache.

* Apache mod_wsgi dispatches them to the mysite/scripts/app.wsgi.

* In production, we use a mysite/local_settings.py file that imports mysite/deployment_settings.py and overrides the Django SECRET_KEY.


Other sites we host
===================

The OpenHatch infrastructure hosts some other websites, including
bostonpythonworkshop.com and corp.openhatch.org. For information about that, read
the `documentation on the wiki about static site hosting`_.

.. _documentation on the wiki about static site hosting: https://openhatch.org/wiki/Static_site_hosting
