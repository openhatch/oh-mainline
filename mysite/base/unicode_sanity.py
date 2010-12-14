### I will not be afraid of Unicode.

### I do want to monkey-patch away Python stdlib functions
### that stress me out.

### Sadly our dependencies use them, so I can't.
import urllib
import cStringIO as StringIO

import mysite.base.decorators

_urlencode = urllib.urlencode

def urlencode(unicode_dict):
    utf8_dict = {}
    bad_keys = []
    bad_values = []
    for key in unicode_dict:
        value = unicode_dict[key]
        if type(key) == str:
            bad_keys.append(key)
        if type(value) == str:
            bad_values.append(value)
        utf8_dict[unicode(key).encode('utf-8')] = unicode(value).encode('utf-8')
    if bad_keys or bad_values:
        raise ProgrammingError
        #import pdb
        #pdb.set_trace()
    return _urlencode(utf8_dict)
    
@mysite.base.decorators.unicodify_strings_when_inputted
def quote(str):
    return urllib.quote(str.encode('utf-8'))

def wrap_file_object_in_utf8_check(f):
    ### For now, this does the horrifying thing of reading in the whole file.
    ### Better ways would be apprediated.
    bytes = f.read()
    as_unicode = unicode(bytes, 'utf-8-sig')
    as_utf8 = as_unicode.encode('utf-8')
    return StringIO.StringIO(as_utf8)
