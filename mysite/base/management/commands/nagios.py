from django.core.management.base import BaseCommand
from mysite.base.models import Timestamp
from optparse import make_option
import datetime
import mysite.base.views
import sys


class Command(BaseCommand):
    help = 'Returns the Nagios exit code for objects that are monitored'

    option_list = BaseCommand.option_list + (
        make_option('-m', '--meta', action='store_true',
                    dest='meta', default=False, help='Check the meta data.'),

        make_option('-w', '--weekly', action='store_true',
                    dest='weekly', default=False,
                    help='Check whether last email was sent more than 7 days ago.'),
    )

    def handle(self, *args, **options):
        runmeta = options.get('meta')
        runweekly = options.get('weekly')

        if runmeta:
            code = mysite.base.views.meta_exit_code()
            sys.exit(code)

        if runweekly:
            code = self.send_weekly_exit_code()
            sys.exit(code)

    @staticmethod
    def send_weekly_exit_code(covers_things_since=None):
        if covers_things_since is None:
            covers_things_since = Timestamp.get_timestamp_for_string(
                "What's the endpoint of the time range of the last email we sent out?")

        covers_things_until = datetime.datetime.utcnow()

        EIGHT_DAYS = datetime.timedelta(days=8)

        if ((covers_things_until - EIGHT_DAYS) < covers_things_since):
            print "OK - Last email sent less than 8 days ago"
            return 0
        else:
            print "CRITICAL - Last email sent more than 8 days ago"
            return 2
