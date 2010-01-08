from optparse import make_option
from django.core.management.base import NoArgsCommand, CommandError
import mysite.customs.cia

class Command(NoArgsCommand):
    def handle(self, **options):
         mysite.customs.cia.main()
