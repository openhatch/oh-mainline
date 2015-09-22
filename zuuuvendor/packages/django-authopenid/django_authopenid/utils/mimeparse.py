"""MIME-Type Parser

This module provides basic functions for handling mime-types. It can handle
matching mime-types against a list of media-ranges. See section 14.1 of 
the HTTP specification [RFC 2616] for a complete explaination.

   http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.1

Contents:
    - parse_mime_type():   Parses a mime-type into it's component parts.
    - parse_media_range(): Media-ranges are mime-types with wild-cards and a 
    'q' quality parameter.
    - quality():           Determines the quality ('q') of a mime-type when 
    compared against a list of media-ranges.
    - quality_parsed():    Just like quality() except the second parameter must
     be pre-parsed.
    - best_match():        Choose the mime-type with the highest quality ('q')
     from a list of candidates. 
"""

__version__ = "0.1.1"
__author__ = 'Joe Gregorio'
__email__ = "joe@bitworking.org"
__credits__ = ""

def parse_mime_type(mime_type):
    """Carves up a mime_type and returns a tuple of the
       (type, subtype, params) where 'params' is a dictionary
       of all the parameters for the media range.
       For example, the media range 'application/xhtml;q=0.5' would
       get parsed into:

       ('application', 'xhtml', {'q', '0.5'})
       """
    parts = mime_type.split(";")
    params = dict([tuple([s.strip() for s in param.split("=")])\
            for param in parts[1:] ])
    (type, subtype) = parts[0].split("/")
    return (type.strip(), subtype.strip(), params)

def parse_media_range(range):
    """Carves up a media range and returns a tuple of the
       (type, subtype, params) where 'params' is a dictionary
       of all the parameters for the media range.
       For example, the media range 'application/*;q=0.5' would
       get parsed into:

       ('application', '*', {'q', '0.5'})

       In addition this function also guarantees that there 
       is a value for 'q' in the params dictionary, filling it
       in with a proper default if necessary.
       """
    (type, subtype, params) = parse_mime_type(range)
    if not params.has_key('q') or not params['q'] or \
            not float(params['q']) or float(params['q']) > 1\
            or float(params['q']) < 0:
        params['q'] = '1'
    return (type, subtype, params)

def quality_parsed(mime_type, parsed_ranges):
    """Find the best match for a given mime_type against 
       a list of media_ranges that have already been 
       parsed by parse_media_range(). Returns the 
       'q' quality parameter of the best match, 0 if no
       match was found. This function bahaves the same as quality()
       except that 'parsed_ranges' must be a list of
       parsed media ranges. """
    best_fitness = -1 
    best_match = ""
    best_fit_q = 0
    (target_type, target_subtype, target_params) =\
            parse_media_range(mime_type)
    for (type, subtype, params) in parsed_ranges:
        param_matches = reduce(lambda x, y: x+y, [1 for (key, value) in \
                target_params.iteritems() if key != 'q' and \
                params.has_key(key) and value == params[key]], 0)
        if (type == target_type or type == '*' or target_type == '*') and \
                (subtype == target_subtype or subtype == '*' or target_subtype == '*'):
            fitness = (type == target_type) and 100 or 0
            fitness += (subtype == target_subtype) and 10 or 0
            fitness += param_matches
            if fitness > best_fitness:
                best_fitness = fitness
                best_fit_q = params['q']
            
    return float(best_fit_q)
    
def quality(mime_type, ranges):
    """Returns the quality 'q' of a mime_type when compared
    against the media-ranges in ranges. For example:

    >>> quality('text/html','text/*;q=0.3, text/html;q=0.7, text/html;level=1, '
    'text/html;level=2;q=0.4, */*;q=0.5')
    0.7
    
    """ 
    parsed_ranges = [parse_media_range(r) for r in ranges.split(",")]
    return quality_parsed(mime_type, parsed_ranges)

def best_match(supported, header):
    """Takes a list of supported mime-types and finds the best
    match for all the media-ranges listed in header. The value of
    header must be a string that conforms to the format of the 
    HTTP Accept: header. The value of 'supported' is a list of
    mime-types.
    
    >>> best_match(['application/xbel+xml', 'text/xml'], 'text/*;q=0.5,*/*; q=0.1')
    'text/xml'
    """
    parsed_header = [parse_media_range(r) for r in header.split(",")]
    weighted_matches = [(quality_parsed(mime_type, parsed_header), mime_type)\
            for mime_type in supported]
    weighted_matches.sort()
    return weighted_matches[-1][0] and weighted_matches[-1][1] or ''

if __name__ == "__main__":
    import unittest

    class TestMimeParsing(unittest.TestCase):

        def test_parse_media_range(self):
            self.assert_(('application', 'xml', {'q': '1'}) == parse_media_range('application/xml;q=1'))
            self.assertEqual(('application', 'xml', {'q': '1'}), parse_media_range('application/xml'))
            self.assertEqual(('application', 'xml', {'q': '1'}), parse_media_range('application/xml;q='))
            self.assertEqual(('application', 'xml', {'q': '1'}), parse_media_range('application/xml ; q='))
            self.assertEqual(('application', 'xml', {'q': '1', 'b': 'other'}), parse_media_range('application/xml ; q=1;b=other'))
            self.assertEqual(('application', 'xml', {'q': '1', 'b': 'other'}), parse_media_range('application/xml ; q=2;b=other'))

        def test_rfc_2616_example(self):
            accept = "text/*;q=0.3, text/html;q=0.7, text/html;level=1, text/html;level=2;q=0.4, */*;q=0.5"
            self.assertEqual(1, quality("text/html;level=1", accept))
            self.assertEqual(0.7, quality("text/html", accept))
            self.assertEqual(0.3, quality("text/plain", accept))
            self.assertEqual(0.5, quality("image/jpeg", accept))
            self.assertEqual(0.4, quality("text/html;level=2", accept))
            self.assertEqual(0.7, quality("text/html;level=3", accept))

        def test_best_match(self):
            mime_types_supported = ['application/xbel+xml', 'application/xml']
            # direct match
            self.assertEqual(best_match(mime_types_supported, 'application/xbel+xml'), 'application/xbel+xml')
            # direct match with a q parameter
            self.assertEqual(best_match(mime_types_supported, 'application/xbel+xml; q=1'), 'application/xbel+xml')
            # direct match of our second choice with a q parameter
            self.assertEqual(best_match(mime_types_supported, 'application/xml; q=1'), 'application/xml')
            # match using a subtype wildcard
            self.assertEqual(best_match(mime_types_supported, 'application/*; q=1'), 'application/xml')
            # match using a type wildcard
            self.assertEqual(best_match(mime_types_supported, '*/*'), 'application/xml')

            mime_types_supported = ['application/xbel+xml', 'text/xml']
            # match using a type versus a lower weighted subtype
            self.assertEqual(best_match(mime_types_supported, 'text/*;q=0.5,*/*; q=0.1'), 'text/xml')
            # fail to match anything
            self.assertEqual(best_match(mime_types_supported, 'text/html,application/atom+xml; q=0.9'), '')

        def test_support_wildcards(self):
            mime_types_supported = ['image/*', 'application/xml']
            # match using a type wildcard
            self.assertEqual(best_match(mime_types_supported, 'image/png'), 'image/*')
            # match using a wildcard for both requested and supported 
            self.assertEqual(best_match(mime_types_supported, 'image/*'), 'image/*')

    unittest.main() 