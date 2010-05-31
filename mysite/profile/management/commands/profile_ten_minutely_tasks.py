import datetime
import logging

from django.core.management.base import BaseCommand

import staticgenerator

class Command(BaseCommand):
    help = "Run this once every 10 minutes for the OpenHatch profile app."

    def handle(self, *args, **options):
        # Every 10 minutes, refresh /+projects/
        staticgenerator.quick_publish('/+projects/')
