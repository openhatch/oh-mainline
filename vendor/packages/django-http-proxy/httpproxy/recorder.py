# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.http import HttpResponse
try:
    from hashlib import md5 as md5_constructor
except ImportError:
    from django.utils.hashcompat import md5_constructor

from httpproxy.exceptions import RequestNotRecorded, ResponseUnsupported
from httpproxy.models import Request, Response


logger = logging.getLogger(__name__)

class ProxyRecorder(object):
    """
    Facilitates recording and playback of Django HTTP requests and responses.
    """

    response_types_supported = (
        'application/javascript',
        'application/xml',
        'text/css',
        'text/html',
        'text/javascript',
        'text/plain',
        'text/xml',
    )

    def __init__(self, domain, port):
        super(ProxyRecorder, self).__init__()
        self.domain, self.port = domain, port

    def record(self, request, response):
        """
        Attempts to record the request and the corresponding response.

        .. note::
            The recording functionality of the Django HTTP Proxy is currently
            limited to plain text content types. The default behavior is to
            *ignore* any unsupported content types when
            :attr:`httpproxy.views.HttpProxy.mode` is set to ``record`` –
            responses with unsupported content types are not recorded and will
            be ignored silently. To prevent this, put this in your Django
            settings module::

                PROXY_IGNORE_UNSUPPORTED = False

            Doing so will raise a
            :class:`~httpproxy.exceptions.ResponseUnsupported` exception if any
            unsupported response type is encountered in "record" mode.
        """
        if self.response_supported(response):
            recorded_request = self.record_request(request)
            self.record_response(recorded_request, response)
        elif not getattr(settings, 'PROXY_IGNORE_UNSUPPORTED', True):
            raise ResponseUnsupported('Response of type "%s" could not be recorded.' % response['Content-Type'])

    def record_request(self, request):
        """
        Saves the provided :class:`~httpproxy.models.Request`, including its
        :class:`~httpproxy.models.RequestParameter` objects.
        """
        logger.info('Recording: GET "%s"' % self._request_string(request))

        recorded_request, created = Request.objects.get_or_create(
                method=request.method, domain=self.domain, port=self.port,
                path=request.path, querykey=self._get_query_key(request))

        self.record_request_parameters(request, recorded_request)

        # Update the timestamp on the existing recorded request
        if not created:
            recorded_request.save()

        return recorded_request

    def record_request_parameters(self, request, recorded_request):
        """
        Records the :class:`~httpproxy.models.RequestParameter` objects for the
        recorded :class:`~httpproxy.models.Request`.

        The order field is set to reflect the order in which the QueryDict
        returns the GET parameters.
        """
        recorded_request.parameters.get_query_set().delete()
        position = 1
        for name, values_list in request.GET.lists():
            for value in values_list:
                recorded_request.parameters.create(order=position, name=name,
                        value=value)
                position += 1

    def record_response(self, recorded_request, response):
        """
        Records a :class:`~httpproxy.models.Response` so it can be replayed at a
        later stage.

        The recorded response is linked to a previously recorded
        :class:`~httpproxy.models.Request` and its request parameters to allow
        for reverse-finding the recorded response given the recorded request
        object.
        """
        # Delete the previously recorded response, if any
        try:
            recorded_request.response.delete()
        except Response.DoesNotExist:
            pass

        # Extract the encoding from the response
        content_type = response['Content-Type']
        encoding = content_type.partition('charset=')[-1] or 'utf-8'

        # Record the new response
        Response.objects.create(request=recorded_request,
                status=response.status_code, content_type=content_type,
                content=response.content.decode(encoding))

    def playback(self, request):
        """
        Returns a previously recorded response based on the provided request.
        """
        try:
            matching_request = Request.objects.filter(method=request.method,
                    domain=self.domain, port=self.port, path=request.path,
                    querykey=self._get_query_key(request)).latest()
        except Request.DoesNotExist:
            raise RequestNotRecorded('The request made has not been ' \
                    'recorded yet. Please run httpproxy in "record" mode ' \
                    'first.')

        logger.info('Playback: GET "%s"' % self._request_string(request))
        response = matching_request.response # TODO handle "no response" situation
        encoding = self._get_encoding(response.content_type)

        return HttpResponse(response.content.encode(encoding),
                status=response.status, content_type=response.content_type)

    def response_supported(self, response):
        return response['Content-Type'].partition(';')[0] \
                in self.response_types_supported

    def _get_encoding(self, content_type):
        """
        Extracts the character encoding from an HTTP Content-Type header.
        """
        return content_type.partition('charset=')[-1] or 'utf-8'

    def _request_string(self, request):
        """
        Helper for getting a string representation of a request.
        """
        return '%(domain)s:%(port)d%(path)s' % {
            'domain': self.domain,
            'port': self.port,
            'path': request.get_full_path()
        }

    def _get_query_key(self, request):
        """
        Returns an MD5 has of the request's query parameters.
        """
        querystring = request.GET.urlencode()
        return md5_constructor(querystring).hexdigest()
