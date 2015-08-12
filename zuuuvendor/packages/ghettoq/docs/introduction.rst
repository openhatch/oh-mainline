============================================================================
ghettoq - Ghetto Queue using Redis or Django Models.
============================================================================

:version: 0.4.5

Introduction
============

ghettoq is a ghetto queue framework, used to implement Redis, MongoDB, 
Beanstalk, CouchDB, and Django database support for
`carrot`_

.. _`carrot`: http://pypi.python.org/pypi/carrot

Installation
============

You can install ``ghettoq`` either via the Python Package Index (PyPI)
or from source.

To install using ``pip``,::

    $ pip install ghettoq


To install using ``easy_install``,::

    $ easy_install ghettoq


If you have downloaded a source tarball you can install it
by doing the following,::

    $ python setup.py build
    # python setup.py install # as root

Examples
========

    >>> from ghettoq.simple import Connection
    >>> import simplejson

    >>> conn = Connection("redis", host="localhost", database=1)

    >>> # Publishing messages
    >>> q = conn.Queue("tasks")
    >>> payload = {"name": "George Constanza"}
    >>> q.put(simplejson.dumps(payload))

    >>> # Consuming messages
    >>> message = q.get()
    >>> simplejson.loads(message)
    {"name": "George Constanza"}

    # Empty raises ghettoq.messaging.Empty
    >>> q.get()
    Empty


Using Django database support
-----------------------------

If settings is already configured you don't have to specify any
connection options.

    >>> from ghettoq.simple import Connection

    >>> conn = Connection("database")
    >>> queue = conn.Queue(name="tasks")
    >>> queue.put("To whom it may concern")
    >>> queue.get()
    "To whom it may concern"

Using MongoDB support
-----------------------------

If settings is already configured you don't have to specify any
connection options. The settings attrs used are:

* BROKER_HOST: '127.0.0.1' if not set
* BROKER_PORT: 27017 if not set
* BROKER_VHOST (Database Name): 'ghettoq' if not set
* Collection name: "messages"... should be added support for BROKER_COL settings var?

    >>> from ghettoq.simple import Connection

    >>> conn = Connection("mongodb")
    >>> queue = conn.Queue(name="tasks")
    >>> queue.put("To whom it may concern")
    >>> queue.get()
    "To whom it may concern"

Using Beanstalk support
-----------------------------

Requires the beanstalkc python library. If settings is already configured you 
don't have to specify any connection options. The settings attrs used are:

* BROKER_HOST: 'localhost' if not set
* BROKER_PORT: 11300 if not set
* BROKER_VHOST: 'ghettoq' if not set

    >>> from ghettoq.simple import Connection

    >>> conn = Connection("beanstalk")
    >>> queue = conn.Queue(name="tasks")
    >>> queue.put("To whom it may concern")
    >>> queue.get()
    "To whom it may concern"

Beanstalk also supports priorities. Jobs with lower priory numbers are
executed before jobs with higher numbers. This number defaults to 0
and ranges from 0 to 2**32 - 1.

	>>> queue.put("spam", priority=3)
	>>> queue.get()
	"spam"

Using CouchDB support
-----------------------------

If settings is already configured you don't have to specify any
connection options. The settings attrs used are:

* BROKER_HOST: '127.0.0.1' if not set
* BROKER_PORT: 5984 if not set
* BROKER_VHOST (Database Name): 'ghettoq' if not set
* View name: "ghettoq/messages"

    >>> from ghettoq.simple import Connection

    >>> conn = Connection("couchdb")
    >>> queue = conn.Queue(name="tasks")
    >>> queue.put("To whom it may concern")
    >>> queue.get()
    "To whom it may concern"

The couchdb backend requires the couchdb python module.

License
=======

This software is licensed under the ``New BSD License``. See the ``LICENSE``
file in the top distribution directory for the full license text.

.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround

