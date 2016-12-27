from pymongo.connection import Connection
from pymongo.errors import OperationFailure

from ghettoq.backends.base import BaseBackend
from ghettoq.messaging import Empty

__author__ = "Flavio [FlaPer87] Percoco Premoli <flaper87@flaper87.org>"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 27017


class MongodbBackend(BaseBackend):

    def establish_connection(self):
        self.port = self.port or DEFAULT_PORT
        self.host = self.host or DEFAULT_HOST
        self.connection = Connection(host=self.host, port=self.port)
        dbname = self.database
        if not dbname or dbname == "/":
            dbname = "ghettoq"
        self.database = getattr(self.connection, dbname)
        col = self.database.messages
        col.ensure_index([("queue", 1)])
        return col

    def put(self, queue, message, **kwargs):
        self.client.insert({"payload": message, "queue": queue})

    def get(self, queue):
        try:
            msg = self.client.database.command("findandmodify",
                        "messages", query={"queue": queue}, remove=True)
        except OperationFailure:
            raise Empty("Empty queue")
        return msg["value"]["payload"]

    def purge(self, queue):
        return self.client.remove({"queue": queue})
