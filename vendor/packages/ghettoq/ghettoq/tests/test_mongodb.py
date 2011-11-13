import unittest

from anyjson import serialize, deserialize

from ghettoq.simple import Connection, Empty


def create_connection(database):
    return Connection("mongodb", host="localhost", database=database)


class TestMongoDbBackend(unittest.TestCase):

    def test_empty_raises_Empty(self):
        conn = create_connection("database")
        q = conn.Queue("testing")

        self.assertRaises(Empty, q.get)

    def test_queue_is_empty_after_purge(self):
        conn = create_connection("database")
        q = conn.Queue("test_queue")
        q.put(serialize({"name": "George Constanza"}))
        q.put(serialize({"name": "George Constanza"}))
        q.purge()

        self.assertRaises(Empty, q.get)

    def test_put_and_get(self):
        conn = create_connection("database")
        q = conn.Queue("testing")
        q.put(serialize({"name": "George Constanza"}))

        self.assertEquals(deserialize(q.get()),
                {"name": "George Constanza"})

    def test_empty_queset_raises_Empty(self):
        conn = create_connection("database")
        a, b, c, = conn.Queue("a"), conn.Queue("b"), conn.Queue("c")
        queueset = conn.QueueSet(queue.name for queue in (a, b, c))
        for queue in a, b, c:
            self.assertRaises(Empty, queue.get)
        self.assertRaises(Empty, queueset.get)
