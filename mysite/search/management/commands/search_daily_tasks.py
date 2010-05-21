from django.core.management.base import BaseCommand

import mysite.search.tasks
import django.conf

class Command(BaseCommand):
    help = "Enqueue jobs into celery that would cause it to recrawl various bug trackers."

    def handle(self, *args, **options):
        # Make celery always eager, baby
        django.conf.settings.CELERY_ALWAYS_EAGER = True
        
        # A bunch of classes whose .run() we want to .delay()
        dot_run_these = [
            mysite.search.tasks.LearnAboutNewPythonDocumentationBugs,
            mysite.search.tasks.LearnAboutNewEasyPythonBugs,
            mysite.search.tasks.GrabPythonBugs
        ]
        for thing in dot_run_these:
            thing().run()

