from django.core.management.base import BaseCommand

import mysite.profile.tasks

class Command(BaseCommand):
    help = "Run this once daily for the OpenHatch profile app."

    def handle(self, *args, **options):
        # Garbage collect forwarders
        mysite.profile.tasks.GarbageCollectForwarders.apply()

        # Try to send the emails. The command will only actually send emails at
        # most once per week.
        command = mysite.profile.management.commands.send_weekly_emails.Command()
        command.run()
