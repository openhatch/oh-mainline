"""
Some generic exceptions that can occur in Django HTTP Proxy.
"""
from django.http import Http404


class ResponseUnsupported(Exception):
    """
    Raised by :meth:`httpproxy.recorder.ProxyRecorder.record` when it cannot
    a response (e.g. because it has an unsupported content type).
    """
    pass


class RequestNotRecorded(Http404):
    """
    Raised by :meth:`httpproxy.recorder.ProxyRecorder.playback` when a request
    is made for a URL that has not previously recorded yet.
    """
    pass
