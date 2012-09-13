"""
This module implements the HtmlResponse class which adds encoding
discovering through HTML encoding declarations to the TextResponse class.

See documentation in docs/topics/request-response.rst
"""

import re

from scrapy.http.response.text import TextResponse
from scrapy.utils.python import memoizemethod_noargs

class HtmlResponse(TextResponse):

    _template = r'''%s\s*=\s*["']?\s*%s\s*["']?'''

    _httpequiv_re = _template % ('http-equiv', 'Content-Type')
    _content_re   = _template % ('content', r'(?P<mime>[^;]+);\s*charset=(?P<charset>[\w-]+)')
    _content2_re   = _template % ('charset', r'(?P<charset>[\w-]+)')

    METATAG_RE  = re.compile(r'<meta(?:\s+(?:%s|%s)){2}' % (_httpequiv_re, _content_re), re.I)
    METATAG2_RE  = re.compile(r'<meta\s+%s' % _content2_re, re.I)

    @memoizemethod_noargs
    def _body_declared_encoding(self):
        chunk = self.body[:5000]
        match = self.METATAG_RE.search(chunk) or self.METATAG2_RE.search(chunk)
        return match.group('charset') if match else None


