from ghettoq.models import Queue
from ghettoq.backends.base import BaseBackend


class DatabaseBackend(BaseBackend):

    def __init__(self, *args, **kwargs):
        from django.conf import settings
        if not settings.configured:
            settings.configure(DEBUG=False,
                               DATABASE_HOST=self.host,
                               DATABASE_PORT=self.port,
                               DATABASE_NAME=self.database,
                               DATABASE_USER=self.user,
                               DATABASE_PASSWORD=self.password)
        super(DatabaseBackend, self).__init__(*args, **kwargs)

    def establish_connection(self):
        pass

    def put(self, queue, message, **kwargs):
        Queue.objects.publish(queue, message)

    def get(self, queue):
        self.refresh_connection()
        return Queue.objects.fetch(queue)

    def purge(self, queue):
        return Queue.objects.purge(queue)

    def refresh_connection(self):
        from django.db import connection
        connection.close()
