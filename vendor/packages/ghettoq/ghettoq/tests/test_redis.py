import unittest

from anyjson import serialize, deserialize

from ghettoq.simple import Connection, Empty


def create_connection(database):
    return Connection("redis", host="localhost", database=database)


class TestRedisBackend(unittest.TestCase):

    def test_default_database_is_set_correctly(self):
        conn1 = create_connection("")
        conn2 = create_connection("/")
        conn3 = create_connection("")
        conn4 = create_connection(None)

        self.assertEquals(conn1.database, 0)
        self.assertEquals(conn2.database, 0)
        self.assertEquals(conn3.database, 0)
        self.assertEquals(conn4.database, 0)

    def test_database_name_is_set_correctly(self):
        conn1 = create_connection("1")
        conn2 = create_connection("/2")
        conn3 = create_connection(3)

        self.assertEquals(conn1.database, 1)
        self.assertEquals(conn2.database, 2)
        self.assertEquals(conn3.database, 3)

    def test_invalid_database_name_raises_AttributeError(self):
        self.assertRaises(AttributeError, create_connection, "string")
        self.assertRaises(AttributeError, create_connection, "1string")
        self.assertRaises(AttributeError, create_connection, "/string")

    def test_empty_raises_Empty(self):
        conn = create_connection(1)
        q = conn.Queue("testing")

        self.assertRaises(Empty, q.get)

    def test_queue_is_empty_after_purge(self):
        conn = create_connection(1)
        q = conn.Queue("test_queue")
        q.put(serialize({"name": "George Constanza"}))
        q.put(serialize({"name": "George Constanza"}))
        q.purge()

        self.assertRaises(Empty, q.get)

    def test_put__get(self):
        conn = create_connection(1)
        q = conn.Queue("testing")
        q.put(serialize({"name": "George Constanza"}))

        self.assertEquals(deserialize(q.get()),
                {"name": "George Constanza"})

    def test_empty_queueset_raises_Empty(self):
        conn = create_connection(1)
        a, b, c, = conn.Queue("a"), conn.Queue("b"), conn.Queue("c")
        queueset = conn.QueueSet(queue.name for queue in (a, b, c))
        for queue in a, b, c:
            self.assertRaises(Empty, queue.get)
        self.assertRaises(Empty, queueset.get)
