import atexit
import socket
import sys

from itertools import count
from time import time, sleep

from anyjson import serialize, deserialize
from carrot.backends.base import BaseBackend, BaseMessage
from carrot.utils import gen_unique_id

from ghettoq.backends import Connection
from ghettoq.messaging import Empty as QueueEmpty


try:
    from collections import OrderedDict
except ImportError:
    from odict import odict as OrderedDict


class QualityOfService(object):

    def __init__(self, backend, resource, prefetch_count=None,
            interval=None):
        self.backend = backend
        self.resource = resource
        self.prefetch_count = prefetch_count
        self.interval = interval
        self._delivered = OrderedDict()
        self._restored_once = False
        atexit.register(self.restore_unacked_once)

    def can_consume(self):
        return len(self._delivered) > self.prefetch_count

    def append(self, message, queue_name, delivery_tag):
        self._delivered[delivery_tag] = message, queue_name

    def ack(self, delivery_tag):
        self._delivered.pop(delivery_tag, None)

    def restore_unacked(self):
        for delivery_tag, delivered in self._delivered.items():
            message, queue_name = delivered
            send = self.backend.prepare_message(message.body, 2, 10,
                                                message.content_type,
                                                message.content_encoding)
            send["destination"] = queue_name
            self.resource.put(queue_name, serialize(send))
        self._delivered = OrderedDict()

    def requeue(self, delivery_tag):
        try:
            message, queue_name = self._delivered.pop(delivery_tag)
        except KeyError:
            pass
        self.resource.put(queue_name, message)

    def restore_unacked_once(self):
        if not self._restored_once:
            if self._delivered:
                sys.stderr.write(
                    "Restoring unacknowledged messages: %s\n" % (
                        self._delivered))
            self.restore_unacked()
            if self._delivered:
                sys.stderr.write("UNRESTORED MESSAGES: %s\n" % (
                    self._delivered))


class Message(BaseMessage):

    def __init__(self, backend, payload, **kwargs):
        self.backend = backend

        payload = deserialize(payload)
        kwargs["body"] = payload.get("body").encode("utf-8")
        kwargs["delivery_tag"] = payload.get("delivery_tag")
        kwargs["content_type"] = payload.get("content-type")
        kwargs["content_encoding"] = payload.get("content-encoding")
        kwargs["priority"] = payload.get("priority")
        self.destination = payload.get("destination")

        super(Message, self).__init__(backend, **kwargs)

    def reject(self):
        raise NotImplementedError(
            "The GhettoQ backend does not implement basic.reject")


class MultiBackend(BaseBackend):
    Message = Message
    default_port = None
    type = None
    interval = 1
    polling = True
    _prefetch_count = None
    _consumers = {}
    _callbacks = {}

    def __init__(self, connection, **kwargs):
        if not self.type:
            raise NotImplementedError(
                        "MultiBackends must have the type attribute")
        self.connection = connection
        self._channel = None
        self._qos_manager = None

    def establish_connection(self):
        conninfo = self.connection
        conn = Connection(self.type, host=conninfo.hostname,
                                     user=conninfo.userid,
                                     password=conninfo.password,
                                     database=conninfo.virtual_host,
                                     port=conninfo.port)
        conn.drain_events = self.drain_events
        return conn

    def close_connection(self, connection):
        connection.close()

    def queue_exists(self, queue):
        return True

    def queue_purge(self, queue, **kwargs):
        return self.channel.Queue(queue).purge()

    def _poll(self, resource, timeout=None):
        time_elapsed = 0.0
        while True:
            time_start = time()
            if self.qos_manager.can_consume():
                try:
                    return resource.get()
                except QueueEmpty:
                    pass
            time_elapsed += (time() - time_start)
            if timeout and time_elapsed >= timeout:
                raise socket.timeout("Operation timed out.")
            if self.polling:
                sleep(self.interval)
                time_elapsed += self.interval

    def declare_consumer(self, queue, no_ack, callback, consumer_tag,
                         **kwargs):
        self._consumers[consumer_tag] = queue
        self._callbacks[queue] = callback

    def drain_events(self, timeout=None):
        queueset = self.channel.QueueSet(self._consumers.values())
        payload, queue = self._poll(queueset, timeout=timeout)

        if not queue or queue not in self._callbacks:
            return

        self._callbacks[queue](payload)

    def consume(self, limit=None):
        for total_message_count in count():
            if limit and total_message_count >= limit:
                raise StopIteration

            self.drain_events()

            yield True

    def queue_declare(self, queue, *args, **kwargs):
        pass

    def get(self, queue, **kwargs):
        try:
            payload = self.channel.Queue(queue).get()
        except QueueEmpty:
            return None
        else:
            return self.message_to_python(payload)

    def ack(self, delivery_tag):
        self.qos_manager.ack(delivery_tag)

    def requeue(self, delivery_tag):
        self.qos_manager.requeue(delivery_tag)

    def message_to_python(self, raw_message):
        message = self.Message(backend=self, payload=raw_message)
        self.qos_manager.append(message, message.destination,
                                message.delivery_tag)
        return message

    def prepare_message(self, message_data, delivery_mode, priority=0,
            content_type=None, content_encoding=None):
        return {"body": message_data,
                "delivery_tag": gen_unique_id(),
                "priority": priority or 0,
                "content-encoding": content_encoding,
                "content-type": content_type}

    def publish(self, message, exchange, routing_key, **kwargs):
        message["destination"] = exchange
        self.channel.Queue(exchange).put(serialize(message),
                                         priority=message["priority"])

    def cancel(self, consumer_tag):
        if not self._channel:
            return
        queue = self._consumers.pop(consumer_tag, None)
        self._callbacks.pop(queue, None)

    def close(self):
        for consumer_tag in self._consumers.keys():
            self.cancel(consumer_tag)
        if self._channel:
            self._channel.close()
        self._channel = None

    def basic_qos(self, prefetch_size, prefetch_count, apply_global=False):
        self._prefetch_count = prefetch_count

    @property
    def channel(self):
        if not self._channel:
            # Need one connection per channel.
            # AMQP has multiplexing, but Redis does not.
            self._channel = self.establish_connection()
        return self._channel

    @property
    def qos_manager(self):
        if self._qos_manager is None:
            self._qos_manager = QualityOfService(self, self.channel)

        # Update prefetch count / interval
        self._qos_manager.prefetch_count = self._prefetch_count
        self._qos_manager.interval = self.interval

        return self._qos_manager


class Redis(MultiBackend):
    type = "Redis"
    polling = False


class Database(MultiBackend):
    type = "database"


class MongoDB(MultiBackend):
    type = "mongodb"


class Beanstalk(MultiBackend):
    type = "Beanstalk"
    polling = False


class CouchDB(MultiBackend):
    type = "couchdb"
