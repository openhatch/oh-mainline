from django.core.management.base import BaseCommand

import logging
import mysite.profile.tasks

class Command(BaseCommand):
    help = "Run this once daily for the OpenHatch profile app."

    def handle(self, *args, **options):
        # Garbage collect forwarders
        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.WARN)
        mysite.profile.tasks.GarbageCollectForwarders().run()

