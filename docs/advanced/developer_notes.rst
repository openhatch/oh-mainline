===============
Developer Notes
===============

This section of the documentation is intended to provide developers
with technical information that is helpful to know. This information
will typically only be necessary for the short term (less than 6
months) as developers collaborate on larger issues that require
a longer development timeframe.

We make this information available since it will likely be useful
beyond the scope of one individual issue in our GitHub issue tracker.

January 2015 Notes
==================

DataImportAttempts (DIAs)
-------------------------
DataImportAttempt is a model that contains metadata about when the
profile importer (the thing that attempts to automatically fill in
your list of projects you've contributed to, by letting you type in
a query like 'asheesh@ahseesh.org', and then the code will trigger
some background HTTP GETs to other services (see -- an attempt to
import data!) and log a note about this attempt in a model called
DataImportAttempt. We no longer do automatic profile importing, so
we don't need DIAs.

Twill
-----
Twill being phased out of our tests and is being replaed with the use of webtest.

Ohloh
-----
For project icons, we will be moving away from the use of Ohloh (now
know as OpenHub). Ohloh is not used for any other purpose in the
OpenHatch codebase. We will refactor the way project icons are fetched so we get them a different way than through Ohloh.
