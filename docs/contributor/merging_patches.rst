===============
Merging patches
===============

**Objective**: Someone gives you a patch to OpenHatch. What now?


Steps
=====

::

  # Step 0. Fetch the patch file and get the latest code from "origin"
  wget http://openhatch.org/bugs/file33/whatever
  git fetch

  # Step 1. Create a new local topic branch, based on origin/master
  git checkout origin/master -b new_topic_branch

  # Step 2. Apply said file
  git am < file_created_by_wget.patch

  # Step 3. Make sure it worked
  # If it did work, you will have some commits on top of origin/master
  git log --decorate


Conclusion
==========

That's all you need to do, in order to apply a patch. You might want to now
*test* the patch, or provide feedback to the submitter.


Troubleshooting
===============

* Step one: Ping paulproteus.
* Step two: ???
* Step three: Chocolate!

