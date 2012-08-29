=============
Documentation
=============

The documentation for openhatch is written and deployed using Sphinx. You can
learn more about the sphinx format and deploy commands at:
http://sphinx.readthedocs.org/en/latest/index.html

You can read the most up to date documentation online at this link:
http://openhatch.readthedocs.org/en/latest/index.html

Writing and deploying documentation locally
===========================================

All our documentation can be found in the docs folder inside oh-mainline
repository. All the documentation is written in plain text files with a .rst
extension following the Sphinx syntax.

For deploying the documentation you can use the render_docs.py script under the
tools folder of the oh-mainline repository::

  python tools/render_docs.py

You will find the documentation in html format inside the docs/html folder of
the oh-mainline repository.
