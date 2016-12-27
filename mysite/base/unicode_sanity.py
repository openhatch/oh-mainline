# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# I will not be afraid of Unicode.

# I do want to monkey-patch away Python stdlib functions
# that stress me out.

# Sadly our dependencies use them, so I can't.
import urllib
import cStringIO as StringIO

import decorator

@decorator.decorator
def unicodify_strings_when_inputted(func, *args, **kwargs):
    '''Decorator that makes sure every argument passed in that is
    a string-esque type is turned into a Unicode object. Does so
    by decoding UTF-8 byte strings into Unicode objects.'''
    args_as_list = list(args)
    # first, *args
    for i in range(len(args)):
        arg = args[i]
        if type(arg) is str:
            args_as_list[i] = unicode(arg, 'utf-8')

    # then, **kwargs
    for key in kwargs:
        arg = kwargs[key]
        if type(arg) is str:
            kwargs[key] = unicode(arg, 'utf-8')
    return func(*args_as_list, **kwargs)


@unicodify_strings_when_inputted
def quote(str):
    return urllib.quote(str.encode('utf-8'))


def wrap_file_object_in_utf8_check(f):
    # For now, this does the horrifying thing of reading in the whole file.
    # Better ways would be apprediated.
    bytes = f.read()
    if type(bytes) == unicode:
        as_unicode = bytes
    else:
        as_unicode = unicode(bytes, 'utf-8-sig')
    as_utf8 = as_unicode.encode('utf-8')
    return StringIO.StringIO(as_utf8)


def utf8(s):
    '''This function takes a bytestring or a Unicode object
    as its input, and it outputs a bytestring that is UTF-8
    encoded.

    If you pass an object with a __unicode__ method, like an
    integer, it will also convert that to a Unicode object.

    This is very similar to the smart_str method provided by
    Django with one particular difference: this function will
    raise a UnicodeDecodeError if you pass in a bytestring that
    cannot be decoded into UTF-8. This is a feature; in the case
    of invalid data, we refuse the temptation to guess.'''
    # If the input is a bytestring, then we use the unicode
    # constructor to up-convert it:
    try:
        pure = unicode(s, 'utf-8')
    except TypeError:
        # the Unicode constructor will raise a TypeError
        # if it received something other than a bytestring.
        #
        # In that case, just call unicode() directly on it.
        # For pure Unicode objects, this just gives us the
        # pure Unicode object back.
        pure = unicode(s)

    # Now, take that pure object and return a UTF-8-encoded
    # bytestring.
    return pure.encode('utf-8')
