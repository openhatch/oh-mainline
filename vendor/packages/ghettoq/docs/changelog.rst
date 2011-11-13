t================
 Change history
================

0.4.5
=====

* CouchDB backend added.

* Redis: Automatically cast port argument to int.

* Beanstalk: Now properly implements ``queue.purge``.

* Django dependency removed.

    :class:`collections.OrderedDict` is used instead of
    `django.utils.datastructures.SortedDict` when running on Python 2.7.
    If running on an older Python version, the :mod:`odict` package is added
    as a dependency.

* Now depends on the :mod:`uuid` module.

    The :mod:`uuid` module was added to Python 2.5. If running on older
    versions the compat package is added as a dependency.

0.4.4
=====

* Redis: Fied ``too many values to unpack`` errors.

    See http://github.com/ask/ghettoq/issues/#issue/6

0.4.3
=====

* Now sets the destination queue when restoring unacked messages.

    See http://github.com/ask/ghettoq/issues/#issue/7

* Regression broke restoring of unacked messages.

* ``connection.drain_events`` now supports the ``timeout`` argument.

0.4.2
=====

* Beanstalk backend added.

* Remove _consumers + _callbacks from thread local storage

    See http://github.com/ask/ghettoq/issues/#issue/5

* Redis: purge now returns number of messages deleted.

* Beanstalk: Added support for queue priorities and increased default receive
  timeout to 1.

0.4.1
=====
:release-date: 2010-07-19 11:30 A.M CEST

* Fixed ``invalid number of arguments for brpop command`` bug.

0.4.0
=====
:release-date: 2010-07-14 11:00 A.M CEST

* setup.py now works with Python 2.4.

* License information added to distribution.

* Redis: Now uses blpop instead of polling.
    This means version 2.0 of both the redis-server and the Python
    redis client is required to use the Redis backend.

* Redis: The specified database name must now be an integer.

    The following values are considered OK and are accepted:

    =====================================  =====================================
    **Provided Value**                     **Actual database used**
    =====================================  =====================================
    :const:`None`                          0 (default database is used)
    ``""``                                 0 (default database is used)
    ``"/"``                                0 (default database is used)
    ``"/1"``                               1
    ``"2"``                                2
    ``3``                                  3
    =====================================  =====================================


    **Note:** The backend does not check that specified database
    actually exists on the server.

* MongoDB: ``find_one`` and ``remove`` has been replaced with
    the atomic operation ``find_and_modify`` (see:
    http://www.mongodb.org/display/DOCS/findandmodify+Command).

* .taproot: Added support for ``drain_events()``


0.2.0
=====
:release-date: 2010-04-19 11:40 A.M CEST

* **IMPORTANT** database backend: The ``timestamp`` field has been renamed to
  ``sent_at`` as ``TIMESTAMP`` is a reserved word in Oracle databases.

  This means existing users will need to migrate their existing tables.
  In MySQL this can be done manually by using ``ALTER``::

  	ALTER TABLE ghettoq_message CHANGE timestamp sent_at DATETIME;



* Added support for MongoDB.
