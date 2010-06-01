from django.core.management.base import BaseCommand

import mysite.profile.tasks

class Command(BaseCommand):
    help = "Run this once daily for the OpenHatch profile app."

    def handle(self, *args, **options):
        # Garbage collect forwarders
        mysite.profile.tasks.GarbageCollectForwarders.apply()

