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

For deploying the documentation it is necessary to install python-sphinx package.
Once installed the documentation can be compiled locally. To see how the
documentation looks go to the docs folder inside oh-mainline repository and
issue this command (Change <destination-folder> for the folder where you want
the documentation to be deployed, if the folder doesn't exist it will be
created)::

  sphinx-build -b html . <destination-folder>

Now you can go to <destination-folder> and double click on index.html to see the
main index for the documentation. You can navigate from there following the
links.
