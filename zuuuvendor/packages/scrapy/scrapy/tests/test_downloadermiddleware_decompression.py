from unittest import TestCase, main
from scrapy.http import Response, XmlResponse, Request
from scrapy.contrib_exp.downloadermiddleware.decompression import DecompressionMiddleware
from scrapy.spider import BaseSpider
from scrapy.tests import get_testdata


def _test_data(formats):
    uncompressed_body = get_testdata('compressed', 'feed-sample1.xml')
    test_responses = {}
    for format in formats:
        body = get_testdata('compressed', 'feed-sample1.' + format)
        test_responses[format] = Response('http://foo.com/bar', body=body)
    return uncompressed_body, test_responses


class DecompressionMiddlewareTest(TestCase):
    
    test_formats = ['tar', 'xml.bz2', 'xml.gz', 'zip']
    uncompressed_body, test_responses = _test_data(test_formats)

    def setUp(self):
        self.mw = DecompressionMiddleware()
        self.spider = BaseSpider('foo')

    def test_known_compression_formats(self):
        for fmt in self.test_formats:
            rsp = self.test_responses[fmt]
            new = self.mw.process_response(None, rsp, self.spider)
            assert isinstance(new, XmlResponse), \
                    'Failed %s, response type %s' % (fmt, type(new).__name__)
            self.assertEqual(new.body, self.uncompressed_body, fmt)

    def test_plain_response(self):
        rsp = Response(url='http://test.com', body=self.uncompressed_body)
        new = self.mw.process_response(None, rsp, self.spider)
        assert new is rsp
        self.assertEqual(new.body, rsp.body)

    def test_empty_response(self):
        rsp = Response(url='http://test.com', body='')
        new = self.mw.process_response(None, rsp, self.spider)
        assert new is rsp
        assert not rsp.body
        assert not new.body

    def tearDown(self):
        del self.mw


if __name__ == '__main__':
    main()
