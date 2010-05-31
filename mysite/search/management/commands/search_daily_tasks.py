from django.core.management.base import BaseCommand

import django.conf
django.conf.settings.CELERY_ALWAYS_EAGER = True

import mysite.search.tasks
import mysite.customs.bugtrackers.roundup_general
import mysite.search.tasks.launchpad_tasks

class Command(BaseCommand):
    help = "Enqueue jobs into celery that would cause it to recrawl various bug trackers."

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
            thing.update()

    def handle(self, *args, **options):
        # Make celery always eager, baby
        
        # A bunch of classes whose .run() we want to .delay()
        dot_run_these = [
            # Twisted
            mysite.search.tasks.trac_instances.LearnAboutNewEasyTwistedBugs,
            mysite.search.tasks.trac_instances.RefreshAllTwistedEasyBugs,
        ]
        for thing in dot_run_these:
            thing().run()

        # Just functions
        run_these = [
            # various projects hosted on Launchpad
            mysite.search.tasks.launchpad_tasks.refresh_bugs_from_all_indexed_launchpad_projects,
            mysite.search.tasks.launchpad_tasks.refresh_all_launchpad_bugs,

            # sweet sweet sugar
            mysite.search.tasks.trac_instances.learn_about_new_sugar_easy_bugs,
            mysite.search.tasks.trac_instances.refresh_all_sugar_easy_bugs,
        ]
        for callable in run_these:
            callable()

        # And for Roundup bug trackers, use our special handling
        self.find_and_update_enabled_roundup_trackers()
        

