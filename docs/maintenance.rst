# Maintenance tasks #

The OpenHatch web app has some built-in features to help you maintain
an instance. This file lists those features and how to use them.

## Importing data snapshots ##

If you want your site to have a database filled with data like what is
on the main OpenHatch.org site, you can import a data snapshot.

See https://openhatch.org/wiki/Importing_a_data_snapshot for more
information about that. You can read our privacy policy at
https://openhatch.org/policies-etc/.

## How to run the bug importer ##

At present, there is no inbuilt automation of bug importing (celeryd
was causing too many problems). Run the following command to start a
bug import:

    ./manage.py customs_twist

Since this can take a while, it is a good idea to run this somewhere
where it won't prevent you from using your computer - for example,
inside a GNU screen session.

## Run the hourly tasks related to profiles ###

There's a management command that runs necessary maintenance tasks. At
time of writing, it tries to keep our cache of recommended bugs more
or less up to date with the state of the bug table in our database.

To run this maintenance task hourly, run these commands:

    # The following use of GNU screen is helpful for running maintenance tasks,
    # but is not necessary.
    screen -RD # Create an instance of screen, or attach to an existing one.
    # Type Ctrl-a, c to open a new screen
    while (true); do ./manage.py profile_hourly_tasks; sleep 1h; done
    # Type Ctrl-a, d to hide ("detach from") the screen

## Adding jQuery UI components

When you want to add a jQuery UI component, go here:

    http://jqueryui.com/download

Select the following options, plus yours:

* Sortable
* Accordion
* Tabs
* Progressbar

Note that the site will automatically select any dependencies (like jQuery UI's "Core").

First, under "Theme", select "No Theme". Under "Version", select "1.7.2 (stable release, for jQuery 1.3.2). Then click your little cartoon hand on the Download button.

Unzip the file in /tmp/, and just extract the file js/jquery-ui-1.7.2.custom.min.js, and cp it to mysite/static/js/. That will overwrite the existing jQuery UI bundle.

Be sure to check using git diff that the change you've introduced in git's view of that file is exactly what you expect.

Finally, don't forget to add your component to the list above, so the next person does the right thing.
