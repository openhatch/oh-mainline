=================
README for Sphinx
=================

Installing
==========

Use ``setup.py``::

   python setup.py build
   sudo python setup.py install


Reading the docs
================

After installing::

   cd doc
   sphinx-build . _build/html

Then, direct your browser to ``_build/html/index.html``.

Or read them online at <http://sphinx-doc.org/>.


Testing
=======

To run the tests with the interpreter available as ``python``, use::

    make test

If you want to use a different interpreter, e.g. ``python3``, use::

    PYTHON=python3 make test


Contributing
============

Send wishes, comments, patches, etc. to sphinx-dev@googlegroups.com.
