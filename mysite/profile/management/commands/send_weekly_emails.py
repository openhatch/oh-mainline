from django.core.management.base import BaseCommand
from mysite.base.models import Timestamp
from django.core.mail import EmailMultiAlternatives
from mysite.profile.models import Person
from django.db.models import Q
from mysite.profile.models import PortfolioEntry
from django.template.loader import render_to_string
from mysite.search.models import WannaHelperNote
import datetime
import logging
import html2text 

from django.core.urlresolvers import reverse
import mysite.profile.views
import uuid

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

        self.this_run_covers_things_up_until = datetime.datetime.utcnow()

        # Now all calls to filter() should include both of those dates: greater than ...since,
        # and less than up_until.

    def handle(self, *args, **options):

        SEVEN_DAYS = datetime.timedelta(days=7)

        # If it's been less than seven days since our last big email,
        # stop here and don't send any emails.
        if ((self.this_run_covers_things_up_until - self.this_run_covers_things_since) < 
                SEVEN_DAYS):
            logging.warn("Not sending emails; emails were last sent later than seven days ago.")
            return

        # If we made it this far in the function, it's been seven days or more
        # since our last email. Let's make a note that the time range of this
        # email extends until the timestamp stored in self.this_run_covers_things_up_until
        Timestamp.update_timestamp_for_string(Command.TIMESTAMP_KEY,
                override_time=self.this_run_covers_things_up_until)
        # ^^ This entry in the database will be used for calculating the time
        # range starting point of the next email

        # Now let's send some emails! :-)
        people_who_want_email = Person.objects.filter(email_me_weekly_re_projects=True)
        for person in people_who_want_email:
            message_in_plain_text, message_in_html = self.get_weekly_projects_email_for(person)
            if message_in_html: 
                print "Emailing %s their weekly project activity." % person.user.email
                email = EmailMultiAlternatives(
                        subject="News about your OpenHatch projects",
                        body=message_in_plain_text,
                        from_email="\"OpenHatch Mail-Bot\" <hello+mailbot@openhatch.org>",
                        headers={
                            'X-Notion': "I'm feeling a lot less evil now.",
                            },
                        to=[person.user.email])
                email.attach_alternative(message_in_html, "text/html")
                email.send()

    def get_weekly_projects_email_for(self, recipient):
        context = self.get_context_for_weekly_email_to(recipient)
        if context is None:
            return None, None

        # Create two slightly different template contexts

        plain_context = context.copy()
        rich_context = context.copy()

        plain_context['rich_text'] = False
        rich_context['rich_text'] = True

        message_in_simpler_html = render_to_string('weekly_email_re_projects.html', plain_context)
        message_in_html = render_to_string('weekly_email_re_projects.html', rich_context)
        
        # message_in_simpler_html is a string of HTML we've hand-tuned so that
        # when it is converted into Markdown it looks good in an email
        html2text.BODY_WIDTH = 72 # good for emails
        to_markdown = html2text.html2text
        message_in_plain_text = to_markdown(message_in_simpler_html)
        
        return message_in_plain_text, message_in_html

    @staticmethod
    def get_projects_this_person_cares_about(person):
        projects_i_contributed_to = [ pfe.project
                for pfe in person.get_published_portfolio_entries()]
        projects_i_wanna_help = [note.project
                for note in WannaHelperNote.objects.filter(person=person)]
        all_projects = set(projects_i_contributed_to + projects_i_wanna_help)
        return sorted(all_projects, key=lambda x: x.name.lower())

    def get_context_for_weekly_email_to(self, recipient):
        context = {}
        project_name2people = []

        within_range = Q(
                date_created__gt=  self.this_run_covers_things_since,
                date_created__lte=   self.this_run_covers_things_up_until)
        within_range_for_wh = Q(
                created_date__gt=  self.this_run_covers_things_since,
                created_date__lte=   self.this_run_covers_things_up_until)

        projects = Command.get_projects_this_person_cares_about(recipient)

        # Add contributors and wannahelpers in recipient's projects
        for project in projects:

            # Let's build a dictionary
            people_data = {}
            
            # Add contributors
            # ---------------------
            fellow_contributors_pfes = PortfolioEntry.published_ones.filter(
                within_range, project=project)
            display_these_contributors = [pfe.person for pfe in fellow_contributors_pfes]
            people_data['contributor_count'] = len(display_these_contributors)


            # Add wanna helpers
            # ---------------------
            notes = WannaHelperNote.objects.filter(within_range_for_wh, project=project)
            display_these_wannahelpers = [note.person for note in notes]
            people_data['wannahelper_count'] = len(display_these_wannahelpers)

            everybody = set(display_these_contributors + display_these_wannahelpers)
            if not everybody or everybody == set([recipient]):
                continue # to the next PortfolioEntry

            # Sort and slice lists of contributors and wannahelpers
            # --------------------------------------------

            # Sort
            display_these_contributors.sort(key=lambda x: x.get_coolness_factor('contributors'))
            display_these_wannahelpers.sort(key=lambda x: x.get_coolness_factor('wannahelpers'))
            
            # Put the recipient of the email at the end of any list he or she
            # appears in
            push_to_end_of_list(recipient, display_these_wannahelpers)
            push_to_end_of_list(recipient, display_these_contributors)

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

        context['recipient'] = recipient
        context['project_name2people'] = project_name2people
        token_string = recipient.generate_new_unsubscribe_token().string
        context['unsubscribe_link'] = "http://openhatch.org" + reverse(
                mysite.profile.views.unsubscribe, 
                kwargs={'token_string': token_string})
        return context 
