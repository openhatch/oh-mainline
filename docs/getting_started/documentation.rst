====================
Documentation Basics
====================

You can read the most up to date documentation online at this link:
http://openhatch.readthedocs.org/en/latest/index.html

Source files
============

The documentation source files can be found in the
`docs/ <https://github.com/openhatch/oh-mainline/tree/master/docs>`_
folder of the oh-mainline repository:
https://github.com/openhatch/oh-mainline/tree/master/docs

reStructuredText and Sphinx
===========================

The documentation for OpenHatch is built using Sphinx and deployed at
readthedocs. You can learn more about the Sphinx, which uses 
`reStructuredText (.rst files) format <http://docutils.sourceforge.net/rst.html>`_,
and 
`Sphinx deploy commands <http://sphinx.readthedocs.org/en/latest/index.html>`_.

Style
=====

We encourage you to help improve the OpenHatch documentation. We have a
:doc:`../advanced/styleguide` which gives an overview of our basic
documentation style and guidelines.

Changing or Adding Documentation
================================

Before making any changes, we recommend taking a moment to read the 
:doc:`../advanced/styleguide`.

Making changes to documentation via pull request
------------------------------------------------

To alter the documentation, you'll want to clone `the github repository <https://github.com/openhatch/oh-mainline>`_.  (Not sure what cloning 
is?  Read our version of `Git Basics. <https://openhatch.org/wiki/Git_Basics>`_)

Once you've got a local copy, you can edit the files in the `docs/ <https://github.com/openhatch/oh-mainline/tree/master/docs>`_ directory to make changes.  You may find the official Sphinx `reStructuredText 
primer <http://sphinx-doc.org/rest.html>`_ useful for that.

To see the changes rendered locally, you can run the render_docs.py script found in the tools folder of the oh-mainline repository::

  python tools/render_docs.py

You will find the documentation rendered into html format inside the docs/html folder of the oh-mainline repository.  You can view it in your 
browser and check that you like your changes before submitting them.  (Again, see `Git Basics <https://openhatch.org/wiki/Git_Basics>`_ for 
help submitting your changes.)

Once you submit your changes as a pull request and they have been merged by a maintainer, they will appear in the openhatch/oh-mainline repository.  
The openhatch.readthedocs.org/ files will update automatically via a github web hook.

.. note:: If you've create a new file or edited/deleted a "toctree", you may get an error "WARNING: document isn't included in any toctree".  This means 
            a file is not referenced by a table of contents anywhere.  Consider adding it to one.  See `Sphinx guide <http://sphinx-doc.org/markup/toctree.html>`_ or reference.)

Making changes to documentation via readthedocs/Github editor
-------------------------------------------------------------

If you're having trouble navigating the documentation by opening and editing files locally, you can also try paging through the readthedocs.  
Each page should have an 'Edit on Github' link in the righthand corner.  When you click this link, Github will automatically create a fork 
of the project for you (if one does not automatically exist).  Once you finish editing, make sure to submit a pull request.
