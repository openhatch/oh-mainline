# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
import HTMLParser
import html2text

from django.core.urlresolvers import reverse
import mysite.profile.views

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
    help = "Send out periodic emails to users who've requested a running summary of OpenHatch activity in their projects."

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

        YESTERDAY = datetime.timedelta(hours=24)

        # If it's been less than 24 hours since our last big email,
        # stop here and don't send any emails.
        if ((self.this_run_covers_things_up_until - self.this_run_covers_things_since) < 
                YESTERDAY):
            logging.warn("Not sending emails; emails were last sent within the last 24 hours.")
            return

        # If we made it this far in the function, it's been 24 hours or more
        # since our last email. Let's make a note that the time range of this
        # email extends until the timestamp stored in self.this_run_covers_things_up_until
        Timestamp.update_timestamp_for_string(Command.TIMESTAMP_KEY,
                override_time=self.this_run_covers_things_up_until)
        # ^^ This entry in the database will be used for calculating the time
        # range starting point of the next email

        # Now let's send some emails! :-)
        people_who_want_email = Person.objects.filter(email_me_re_projects=True)

        count = 0
        for person in people_who_want_email:

            if not person.user.email:
                logging.warn("Uh, the person has no email address: %s" % person.user.username)
                continue # if the user has no email address, we skip the user.

            message_in_plain_text, message_in_html = self.get_projects_email_for(person)
            if message_in_html: 
                count += 1
                print "Emailing %s their project activity." % person.user.email
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
        print "Emailed", count 

    def get_projects_email_for(self, recipient):
        context = self.get_context_for_email_to(recipient)
        if context is None:
            return None, None

        # Create two slightly different template contexts

        plain_context = context.copy()
        rich_context = context.copy()

        plain_context['rich_text'] = False
        rich_context['rich_text'] = True

        message_in_simpler_html = render_to_string('email_re_projects.html', plain_context)
        message_in_html = render_to_string('email_re_projects.html', rich_context)

        # when it is converted into Markdown it looks good in an email
        html2text.BODY_WIDTH = 0 # good for emails
        to_markdown = html2text.html2text
        try:
            message_in_plain_text = to_markdown(message_in_simpler_html)
        except HTMLParser.HTMLParseError:
            # Oh, snap. There is something terribly wrong.
            raise ValueError(("We failed to parse the HTML of the message, which means "
                              "that we could not create a text version. You might want "
                              "to look at the message:\n\n" +
                              message_in_simpler_html))

        return message_in_plain_text, message_in_html

    @staticmethod
    def get_maintainer_projects(person):
        return [pfe.project for pfe in person.get_maintainer_portfolio_entries()]

    def get_context_for_email_to(self, recipient):
        context = {}
        project2people = []

        within_range = Q(
                date_created__gt=  self.this_run_covers_things_since,
                date_created__lte=   self.this_run_covers_things_up_until)
        within_range_for_wh = Q(
                created_date__gt=  self.this_run_covers_things_since,
                created_date__lte=   self.this_run_covers_things_up_until)

        projects = Command.get_maintainer_projects(recipient)

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
            display_these_contributors.sort(key=lambda x: x.get_coolness_factor(
                'contributors_for_%s_in_%s' % (recipient.user.username, project.name)))
            display_these_wannahelpers.sort(key=lambda x: x.get_coolness_factor(
                'wannahelpers_for_%s_in_%s' % (recipient.user.username, project.name)))
            
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
            project2people.append((project, people_data))

        if not project2people:
            # If there's no news to report, signal this fact loudly to the caller
            return None

        context['recipient'] = recipient
        context['project2people'] = project2people
        token_string = recipient.generate_new_unsubscribe_token().string
        context['unsubscribe_link'] = "http://openhatch.org" + reverse(
                mysite.profile.views.unsubscribe, 
                kwargs={'token_string': token_string})
        return context 
