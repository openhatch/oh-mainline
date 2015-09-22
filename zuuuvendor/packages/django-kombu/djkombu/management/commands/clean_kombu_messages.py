from django.core.management.base import BaseCommand


class Command(BaseCommand):
    requires_model_validation = True

    def handle(self, *args, **options):
        from djkombu.models import Message

        print("Removing %s invisible messages... " % (
            Message.objects.filter(visible=False).count(), ))
        Message.objects.cleanup()



