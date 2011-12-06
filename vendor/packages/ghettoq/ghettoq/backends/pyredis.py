from Queue import Empty

from redis import Redis
from ghettoq.backends.base import BaseBackend

DEFAULT_PORT = 6379
DEFAULT_DB = 0


class RedisBackend(BaseBackend):

    def __init__(self, host=None, port=None, user=None, password=None,
            database=None, timeout=None):

        if not isinstance(database, int):
            if not database or database == "/":
                database = DEFAULT_DB
            elif database.startswith('/'):
                database = database[1:]
            try:
                database = int(database)
            except ValueError:
                raise AttributeError(
                    "Database name must be integer between 0 "
                    "and database_count - 1")

        super(RedisBackend, self).__init__(host, port, user, password,
                                           database, timeout)

    def establish_connection(self):
        self.port = int(self.port) or DEFAULT_PORT
        return Redis(host=self.host, port=self.port, db=self.database,
                     password=self.password)

    def put(self, queue, message, **kwargs):
        self.client.lpush(queue, message)

    def get(self, queue):
        if not queue:
            raise Empty

        try:
            dest, item = self.client.brpop([queue], timeout=1)
        except TypeError:
            raise Empty

        return item

    def get_many(self, queues, timeout=None):
        if not queues:
            raise Empty

        try:
            dest, item = self.client.brpop(queues, timeout=1)
        except TypeError:
            raise Empty

        return item, dest

    def purge(self, queue):
        size = self.client.llen(queue)
        self.client.delete(queue)
        return size
