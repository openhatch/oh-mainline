from django.core.management.base import BaseCommand
import mysite.customs.ping_twisted

class Command(BaseCommand):
    help = "Call this when you want to know the path to the Twisted ping directory."

    def handle(self, *args, **options):
        print mysite.customs.ping_twisted.directory()
