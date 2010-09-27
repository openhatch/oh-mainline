import datetime
import logging
import sys

from django.core.management.base import BaseCommand

import mysite.profile.models

class Command(BaseCommand):
    help = "Reads a session ID on stdin, and prints an email address for the person."

    def handle(self, *args, **options):
        for session_id in sys.stdin:
            p = mysite.profile.models.Person.get_from_session_key(session_id.strip())
            print '"' + p.get_full_name_or_username() + '"',
            print '<' + p.user.email + '>'
