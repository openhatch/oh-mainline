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

* Adjust oh-bugimporters so that it generates output with data from your
  bug tracker of choice.

* Ensure the data imports properly, by running:

  python manage.py import_bugimporter_data < output_from_bugimporters.jsonlines

* Ensure the web UI shows an option for the new kind of bug tracker. To do
  that, take a look at mysite/customs/models.py.

In a little more detail
=======================

* Clone oh-bugimporters to your local machine, and oh-mainline in parallel,
  such that both folders are on the same level in the directory hierarchy.
* Initialize oh-bugimporters with::

    virtualenv env

  and::

    env/bin/python setup.py develop

  See also oh-bugimporters/docs/intro.rst for more infos about how to
  setup the subproject of oh-bugimporters for development and testing.
* Now add your new tracker to the bugimporter folder, by using one of
  the existing variants as template. If possible, add proper tests too.
* Create a testfile with basic queries and then run a command like::

    env/bin/scrapy runspider bugimporters/main.py -a input_filename=/tmp/input-configuration.yaml -s FEED_FORMAT=json -s FEED_URI=/tmp/results.json -s LOG_FILE=/tmp/scrapy-log -s CONCURRENT_REQUESTS_PER_DOMAIN=1 -s CONCURRENT_REQUESTS=200

  in the oh-bugimporters folder. Here /tmp/input-configuration.yaml is
  the prepared input file with the following basic content (may vary,
  depending on the bugtracker's implementation)::


    meta: {limit: 500, next: null, offset: 0, previous: null, total_count: 1}
    objects:
    - base_url: !!python/unicode 'http://scons.tigris.org/issues'
      bitesized_text: !!python/unicode 'Easy'
      bitesized_type: !!python/unicode 'key'
      bugimporter: !!python/unicode 'tigris'
      custom_parser: !!python/unicode ''
      documentation_text: !!python/unicode 'documentation'
      documentation_type: !!python/unicode 'subcomp'
      existing_bug_urls: []
      get_older_bug_data: null
      queries: [!!python/unicode 'http://scons.tigris.org/issues/xml.cgi']
      tracker_name: !!python/unicode 'SCons'

  After the run, check the log files /tmp/scrapy-log and /tmp/results.json
  for correct results.
* For the website part (note how we're switching to the oh-mainline folder
  now) you have to initialize your local installation of OpenHatch with the
  command::

    python manage.py syncdb --migrate --noinput

* Once you have changed the files mysite/customs/forms.py and models.py to
  add your new tracker type, you have to recreate the migration scripts for
  the customs folder. So call::

    python manage.py schemamigration customs --auto

  See also the page https://openhatch.org/wiki/Making_schema_changes for more
  infos on managing and updating schema changes.
* Now you can start the local OpenHatch site with::

    python manage.py runserver

  and direct your browser to it at http://localhost:8000 .
* Add a user and your project, and setup the new bug tracker for it, as you
  would do normally.
* Ensure that the base folder for temporary import files is writable for your
  current user. The default folder as used in ./run_importer.sh is::

    /var/web/inside.openhatch.org/crawl-logs
  
* Patch the import script ./run_importer.sh and change the URL for the
  OpenHatch site from "https://openhatch.org/..." to "http://localhost:8000".
  Otherwise, the run_importer script tries to download and update all bugs
  that are currently tracked at the real website...which might take a little
  while.
* Run the import script::

    ./run_importer.sh

  and wait for it to finish. Then reload the browser page and check that the
  bugs have indeed been imported properly.
* If you mixed things up, you can reset the database completely at any time
  with::

    python ./manage.py reset_db --router=default

  This will leave you with a blank OpenHatch instance, without any users,
  projects or bugs. Then rinse and repeat the steps above...

If you get stuck, please email the list or ping paulproteus or others in IRC!

Submit a patch
==============

This is the easiest part. See :doc:`/getting_started/handling_patches`!

