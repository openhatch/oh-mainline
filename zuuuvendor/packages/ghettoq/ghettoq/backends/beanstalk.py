from itertools import ifilter
from Queue import Empty

from beanstalkc import Connection
from ghettoq.backends.base import BaseBackend

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 11300


class BeanstalkBackend(BaseBackend):

    def _parse_job(self, job):
        item, dest = None, None
        if job:
            try:
                item = job.body
                dest = job.stats()['tube']
            except:
                job.bury()
            else:
                job.delete()
        else:
            raise Empty
        return item, dest

    def establish_connection(self):
        self.host = self.host or DEFAULT_HOST
        self.port = self.port or DEFAULT_PORT
        return Connection(host=self.host, port=self.port)

    def put(self, queue, message, priority=0, **kwargs):
        self.client.use(queue)
        self.client.put(message, priority=priority)

    def get(self, queue):
        if not queue:
            raise Empty
        if queue not in self.client.watching():
            self.client.watch(queue)

        ignore = ifilter(lambda q: q!= queue, self.client.watching())
        map(self.client.ignore, ignore)

        job = self.client.reserve(timeout=1)
        item, dest = self._parse_job(job)
        return item

    def get_many(self, queues, timeout=None):
        if not queues:
            raise Empty

        # timeout of None will cause beanstalk to timeout waiting
        # for a new request
        if timeout is None:
            timeout = 1

        to_watch = ifilter(lambda q: q not in self.client.watching(), queues)
        map(self.client.watch, to_watch)

        job = self.client.reserve(timeout=timeout)
        return self._parse_job(job)

    def purge(self, queue):
        if queue not in self.client.watching(): 
            self.client.watch(queue) 
            ignore = ifilter(lambda q: q!= queue, self.client.watching()) 
            map(self.client.ignore, ignore) 
            count = 0 
            while True: 
                job = self.client.reserve(timeout=1) 
                if job: 
                    job.delete() 
                    count += 1
                else: 
                    break 
            return count 
