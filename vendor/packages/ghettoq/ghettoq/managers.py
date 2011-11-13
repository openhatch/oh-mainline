# Partially stolen from Django Queue Service
# (http://code.google.com/p/django-queue-service)
from django.db import models


class QueueManager(models.Manager):

    def publish(self, queue_name, payload):
        queue, created = self.get_or_create(name=queue_name)
        queue.messages.create(payload=payload)

    def fetch(self, queue_name):
        try:
            queue = self.get(name=queue_name)
        except self.model.DoesNotExist:
            return

        return queue.messages.pop()

    def purge(self, queue_name):
        try:
            queue = self.get(name=queue_name)
        except self.model.DoesNotExist:
            return

        messages = queue.messages.all()
        count = messages.count()
        messages.delete()
        return count


class MessageManager(models.Manager):

    def pop(self):
        try:
            resultset = self.filter(visible=True).order_by('sent_at', 'id')
            result = resultset[0:1].get()
            result.visible = False
            result.save()
            return result.payload
        except self.model.DoesNotExist:
            pass

    def cleanup(self):
        self.filter(visible=False).delete()
