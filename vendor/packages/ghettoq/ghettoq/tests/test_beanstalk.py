import unittest

from anyjson import serialize, deserialize

from ghettoq.simple import Connection, Empty


def create_connection():
    return Connection("beanstalk", host="localhost")


class TestBeanstalkBackend(unittest.TestCase):

    def test_empty_raises_Empty(self):
        conn = create_connection()
        q = conn.Queue("testing")

        self.assertRaises(Empty, q.get)

    def test_put__get(self):
        conn = create_connection()
        q = conn.Queue("testing")
        q.put(serialize({"name": "George Constanza"}))

        self.assertEquals(deserialize(q.get()),
                {"name": "George Constanza"})

    def test_empty_queueset_raises_Empty(self):
        conn = create_connection()
        a, b, c, = conn.Queue("a"), conn.Queue("b"), conn.Queue("c")
        queueset = conn.QueueSet(queue.name for queue in (a, b, c))
        for queue in a, b, c:
            self.assertRaises(Empty, queue.get)
        self.assertRaises(Empty, queueset.get)
