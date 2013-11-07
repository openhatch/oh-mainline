=============
Documentation
=============

You can read the most up to date documentation online at this link:
http://openhatch.readthedocs.org/en/latest/index.html

The files for that documentation can be found in the `docs/ <https://github.com/openhatch/oh-mainline/tree/master/docs>`_ folder of the main 
repository:
https://github.com/openhatch/oh-mainline/tree/master/docs

The documentation for openhatch is built by sphinx and deployed by readthedocs. You can learn more about the sphinx format, which utilizes 
reStructuredText (.rst files), and sphinx deploy commands at:
http://sphinx.readthedocs.org/en/latest/index.html

Making changes to documentation via pull request
===========================================

To alter the documentation, you'll want to clone `the github repository <https://github.com/openhatch/oh-mainline>`_.  (Not sure what cloning 
is?  Read our version of `Git Basics. <https://openhatch.org/wiki/Git_Basics>`_)

Once you've got a local copy, you can edit the files in the `docs/ <https://github.com/openhatch/oh-mainline/tree/master/docs>`_ directory to make changes.  You may find the official Sphinx `reStructuredText 
primer <http://sphinx-doc.org/rest.html>`_ useful for that.

To see the changes rendered locally, you can run the render_docs.py script found in the tools folder of the oh-mainline repository::

  python tools/render_docs.py

(If you've create a new file or edited/deleted a "toctree", you may get an error "WARNING: document isn't included in any toctree".  This means 
a file is not referenced by a table of contents anywhere.  Consider adding it to one.  See `Sphinx guide <http://sphinx-doc.org/markup/toctree.html>`_ 
for reference.)

You will find the documentation rendered into html format inside the docs/html folder of the oh-mainline repository.  You can view it in your 
browser and check that you like your changes before submitting them.  (Again, see `Git Basics <https://openhatch.org/wiki/Git_Basics>`_ for 
help submitting your changes.)

Once you submit your changes as a pull request and they have been merged by a maintainer, they will appear in the openhatch/oh-mainline repository.  
The openhatch.readthedocs.org/ files will update automatically via a github web hook.

Making changes to documentation via readthedocs/Github editor
===========================================

If you're having trouble navigating the documentation by opening and editing files locally, you can also try paging through the readthedocs.  
Each page should have an 'Edit on Github' link in the righthand corner.  When you click this link, Github will automatically create a fork 
of the project for you (if one does not automatically exist).  Once you finish editing, make sure to submit a pull request.

