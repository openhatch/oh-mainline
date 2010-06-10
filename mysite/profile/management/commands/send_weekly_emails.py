from django.core.management.base import BaseCommand
from mysite.base.models import Timestamp
from django.core.mail import send_mail
from mysite.profile.models import Person
from django.db.models import Q
from mysite.profile.models import PortfolioEntry
from django.template.loader import render_to_string


def push_to_end_of_list(an_object, a_list):
    try:
        a_list.remove(an_object)

        # If we reach this line, then the object *was* in the list before.
        a_list.append(an_object)
    except ValueError:
        # list.remove raises a ValueError if the object isn't in the list
        # But if the object isn't a contributor, no matter
        pass

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
        for person in people_who_want_email:
            context = self.get_context_for_weekly_email_to(person)
            # NB: "context" is None when there's no email to send to this person
            if context: 
                message = render_to_string('weekly_email_re_projects.txt', context)
                send_mail("Your weekly OpenHatch horoscope", message,
                        "all@openhatch.org", [person.user.email])

    def get_context_for_weekly_email_to(self, recipient):
        context = {}
        project_name2people = []

        within_range = Q(
                date_created__gte=  self.this_run_covers_things_since,
                date_created__lt=   self.this_run_covers_things_up_until)

        # Add contributors and wannahelpers in recipient's projects
        pfes = recipient.get_published_portfolio_entries()
        for pfe in pfes.order_by('project__name'):

            import pdb; pdb.set_trace() 

            project = pfe.project

            # Let's build a dictionary
            people_data = {}
            
            # Add contributors
            # ---------------------
            fellow_contributors_pfes = PortfolioEntry.published_ones.filter(
                    within_range, project=project)
            display_these_contributors = [pfe.person for pfe in fellow_contributors_pfes]
            people_data['contributor_count'] = len(display_these_contributors)

            push_to_end_of_list(recipient, display_these_contributors)

            # Add wanna helpers
            # ---------------------
            # FIXME: Add "within_range" as a filter below
            display_these_wannahelpers = list(project.people_who_wanna_help.all())

            # Temporarily add this for testing purposes
            assert display_these_wannahelpers

            people_data['wannahelper_count'] = len(display_these_wannahelpers)
            push_to_end_of_list(recipient, display_these_wannahelpers)

            everybody = (display_these_contributors + display_these_wannahelpers)
            if not everybody or everybody == [recipient]:
                continue # to the next PortfolioEntry

            # Sort and slice lists of contributors and wannahelpers
            # --------------------------------------------

            # Sort
            display_these_contributors.sort(key=lambda x: x.get_coolness_factor())
            display_these_wannahelpers.sort(key=lambda x: x.get_coolness_factor())

            # Slice
            display_these_contributors = display_these_contributors[:3]
            display_these_wannahelpers = display_these_wannahelpers[:3]

            # Add to dictionary
            people_data['display_these_contributors'] = display_these_contributors
            people_data['display_these_wannahelpers'] = display_these_wannahelpers

            # Store dictionary inside tuple
            project_name2people.append((project.name, people_data))

        if not project_name2people:
            # If there's no news to report, signal this fact loudly to the caller
            return None

        context['person'] = recipient
        context['project_name2people'] = project_name2people
        return context 
