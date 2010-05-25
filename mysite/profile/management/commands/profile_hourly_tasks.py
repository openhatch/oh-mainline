from django.core.management.base import BaseCommand

import mysite.profile.tasks

class Command(BaseCommand):
    help = "Run this once hourly for the OpenHatch profile app."

    def handle(self, *args, **options):
        mysite.profile.tasks.sync_bug_epoch_from_model_then_fill_recommended_bugs_cache()
        mysite.profile.tasks.fill_recommended_bugs_cache()
