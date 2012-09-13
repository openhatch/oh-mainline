import os

from twisted.python.failure import Failure

class LogFormatter(object):
    """Class for generating log messages for different actions. All methods
    must return a plain string which doesn't include the log level or the
    timestamp
    """

    def crawled(self, request, response, spider):
        referer = request.headers.get('Referer')
        flags = ' %s' % str(response.flags) if response.flags else ''
        return u"Crawled (%d) %s (referer: %s)%s" % (response.status, \
            request, referer, flags)

    def scraped(self, item, response, spider):
        src = response.getErrorMessage() if isinstance(response, Failure) else response
        return u"Scraped from %s%s%s" % (src, os.linesep, item)

    def dropped(self, item, exception, response, spider):
        return u"Dropped: %s%s%s" % (exception, os.linesep, item)
