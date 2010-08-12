import datetime
import logging

from django.core.management.base import BaseCommand

from mysite.search.models import Bug

class Command(BaseCommand):
    help = "A bunch of tools for checking and cleaning the Bug database."

    def list_old_bugs(self, days, hours=0):
        count = 0
        x_days_ago = (datetime.datetime.now() -
                        datetime.timedelta(days=days, hours=hours))
        for bug in Bug.all_bugs.filter(last_polled__lt=x_days_ago):
            count += 1
            print "%d - %s" % (count, str(bug))
        print "There are a total of %d Bug objects that are %d days %d hours old." % (count, days, hours)

    def list_closed_bugs(self):
        count = 0
        for bug in Bug.all_bugs.filter(looks_closed=True):
            count += 1
            print "%d - %s" % (count, str(bug))
        print "There are a total of %d closed Bug objects." % count

    def delete_old_bugs(self, days, hours=0):
        x_days_ago = (datetime.datetime.now() -
                        datetime.timedelta(days=days, hours=hours))
        Bug.all_bugs.filter(last_polled__lt=x_days_ago).delete()

    def delete_closed_bugs(self):
        Bug.all_bugs.filter(looks_closed=True).delete()

    def delete_all_bugs(self):
        Bug.all_bugs.all().delete()

    def show_usage(self):
        print """
usage: ./bin/mysite customs_debugger COMMAND

The following commands are available:
    list_old_bugs           List all Bug objects older than one day plus one hour.
    list_very_old_bugs      List all Bug objects older than two days.
    list_closed_bugs        List all Bug objects that look closed.
    delete_old_bugs         Delete all Bug objects older than one day plus one hour.
    delete_very_old_bugs    Delete all Bug objects older than two days.
    delete_closed_bugs      Delete all Bug objects that look closed.
    delete_all_bugs         Delete ALL Bug objects. Period. Useful if you want to
                            test a bug import from scratch. Not so useful on a
                            production server.

NOTE: These commands are executed immediately, so make sure you are
executing what you want, especially with the deleting commands."""

    def handle(self, *args, **options):
        if len(args) > 1:
            self.show_usage()
        elif 'list_old_bugs' in args:
            self.list_old_bugs(days=1, hours=1)
        elif 'list_very_old_bugs' in args:
            self.list_old_bugs(days=2)
        elif 'list_closed_bugs' in args:
            self.list_closed_bugs()
        elif 'delete_old_bugs' in args:
            self.delete_old_bugs(days=1, hours=1)
        elif 'delete_very_old_bugs' in args:
            self.delete_old_bugs(days=2)
        elif 'delete_closed_bugs' in args:
            self.delete_closed_bugs()
        elif 'delete_all_bugs' in args:
            self.delete_all_bugs()
        else:
            self.show_usage()
