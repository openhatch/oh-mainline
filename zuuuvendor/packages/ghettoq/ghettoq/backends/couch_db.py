from Queue import Empty

import couchdb
import uuid
from ghettoq.backends.base import BaseBackend

__author__ = "David Clymer <david@zettazebra.com>"

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5984
DEFAULT_DATABASE = 'ghettoq'

def create_message_view(db):
    from couchdb import design
    view = design.ViewDefinition('ghettoq', 'messages', """
        function (doc) {
          if (doc.queue && doc.payload)
            emit(doc.queue, doc);
        }
        """)
    if not view.get_doc(db):
        view.sync(db)

class CouchdbBackend(BaseBackend):

    def __init__(self, host=None, port=None, user=None, password=None,
                 database=None, timeout=None, ssl=False):

        self.ssl = ssl
        if not database or database == '/':
            database = DEFAULT_DATABASE
        self.view_created = False
        super(CouchdbBackend, self).__init__(host or DEFAULT_HOST,
                                             port or DEFAULT_PORT,
                                             user, password,
                                             database or DEFAULT_DATABASE,
                                             timeout)

    def establish_connection(self):
        if self.ssl:
            proto = 'https'
        else:
            proto = 'http'

        server = couchdb.Server('%s://%s:%s/' % (proto, self.host, self.port))
        try:
            return server.create(self.database)
        except couchdb.PreconditionFailed:
            return server[self.database]

    def put(self, queue, message, **kwargs):
        self.client.save({'_id': uuid.uuid4().hex, 'queue': queue, 'payload': message})

    def _get(self, queue, **kwargs):
        # If the message view is not yet set up, we'll need it now.
        if not self.view_created:
            create_message_view(self.client)
            self.view_created = True

        if not queue:
            raise Empty
        return self.client.view('ghettoq/messages', key=queue, **kwargs)

    def get(self, queue):
        result = self._get(queue, limit=1)
        if not result:
            raise Empty

        item = result.rows[0].value
        self.client.delete(item)
        return item['payload']

    def purge(self, queue):
        result = self._get(queue)
        for item in result:
            self.client.delete(item.value)
        return len(result)
