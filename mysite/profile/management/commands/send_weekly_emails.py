from django.core.management.base import BaseCommand
from mysite.base.models import Timestamp
from django.core.mail import send_mail
from mysite.profile.models import Person
from django.db.models import Q
from mysite.profile.models import PortfolioEntry

class Command(BaseCommand):
    help = "Send out emails, at most once per week, to users who've requested a running summary of OpenHatch activity in their projects."

    TIMESTAMP_KEY = "What's the endpoint of the time range of the last email we sent out?"

    @staticmethod
    def get_time_range_endpoint_of_last_email():
        return Timestamp.get_timestamp_for_string(Command.TIMESTAMP_KEY)

    def __init__(self):
        # At initialization time, we store the timestamp that this run is with regard to
        self.this_run_covers_things_since = Command.get_time_range_endpoint_of_last_email()

        # And it it covers things right up until the timestamp we're about to set
        Timestamp.update_timestamp_for_string(Command.TIMESTAMP_KEY)

        self.this_run_covers_things_up_until = Command.get_time_range_endpoint_of_last_email()

        # Now all calls to filter() should include both of those dates: greater than ...since,
        # and less than up_until.

    def handle(self, *args, **options):
        Timestamp.update_timestamp_for_string(Command.TIMESTAMP_KEY)
        people_who_want_email = Person.objects.filter(email_me_weekly_re_projects=True)
        for p in people_who_want_email:
            send_mail("Your weekly OpenHatch horoscope", "Message!!",
                    "all@openhatch.org", [p.user.email])

    def get_context_for_weekly_email_to(self, person):

        context = {}
        project_name2contributors = {}
        for pfe in person.get_published_portfolio_entries():

            # Let's build a dictionary
            project = pfe.project
            contributors_data = {}

            within_range = Q(
                    date_created__gte=  self.this_run_covers_things_since,
                    date_created__lt=   self.this_run_covers_things_up_until)

            pfes = PortfolioEntry.published_ones.filter(within_range, project=project)
            display_these_contributors = list([pfe.person for pfe in pfes])
            contributors_data['contributor_count'] = len(display_these_contributors)
            try:
                display_these_contributors.remove(person)
                recipient_is_a_recent_contributor = True
            except ValueError:
                # list.remove raises a ValueError if the person isn't in the list
                recipient_is_a_recent_contributor = False
            display_these_contributors.sort(key=lambda x: x.get_coolness_factor())
            contributors_data['recipient_is_a_recent_contributor'
                    ] = recipient_is_a_recent_contributor
            contributors_data['display_these_contributors'] = display_these_contributors[:3]
            project_name2contributors[project.name] = contributors_data

        context['project_name2contributors'] = project_name2contributors
        return context 
