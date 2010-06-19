import logging

from django.core.management.base import BaseCommand

import django.conf
django.conf.settings.CELERY_ALWAYS_EAGER = True

import mysite.search.tasks
import mysite.customs.bugtrackers.roundup_general
import mysite.customs.bugtrackers
import mysite.search.tasks.launchpad_tasks

import mysite.customs.miro
import mysite.customs.bugtrackers.trac
import mysite.customs.bugtrackers.gnome_love
import mysite.customs.bugtrackers.fedora_fitfinish
import mysite.customs.bugtrackers.mozilla
import mysite.customs.bugtrackers.wikimedia
import mysite.customs.bugtrackers.kde
import mysite.customs.bugtrackers.opensolaris

### All this code runs synchronously once a day.
### For now, we can crawl all the bug trackers in serial.

### One day, though, we will crawl so many bug trackers that it will take
### too long.

### I suggest that, at that point, we fork a number of worker processes, and
### turn these lists into a queue or something. That should be easy with the
### multiprocessing module. Then we can do N at once.

### We could do something smart with statistics, detecting the average
### refresh time within the bug tracker of a bug, then polling at some
### approximation of that rate. (But, really, why bother?)

### Since most of the time we're waiting on the network, we could also use
### Twisted or Stackless Python or something. That would be super cool, too.
### If somone can show me how to migrate this codebase to it, that'd be neat.
### I'm unlikely to look into it myself, though.

### (If at some point we start indexing absolutely every bug in free and open
### source software, then the above ideas will actually become meaningful.)

### -- New Age Asheesh, 2010-05-31.

class Command(BaseCommand):
    help = "Call this once a day to make sure we run Bug search-related nightly jobs."

    def update_bugzilla_trackers(self):
        bugzilla_trackers = {
            'Miro':
                mysite.customs.miro.grab_miro_bugs,
            'KDE junior jobs':
                mysite.customs.bugtrackers.kde.grab,
            'Wikimedia easy bugs':
                mysite.customs.bugtrackers.wikimedia.grab,
            'GNOME Love':
                mysite.customs.bugtrackers.gnome_love.grab,
            'Mozilla "good first bug"s':
                mysite.customs.bugtrackers.mozilla.grab,

            # FIXME
            # Really, the Bugzilla import code should be reworked to be as
            # clean and tidy as the Mercurial/Python/Roundup stuff, with
            # an abstract class with a .update() method.
            # Then simple sub-classes can handle each of the different projects'
            # details.

            # What the heck is up with the Fedora code being
            # special-cased like this? Well, I'll clean it up another day,
            # so long as it seems to work right now.
            'Fedora "fit and finish" new bugs':
                mysite.search.tasks.bugzilla_instances.learn_about_new_fedora_fit_and_finish_bugs,

            'Fedora "fit and finish" refreshing old bugs':
                mysite.search.tasks.bugzilla_instances.refresh_all_fedora_fit_and_finish_bugs,
            }

        for bugzilla_tracker in bugzilla_trackers:
            logging.info("Refreshing bugs from %s." % bugzilla_tracker)
            call_me = bugzilla_trackers[bugzilla_tracker]
            call_me()

    def find_and_update_enabled_roundup_trackers(self):
        enabled_roundup_trackers = []

        ### First, the "find" step
        for thing_name in dir(mysite.customs.bugtrackers.roundup_general):
            thing = getattr(mysite.customs.bugtrackers.roundup_general,
                            thing_name)
            if hasattr(thing, 'enabled'):
                if getattr(thing, 'enabled'):
                    enabled_roundup_trackers.append(thing)

        ### Okay, now update!
        for thing in enabled_roundup_trackers:
            logging.info("[Roundup] About to update %s" % thing)
            instantiated = thing()
            instantiated.update()

    def find_and_update_enabled_trac_instances(self):
        enabled_trac_instances = []

        ### First, the "find" step
        for thing_name in dir(mysite.search.tasks.trac_instances):
            thing = getattr(mysite.search.tasks.trac_instances,
                            thing_name)
            if hasattr(thing, 'enabled'):
                if getattr(thing, 'enabled'):
                    enabled_trac_instances.append(thing)

        ### Okay, now update!
        for thing in enabled_trac_instances:
            logging.info("[Trac] About to update %s" % thing)
            instantiated = thing()
            instantiated.update()

    def update_launchpad_hosted_projects(self):
        ### For Launchpad:
        # First, we ask the projects' bug trackers if there are new bugs we should know about
        mysite.search.tasks.launchpad_tasks.refresh_bugs_from_all_indexed_launchpad_projects()
        # Second, we go through our *own* database of Launchpad-sourced bugs, and make sure they are all up to date
        mysite.search.tasks.launchpad_tasks.refresh_all_launchpad_bugs()

    def update_opensolaris_osnet(self):
        mysite.customs.bugtrackers.opensolaris.update()

    def handle(self, *args, **options):
        self.update_opensolaris_osnet()
        self.update_launchpad_hosted_projects()
        self.find_and_update_enabled_trac_instances()
        self.find_and_update_enabled_roundup_trackers()
        self.update_bugzilla_trackers()
        

