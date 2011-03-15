from django.core.management.base import BaseCommand 
from optparse import make_option
import mysite.base.views
import sys

class Command(BaseCommand):
    help = 'Returns the Nagios exit code for objects that are monitored'

    option_list = BaseCommand.option_list + (
       make_option('-m', '--meta', action='store_true',
           dest='meta', default=False, help='Check the meta data.'),
    )

    def handle(self, *args, **options):
        runmeta = options.get('meta')

        if runmeta:
            code = mysite.base.views.meta_exit_code()
            sys.exit(code)
