from django.core.management.base import BaseCommand
from mysite.base.models import Timestamp
from django.core.mail import send_mail
from mysite.profile.models import Person

class Command(BaseCommand):
    help = "Send out emails, at most once per week, to users who've requested a running summary of OpenHatch activity in their projects."

    TIMESTAMP_KEY = "When did we last send those weekly emails?"

    def handle(self, *args, **options):
        Timestamp.update_timestamp_for_string(Command.TIMESTAMP_KEY)
        people_who_want_email = Person.objects.filter(email_me_weekly_re_projects=True)
        for p in people_who_want_email:
            send_mail("Your weekly OpenHatch horoscope", "Message!!",
                    "all@openhatch.org", [p.user.email])
