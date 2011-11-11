This directory contains a Django application called sessionprofile.  Add it
to your project to make it maintain a table that maps sessions to user
objects.  This is useful when you want to access the current session's
Django user ID from outside Django - for example, when you are integrating
Django with phpBB.

Install it by executing

    python setup.py install


The following instructions show how to create a minimal project that does
nothing but test the install.

1. You will need to modify the settings.py of your project

    * Add the line

        'sessionprofile.middleware.SessionProfileMiddleware',

      to your MIDDLEWARE_CLASSES, *before* SessionMiddleware.

    * Add the line

        'sessionprofile',

      to your INSTALLED_APPS.


2. Add the required table to your DB; run

    python manage.py syncdb

   ...creating an appropriate admin user.


3. Go to the admin pages at http://localhost:8000/admin/


4. In your DB, check the sessionprofile_sessionprofile table.
   You should have one session profile, with a null user.


5. Log in as your admin user.


6. In your DB, check the sessionprofile_sessionprofile table.
   You should have one session profile, associated with the
   admin user.


If you've got this far, everything is working fine and you
should be able to integrate the sessionprofile app with your
own project.

You may also want to take advantage of the extra
cleanup_inactive_sessions.py command, which removes all
expired Django sessions and their associated entries in
the sessionprofile_sessionprofile table.  It was written by
Russ Neufeld and should be run from cron instead of Django's
session cleaner.

-------------------------------------------------------------------------------

Any problems?  Let us know at

    django-php-auth@resolversystems.com
