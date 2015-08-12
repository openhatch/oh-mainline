# coding: utf8

# Copyright 2007 Matt Chaput. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY MATT CHAPUT ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL MATT CHAPUT OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Matt Chaput.

"""Classes and functions for turning a piece of text into an indexable stream
of "tokens" (usually equivalent to words). There are three general types of
classes/functions involved in analysis:

* Tokenizers are always at the start of the text processing pipeline. They take
  a string and yield Token objects (actually, the same token object over and
  over, for performance reasons) corresponding to the tokens (words) in the
  text.
      
  Every tokenizer is a callable that takes a string and returns an iterator of
  tokens.

* Filters take the tokens from the tokenizer and perform various
  transformations on them. For example, the LowercaseFilter converts all tokens
  to lowercase, which is usually necessary when indexing regular English text.
      
  Every filter is a callable that takes a token generator and returns a token
  generator.

* Analyzers are convenience functions/classes that "package up" a tokenizer and
  zero or more filters into a single unit. For example, the StandardAnalyzer
  combines a RegexTokenizer, LowercaseFilter, and StopFilter.
    
  Every analyzer is a callable that takes a string and returns a token
  iterator. (So Tokenizers can be used as Analyzers if you don't need any
  filtering).

You can compose tokenizers and filters together using the ``|`` character::

    my_analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()

The first item must be a tokenizer and the rest must be filters (you can't put
a filter first or a tokenizer after the first item).
"""

import re
from collections import deque
from itertools import chain

from whoosh.compat import (callable, iteritems, string_type, text_type, u,
                           xrange, next)
from whoosh.lang.dmetaphone import double_metaphone
from whoosh.lang.porter import stem
from whoosh.util import lru_cache, unbound_cache, rcompile


# Default list of stop words (words so common it's usually wasteful to index
# them). This list is used by the StopFilter class, which allows you to supply
# an optional list to override this one.

STOP_WORDS = frozenset(('a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can',
                        'for', 'from', 'have', 'if', 'in', 'is', 'it', 'may',
                        'not', 'of', 'on', 'or', 'tbd', 'that', 'the', 'this',
                        'to', 'us', 'we', 'when', 'will', 'with', 'yet',
                        'you', 'your'))


# Pre-configured regular expressions

default_pattern = rcompile(r"\w+(\.?\w+)*")
url_pattern = rcompile("""
(
    [A-Za-z+]+://          # URL protocol
    \\S+?                  # URL body
    (?=\\s|[.]\\s|$|[.]$)  # Stop at space/end, or a dot followed by space/end
) | (                      # or...
    \w+([:.]?\w+)*         # word characters, with opt. internal colons/dots
)
""", verbose=True)


# Utility functions

def unstopped(tokenstream):
    """Removes tokens from a token stream where token.stopped = True.
    """
    return (t for t in tokenstream if not t.stopped)


def entoken(textstream, positions=False, chars=False, start_pos=0,
            start_char=0, **kwargs):
    """Takes a sequence of unicode strings and yields a series of Token objects
    (actually the same Token object over and over, for performance reasons),
    with the attributes filled in with reasonable values (for example, if
    ``positions`` or ``chars`` is True, the function assumes each token was
    separated by one space).
    """

    pos = start_pos
    char = start_char
    t = Token(positions=positions, chars=chars, **kwargs)

    for text in textstream:
        t.text = text

        if positions:
            t.pos = pos
            pos += 1

        if chars:
            t.startchar = char
            char = char + len(text)
            t.endchar = char

        yield t


# Token object

class Token(object):
    """
    Represents a "token" (usually a word) extracted from the source text being
    indexed.
    
    See "Advanced analysis" in the user guide for more information.
    
    Because object instantiation in Python is slow, tokenizers should create
    ONE SINGLE Token object and YIELD IT OVER AND OVER, changing the attributes
    each time.
    
    This trick means that consumers of tokens (i.e. filters) must never try to
    hold onto the token object between loop iterations, or convert the token
    generator into a list. Instead, save the attributes between iterations,
    not the object::
    
        def RemoveDuplicatesFilter(self, stream):
            # Removes duplicate words.
            lasttext = None
            for token in stream:
                # Only yield the token if its text doesn't
                # match the previous token.
                if lasttext != token.text:
                    yield token
                lasttext = token.text

    ...or, call token.copy() to get a copy of the token object.
    """

    def __init__(self, positions=False, chars=False, removestops=True, mode='',
                 **kwargs):
        """
        :param positions: Whether tokens should have the token position in the
            'pos' attribute.
        :param chars: Whether tokens should have character offsets in the
            'startchar' and 'endchar' attributes.
        :param removestops: whether to remove stop words from the stream (if
            the tokens pass through a stop filter).
        :param mode: contains a string describing the purpose for which the
            analyzer is being called, i.e. 'index' or 'query'.
        """

        self.positions = positions
        self.chars = chars
        self.stopped = False
        self.boost = 1.0
        self.removestops = removestops
        self.mode = mode
        self.__dict__.update(kwargs)

    def __repr__(self):
        parms = ", ".join("%s=%r" % (name, value)
                          for name, value in iteritems(self.__dict__))
        return "%s(%s)" % (self.__class__.__name__, parms)

    def copy(self):
        # This is faster than using the copy module
        return Token(**self.__dict__)


# Composition support

class Composable(object):
    is_morph = False

    def __or__(self, other):
        if not callable(other):
            raise Exception("%r is not composable with %r" % (self, other))
        return CompositeAnalyzer(self, other)

    def __repr__(self):
        attrs = ""
        if self.__dict__:
            attrs = ", ".join("%s=%r" % (key, value)
                              for key, value
                              in iteritems(self.__dict__))
        return self.__class__.__name__ + "(%s)" % attrs

    def has_morph(self):
        return self.is_morph


# Tokenizers

class Tokenizer(Composable):
    """Base class for Tokenizers.
    """

    def __eq__(self, other):
        return other and self.__class__ is other.__class__


class IDTokenizer(Tokenizer):
    """Yields the entire input string as a single token. For use in indexed but
    untokenized fields, such as a document's path.
    
    >>> idt = IDTokenizer()
    >>> [token.text for token in idt("/a/b 123 alpha")]
    ["/a/b 123 alpha"]
    """

    def __call__(self, value, positions=False, chars=False,
                 keeporiginal=False, removestops=True,
                 start_pos=0, start_char=0, mode='', **kwargs):
        assert isinstance(value, text_type), "%r is not unicode" % value
        t = Token(positions, chars, removestops=removestops, mode=mode,
                  **kwargs)
        t.text = value
        t.boost = 1.0
        if keeporiginal:
            t.original = value
        if positions:
            t.pos = start_pos + 1
        if chars:
            t.startchar = start_char
            t.endchar = start_char + len(value)
        yield t


class RegexTokenizer(Tokenizer):
    """
    Uses a regular expression to extract tokens from text.
    
    >>> rex = RegexTokenizer()
    >>> [token.text for token in rex(u("hi there 3.141 big-time under_score"))]
    ["hi", "there", "3.141", "big", "time", "under_score"]
    """

    __inittypes__ = dict(expression=text_type, gaps=bool)

    def __init__(self, expression=default_pattern, gaps=False):
        """
        :param expression: A regular expression object or string. Each match
            of the expression equals a token. Group 0 (the entire matched text)
            is used as the text of the token. If you require more complicated
            handling of the expression match, simply write your own tokenizer.
        :param gaps: If True, the tokenizer *splits* on the expression, rather
            than matching on the expression.
        """

        self.expression = rcompile(expression)
        self.gaps = gaps

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            if self.expression.pattern == other.expression.pattern:
                return True
        return False

    def __call__(self, value, positions=False, chars=False, keeporiginal=False,
                 removestops=True, start_pos=0, start_char=0, tokenize=True,
                 mode='', **kwargs):
        """
        :param value: The unicode string to tokenize.
        :param positions: Whether to record token positions in the token.
        :param chars: Whether to record character offsets in the token.
        :param start_pos: The position number of the first token. For example,
            if you set start_pos=2, the tokens will be numbered 2,3,4,...
            instead of 0,1,2,...
        :param start_char: The offset of the first character of the first
            token. For example, if you set start_char=2, the text "aaa bbb"
            will have chars (2,5),(6,9) instead (0,3),(4,7).
        :param tokenize: if True, the text should be tokenized.
        """

        assert isinstance(value, text_type), "%r is not unicode" % value

        t = Token(positions, chars, removestops=removestops, mode=mode,
                  **kwargs)
        if not tokenize:
            t.original = t.text = value
            t.boost = 1.0
            if positions:
                t.pos = start_pos
            if chars:
                t.startchar = start_char
                t.endchar = start_char + len(value)
            yield t
        elif not self.gaps:
            # The default: expression matches are used as tokens
            for pos, match in enumerate(self.expression.finditer(value)):
                t.text = match.group(0)
                t.boost = 1.0
                if keeporiginal:
                    t.original = t.text
                t.stopped = False
                if positions:
                    t.pos = start_pos + pos
                if chars:
                    t.startchar = start_char + match.start()
                    t.endchar = start_char + match.end()
                yield t
        else:
            # When gaps=True, iterate through the matches and
            # yield the text between them.
            prevend = 0
            pos = start_pos
            for match in self.expression.finditer(value):
                start = prevend
                end = match.start()
                text = value[start:end]
                if text:
                    t.text = text
                    t.boost = 1.0
                    if keeporiginal:
                        t.original = t.text
                    t.stopped = False
                    if positions:
                        t.pos = pos
                        pos += 1
                    if chars:
                        t.startchar = start_char + start
                        t.endchar = start_char + end

                    yield t

                prevend = match.end()

            # If the last "gap" was before the end of the text,
            # yield the last bit of text as a final token.
            if prevend < len(value):
                t.text = value[prevend:]
                t.boost = 1.0
                if keeporiginal:
                    t.original = t.text
                t.stopped = False
                if positions:
                    t.pos = pos
                if chars:
                    t.startchar = prevend
                    t.endchar = len(value)
                yield t


class CharsetTokenizer(Tokenizer):
    """Tokenizes and translates text according to a character mapping object.
    Characters that map to None are considered token break characters. For all
    other characters the map is used to translate the character. This is useful
    for case and accent folding.
    
    This tokenizer loops character-by-character and so will likely be much
    slower than :class:`RegexTokenizer`.
    
    One way to get a character mapping object is to convert a Sphinx charset
    table file using :func:`whoosh.support.charset.charset_table_to_dict`.
    
    >>> from whoosh.support.charset import charset_table_to_dict
    >>> from whoosh.support.charset import default_charset
    >>> charmap = charset_table_to_dict(default_charset)
    >>> chtokenizer = CharsetTokenizer(charmap)
    >>> [t.text for t in chtokenizer(u'Stra\\xdfe ABC')]
    [u'strase', u'abc']
    
    The Sphinx charset table format is described at
    http://www.sphinxsearch.com/docs/current.html#conf-charset-table.
    """

    __inittype__ = dict(charmap=str)

    def __init__(self, charmap):
        """
        :param charmap: a mapping from integer character numbers to unicode
            characters, as used by the unicode.translate() method.
        """
        self.charmap = charmap

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.charmap == other.charmap)

    def __call__(self, value, positions=False, chars=False, keeporiginal=False,
                 removestops=True, start_pos=0, start_char=0, tokenize=True,
                  mode='', **kwargs):
        """
        :param value: The unicode string to tokenize.
        :param positions: Whether to record token positions in the token.
        :param chars: Whether to record character offsets in the token.
        :param start_pos: The position number of the first token. For example,
            if you set start_pos=2, the tokens will be numbered 2,3,4,...
            instead of 0,1,2,...
        :param start_char: The offset of the first character of the first
            token. For example, if you set start_char=2, the text "aaa bbb"
            will have chars (2,5),(6,9) instead (0,3),(4,7).
        :param tokenize: if True, the text should be tokenized.
        """

        assert isinstance(value, text_type), "%r is not unicode" % value

        t = Token(positions, chars, removestops=removestops, mode=mode,
                  **kwargs)
        if not tokenize:
            t.original = t.text = value
            t.boost = 1.0
            if positions:
                t.pos = start_pos
            if chars:
                t.startchar = start_char
                t.endchar = start_char + len(value)
            yield t
        else:
            text = u("")
            charmap = self.charmap
            pos = start_pos
            startchar = currentchar = start_char
            for char in value:
                tchar = charmap[ord(char)]
                if tchar:
                    text += tchar
                else:
                    if currentchar > startchar:
                        t.text = text
                        t.boost = 1.0
                        if keeporiginal:
                            t.original = t.text
                        if positions:
                            t.pos = pos
                            pos += 1
                        if chars:
                            t.startchar = startchar
                            t.endchar = currentchar
                        yield t
                    startchar = currentchar + 1
                    text = u("")

                currentchar += 1

            if currentchar > startchar:
                t.text = value[startchar:currentchar]
                t.boost = 1.0
                if keeporiginal:
                    t.original = t.text
                if positions:
                    t.pos = pos
                if chars:
                    t.startchar = startchar
                    t.endchar = currentchar
                yield t


def SpaceSeparatedTokenizer():
    """Returns a RegexTokenizer that splits tokens by whitespace.
    
    >>> sst = SpaceSeparatedTokenizer()
    >>> [token.text for token in sst("hi there big-time, what's up")]
    ["hi", "there", "big-time,", "what's", "up"]
    """

    return RegexTokenizer(r"[^ \t\r\n]+")


def CommaSeparatedTokenizer():
    """Splits tokens by commas.
    
    Note that the tokenizer calls unicode.strip() on each match of the regular
    expression.
    
    >>> cst = CommaSeparatedTokenizer()
    >>> [token.text for token in cst("hi there, what's , up")]
    ["hi there", "what's", "up"]
    """

    return RegexTokenizer(r"[^,]+") | StripFilter()


class NgramTokenizer(Tokenizer):
    """Splits input text into N-grams instead of words.
    
    >>> ngt = NgramTokenizer(4)
    >>> [token.text for token in ngt("hi there")]
    ["hi t", "i th", " the", "ther", "here"]

    Note that this tokenizer does NOT use a regular expression to extract
    words, so the grams emitted by it will contain whitespace, punctuation,
    etc. You may want to massage the input or add a custom filter to this
    tokenizer's output.
    
    Alternatively, if you only want sub-word grams without whitespace, you
    could combine a RegexTokenizer with NgramFilter instead.
    """

    __inittypes__ = dict(minsize=int, maxsize=int)

    def __init__(self, minsize, maxsize=None):
        """
        :param minsize: The minimum size of the N-grams.
        :param maxsize: The maximum size of the N-grams. If you omit
            this parameter, maxsize == minsize.
        """

        self.min = minsize
        self.max = maxsize or minsize

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            if self.min == other.min and self.max == other.max:
                return True
        return False

    def __call__(self, value, positions=False, chars=False, keeporiginal=False,
                 removestops=True, start_pos=0, start_char=0, mode='',
                 **kwargs):
        assert isinstance(value, text_type), "%r is not unicode" % value

        inlen = len(value)
        t = Token(positions, chars, removestops=removestops, mode=mode)
        pos = start_pos

        if mode == "query":
            size = min(self.max, inlen)
            for start in xrange(0, inlen - size + 1):
                end = start + size
                if end > inlen:
                    continue
                t.text = value[start:end]
                if keeporiginal:
                    t.original = t.text
                t.stopped = False
                if positions:
                    t.pos = pos
                if chars:
                    t.startchar = start_char + start
                    t.endchar = start_char + end
                yield t
                pos += 1
        else:
            for start in xrange(0, inlen - self.min + 1):
                for size in xrange(self.min, self.max + 1):
                    end = start + size
                    if end > inlen:
                        continue
                    t.text = value[start:end]
                    if keeporiginal:
                        t.original = t.text
                    t.stopped = False
                    if positions:
                        t.pos = pos
                    if chars:
                        t.startchar = start_char + start
                        t.endchar = start_char + end

                    yield t
                pos += 1


class PathTokenizer(Tokenizer):
    """A simple tokenizer that given a string ``"/a/b/c"`` yields tokens
    ``["/a", "/a/b", "/a/b/c"]``.
    """

    def __init__(self, expression="[^/]+"):
        self.expr = rcompile(expression, re.UNICODE)

    def __call__(self, value, **kwargs):
        assert isinstance(value, text_type), "%r is not unicode" % value
        token = Token(**kwargs)
        for match in self.expr.finditer(value):
            token.text = value[:match.end()]
            yield token


# Filters

class Filter(Composable):
    """Base class for Filter objects. A Filter subclass must implement a
    filter() method that takes a single argument, which is an iterator of Token
    objects, and yield a series of Token objects in return.
    
    Filters that do morphological transformation of tokens (e.g. stemming)
    should set their ``is_morph`` attribute to True.
    """

    def __eq__(self, other):
        return other and self.__class__ is other.__class__

    def __call__(self, tokens):
        raise NotImplementedError


class PassFilter(Filter):
    """An identity filter: passes the tokens through untouched.
    """

    def __call__(self, tokens):
        return tokens


class LoggingFilter(Filter):
    """Prints the contents of every filter that passes through as a debug
    log entry.
    """

    def __init__(self, logger=None):
        """
        :param target: the logger to use. If omitted, the "whoosh.analysis"
            logger is used.
        """

        if logger is None:
            import logging
            logger = logging.getLogger("whoosh.analysis")
        self.logger = logger

    def __call__(self, tokens):
        logger = self.logger
        for t in tokens:
            logger.debug(repr(t))
            yield t


class MultiFilter(Filter):
    """Chooses one of two or more sub-filters based on the 'mode' attribute
    of the token stream.
    """

    default_filter = PassFilter()

    def __init__(self, **kwargs):
        """Use keyword arguments to associate mode attribute values with
        instantiated filters.
        
        >>> iwf_for_index = IntraWordFilter(mergewords=True, mergenums=False)
        >>> iwf_for_query = IntraWordFilter(mergewords=False, mergenums=False)
        >>> mf = MultiFilter(index=iwf_for_index, query=iwf_for_query)
        
        This class expects that the value of the mode attribute is consistent
        among all tokens in a token stream.
        """
        self.filters = kwargs

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.filters == other.filters)

    def __call__(self, tokens):
        # Only selects on the first token
        t = next(tokens)
        filter = self.filters.get(t.mode, self.default_filter)
        return filter(chain([t], tokens))


class TeeFilter(Filter):
    """Interleaves the results of two or more filters (or filter chains).
    
    NOTE: because it needs to create copies of each token for each sub-filter,
    this filter is quite slow.
    
    >>> target = "ALFA BRAVO CHARLIE"
    >>> # In one branch, we'll lower-case the tokens
    >>> f1 = LowercaseFilter()
    >>> # In the other branch, we'll reverse the tokens
    >>> f2 = ReverseTextFilter()
    >>> ana = RegexTokenizer(r"\S+") | TeeFilter(f1, f2)
    >>> [token.text for token in ana(target)]
    ["alfa", "AFLA", "bravo", "OVARB", "charlie", "EILRAHC"]
    
    To combine the incoming token stream with the output of a filter chain, use
    ``TeeFilter`` and make one of the filters a :class:`PassFilter`.
    
    >>> f1 = PassFilter()
    >>> f2 = BiWordFilter()
    >>> ana = RegexTokenizer(r"\S+") | TeeFilter(f1, f2) | LowercaseFilter()
    >>> [token.text for token in ana(target)]
    ["alfa", "alfa-bravo", "bravo", "bravo-charlie", "charlie"]
    """

    def __init__(self, *filters):
        if len(filters) < 2:
            raise Exception("TeeFilter requires two or more filters")
        self.filters = filters

    def __eq__(self, other):
        return (self.__class__ is other.__class__
                and self.filters == other.fitlers)

    def __call__(self, tokens):
        from itertools import tee

        count = len(self.filters)
        # Tee the token iterator and wrap each teed iterator with the
        # corresponding filter
        gens = [filter(t.copy() for t in gen) for filter, gen
                in zip(self.filters, tee(tokens, count))]
        # Keep a count of the number of running iterators
        running = count
        while running:
            for i, gen in enumerate(gens):
                if gen is not None:
                    try:
                        yield next(gen)
                    except StopIteration:
                        gens[i] = None
                        running -= 1


class ReverseTextFilter(Filter):
    """Reverses the text of each token.
    
    >>> ana = RegexTokenizer() | ReverseTextFilter()
    >>> [token.text for token in ana("hello there")]
    ["olleh", "ereht"]
    """

    def __call__(self, tokens):
        for t in tokens:
            t.text = t.text[::-1]
            yield t


class LowercaseFilter(Filter):
    """Uses unicode.lower() to lowercase token text.
    
    >>> rext = RegexTokenizer()
    >>> stream = rext("This is a TEST")
    >>> [token.text for token in LowercaseFilter(stream)]
    ["this", "is", "a", "test"]
    """

    def __call__(self, tokens):
        for t in tokens:
            t.text = t.text.lower()
            yield t


class StripFilter(Filter):
    """Calls unicode.strip() on the token text.
    """

    def __call__(self, tokens):
        for t in tokens:
            t.text = t.text.strip()
            yield t


class StopFilter(Filter):
    """Marks "stop" words (words too common to index) in the stream (and by
    default removes them).
    
    >>> rext = RegexTokenizer()
    >>> stream = rext("this is a test")
    >>> stopper = StopFilter()
    >>> [token.text for token in stopper(stream)]
    ["this", "test"]
    """

    __inittypes__ = dict(stoplist=list, minsize=int, maxsize=int,
                         renumber=bool)

    def __init__(self, stoplist=STOP_WORDS, minsize=2, maxsize=None,
                 renumber=True):
        """
        :param stoplist: A collection of words to remove from the stream.
            This is converted to a frozenset. The default is a list of
            common English stop words.
        :param minsize: The minimum length of token texts. Tokens with
            text smaller than this will be stopped.
        :param maxsize: The maximum length of token texts. Tokens with text
            larger than this will be stopped. Use None to allow any length.
        :param renumber: Change the 'pos' attribute of unstopped tokens
            to reflect their position with the stopped words removed.
        :param remove: Whether to remove the stopped words from the stream
            entirely. This is not normally necessary, since the indexing
            code will ignore tokens it receives with stopped=True.
        """

        if stoplist is None:
            self.stops = frozenset()
        else:
            self.stops = frozenset(stoplist)
        self.min = minsize
        self.max = maxsize
        self.renumber = renumber

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.stops == other.stops
                and self.min == other.min
                and self.renumber == other.renumber)

    def __call__(self, tokens):
        stoplist = self.stops
        minsize = self.min
        maxsize = self.max
        renumber = self.renumber

        pos = None
        for t in tokens:
            text = t.text
            if (len(text) >= minsize
                and (maxsize is None or len(text) <= maxsize)
                and text not in stoplist):
                # This is not a stop word
                if renumber and t.positions:
                    if pos is None:
                        pos = t.pos
                    else:
                        pos += 1
                        t.pos = pos
                t.stopped = False
                yield t
            else:
                # This is a stop word
                if not t.removestops:
                    # This IS a stop word, but we're not removing them
                    t.stopped = True
                    yield t


class StemFilter(Filter):
    """Stems (removes suffixes from) the text of tokens using the Porter
    stemming algorithm. Stemming attempts to reduce multiple forms of the same
    root word (for example, "rendering", "renders", "rendered", etc.) to a
    single word in the index.
    
    >>> stemmer = RegexTokenizer() | StemFilter()
    >>> [token.text for token in stemmer("fundamentally willows")]
    ["fundament", "willow"]
    
    You can pass your own stemming function to the StemFilter. The default
    is the Porter stemming algorithm for English.
    
    >>> stemfilter = StemFilter(stem_function)
    
    By default, this class wraps an LRU cache around the stemming function. The
    ``cachesize`` keyword argument sets the size of the cache. To make the
    cache unbounded (the class caches every input), use ``cachesize=-1``. To
    disable caching, use ``cachesize=None``.
    
    If you compile and install the py-stemmer library, the
    :class:`PyStemmerFilter` provides slightly easier access to the language
    stemmers in that library.
    """

    __inittypes__ = dict(stemfn=object, ignore=list)

    is_morph = True

    def __init__(self, stemfn=stem, ignore=None, cachesize=50000):
        """
        :param stemfn: the function to use for stemming.
        :param ignore: a set/list of words that should not be stemmed. This is
            converted into a frozenset. If you omit this argument, all tokens
            are stemmed.
        :param cachesize: the maximum number of words to cache. Use ``-1`` for
            an unbounded cache, or ``None`` for no caching.
        """

        self.stemfn = stemfn
        self.ignore = frozenset() if ignore is None else frozenset(ignore)
        self.cachesize = cachesize
        # clear() sets the _stem attr to a cached wrapper around self.stemfn
        self.clear()

    def __getstate__(self):
        # Can't pickle a dynamic function, so we have to remove the _stem
        # attribute from the state
        return dict([(k, self.__dict__[k]) for k in self.__dict__
                      if k != "_stem"])

    def __setstate__(self, state):
        # Check for old instances of StemFilter class, which didn't have a
        # cachesize attribute and pickled the cache attribute
        if "cachesize" not in state:
            self.cachesize = 50000
        if "ignores" in state:
            self.ignore = state["ignores"]
        elif "ignore" not in state:
            self.ignore = frozenset()
        if "cache" in state:
            del state["cache"]

        self.__dict__.update(state)
        # Set the _stem attribute
        self.clear()

    def clear(self):
        if self.cachesize < 0:
            self._stem = unbound_cache(self.stemfn)
        elif self.cachesize > 1:
            self._stem = lru_cache(self.cachesize)(self.stemfn)
        else:
            self._stem = self.stemfn

    def cache_info(self):
        if self.cachesize <= 1:
            return None
        return self._stem.cache_info()

    def __eq__(self, other):
        return (other and self.__class__ is other.__class__
                and self.stemfn == other.stemfn)

    def __call__(self, tokens):
        stemfn = self._stem
        ignore = self.ignore

        for t in tokens:
            if not t.stopped:
                text = t.text
                if text not in ignore:
                    t.text = stemfn(text)
            yield t


class PyStemmerFilter(StemFilter):
    """This is a simple subclass of StemFilter that works with the py-stemmer
    third-party library. You must have the py-stemmer library installed to use
    this filter.
    
    >>> PyStemmerFilter("spanish")
    """

    def __init__(self, lang="english", ignore=None, cachesize=10000):
        """
        :param lang: a string identifying the stemming algorithm to use. You
            can get a list of available algorithms by with the
            :meth:`PyStemmerFilter.algorithms` method. The identification
            strings are directly from the py-stemmer library.
        :param ignore: a set/list of words that should not be stemmed. This is
            converted into a frozenset. If you omit this argument, all tokens
            are stemmed.
        :param cachesize: the maximum number of words to cache.
        """

        import Stemmer  #@UnresolvedImport

        stemmer = Stemmer.Stemmer(lang)
        stemmer.maxCacheSize = cachesize
        self._stem = stemmer.stemWord
        self.ignore = frozenset() if ignore is None else frozenset(ignore)

    def algorithms(self):
        """Returns a list of stemming algorithms provided by the py-stemmer
        library.
        """

        import Stemmer  #@UnresolvedImport

        return Stemmer.algorithms()

    def cache_info(self):
        return None


class CharsetFilter(Filter):
    """Translates the text of tokens by calling unicode.translate() using the
    supplied character mapping object. This is useful for case and accent
    folding.
    
    The ``whoosh.support.charset`` module has a useful map for accent folding.
    
    >>> from whoosh.support.charset import accent_map
    >>> retokenizer = RegexTokenizer()
    >>> chfilter = CharsetFilter(accent_map)
    >>> [t.text for t in chfilter(retokenizer(u'café'))]
    [u'cafe']
    
    Another way to get a character mapping object is to convert a Sphinx
    charset table file using
    :func:`whoosh.support.charset.charset_table_to_dict`.
    
    >>> from whoosh.support.charset import charset_table_to_dict
    >>> from whoosh.support.charset import default_charset
    >>> retokenizer = RegexTokenizer()
    >>> charmap = charset_table_to_dict(default_charset)
    >>> chfilter = CharsetFilter(charmap)
    >>> [t.text for t in chfilter(retokenizer(u'Stra\\xdfe'))]
    [u'strase']
    
    The Sphinx charset table format is described at
    http://www.sphinxsearch.com/docs/current.html#conf-charset-table.
    """

    __inittypes__ = dict(charmap=dict)

    def __init__(self, charmap):
        """
        :param charmap: a dictionary mapping from integer character numbers to
            unicode characters, as required by the unicode.translate() method.
        """
        self.charmap = charmap

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.charmap == other.charmap)

    def __call__(self, tokens):
        assert hasattr(tokens, "__iter__")
        charmap = self.charmap
        for t in tokens:
            t.text = t.text.translate(charmap)
            yield t


class NgramFilter(Filter):
    """Splits token text into N-grams.
    
    >>> rext = RegexTokenizer()
    >>> stream = rext("hello there")
    >>> ngf = NgramFilter(4)
    >>> [token.text for token in ngf(stream)]
    ["hell", "ello", "ther", "here"]
    """

    __inittypes__ = dict(minsize=int, maxsize=int)

    def __init__(self, minsize, maxsize=None, at=None):
        """
        :param minsize: The minimum size of the N-grams.
        :param maxsize: The maximum size of the N-grams. If you omit this
            parameter, maxsize == minsize.
        :param at: If 'start', only take N-grams from the start of each word.
            if 'end', only take N-grams from the end of each word. Otherwise,
            take all N-grams from the word (the default).
        """

        self.min = minsize
        self.max = maxsize or minsize
        self.at = 0
        if at == "start":
            self.at = -1
        elif at == "end":
            self.at = 1

    def __eq__(self, other):
        return other and self.__class__ is other.__class__\
        and self.min == other.min and self.max == other.max

    def __call__(self, tokens):
        assert hasattr(tokens, "__iter__")
        at = self.at
        for t in tokens:
            text = t.text
            if len(text) < self.min:
                continue

            chars = t.chars
            if chars:
                startchar = t.startchar
            # Token positions don't mean much for N-grams,
            # so we'll leave the token's original position
            # untouched.

            if t.mode == "query":
                size = min(self.max, len(t.text))
                if at == -1:
                    t.text = text[:size]
                    if chars:
                        t.endchar = startchar + size
                    yield t
                elif at == 1:
                    t.text = text[0 - size:]
                    if chars:
                        t.startchar = t.endchar - size
                    yield t
                else:
                    for start in xrange(0, len(text) - size + 1):
                        t.text = text[start:start + size]
                        if chars:
                            t.startchar = startchar + start
                            t.endchar = startchar + start + size
                        yield t
            else:
                if at == -1:
                    limit = min(self.max, len(text))
                    for size in xrange(self.min, limit + 1):
                        t.text = text[:size]
                        if chars:
                            t.endchar = startchar + size
                        yield t

                elif at == 1:
                    start = max(0, len(text) - self.max)
                    for i in xrange(start, len(text) - self.min + 1):
                        t.text = text[i:]
                        if chars:
                            t.startchar = t.endchar - size
                        yield t
                else:
                    for start in xrange(0, len(text) - self.min + 1):
                        for size in xrange(self.min, self.max + 1):
                            end = start + size
                            if end > len(text):
                                continue

                            t.text = text[start:end]

                            if chars:
                                t.startchar = startchar + start
                                t.endchar = startchar + end

                            yield t


class IntraWordFilter(Filter):
    """Splits words into subwords and performs optional transformations on
    subword groups. This filter is funtionally based on yonik's
    WordDelimiterFilter in Solr, but shares no code with it.
    
    * Split on intra-word delimiters, e.g. `Wi-Fi` -> `Wi`, `Fi`.
    * When splitwords=True, split on case transitions,
      e.g. `PowerShot` -> `Power`, `Shot`.
    * When splitnums=True, split on letter-number transitions,
      e.g. `SD500` -> `SD`, `500`.
    * Leading and trailing delimiter characters are ignored.
    * Trailing possesive "'s" removed from subwords,
      e.g. `O'Neil's` -> `O`, `Neil`.
    
    The mergewords and mergenums arguments turn on merging of subwords.
    
    When the merge arguments are false, subwords are not merged.
    
    * `PowerShot` -> `0`:`Power`, `1`:`Shot` (where `0` and `1` are token
      positions).
    
    When one or both of the merge arguments are true, consecutive runs of
    alphabetic and/or numeric subwords are merged into an additional token with
    the same position as the last sub-word.
    
    * `PowerShot` -> `0`:`Power`, `1`:`Shot`, `1`:`PowerShot`
    * `A's+B's&C's` -> `0`:`A`, `1`:`B`, `2`:`C`, `2`:`ABC`
    * `Super-Duper-XL500-42-AutoCoder!` -> `0`:`Super`, `1`:`Duper`, `2`:`XL`,
      `2`:`SuperDuperXL`,
      `3`:`500`, `4`:`42`, `4`:`50042`, `5`:`Auto`, `6`:`Coder`,
      `6`:`AutoCoder`
    
    When using this filter you should use a tokenizer that only splits on
    whitespace, so the tokenizer does not remove intra-word delimiters before
    this filter can see them, and put this filter before any use of
    LowercaseFilter.
    
    >>> rt = RegexTokenizer(r"\\S+")
    >>> iwf = IntraWordFilter()
    >>> lcf = LowercaseFilter()
    >>> analyzer = rt | iwf | lcf
    
    One use for this filter is to help match different written representations
    of a concept. For example, if the source text contained `wi-fi`, you
    probably want `wifi`, `WiFi`, `wi-fi`, etc. to match. One way of doing this
    is to specify mergewords=True and/or mergenums=True in the analyzer used
    for indexing, and mergewords=False / mergenums=False in the analyzer used
    for querying.
    
    >>> iwf_i = IntraWordFilter(mergewords=True, mergenums=True)
    >>> iwf_q = IntraWordFilter(mergewords=False, mergenums=False)
    >>> iwf = MultiFilter(index=iwf_i, query=iwf_q)
    >>> analyzer = RegexTokenizer(r"\S+") | iwf | LowercaseFilter()
    
    (See :class:`MultiFilter`.)
    """

    is_morph = True

    __inittypes__ = dict(delims=text_type, splitwords=bool, splitnums=bool,
                         mergewords=bool, mergenums=bool)

    def __init__(self, delims=u("-_'\"()!@#$%^&*[]{}<>\|;:,./?`~=+"),
                 splitwords=True, splitnums=True,
                 mergewords=False, mergenums=False):
        """
        :param delims: a string of delimiter characters.
        :param splitwords: if True, split at case transitions,
            e.g. `PowerShot` -> `Power`, `Shot`
        :param splitnums: if True, split at letter-number transitions,
            e.g. `SD500` -> `SD`, `500`
        :param mergewords: merge consecutive runs of alphabetic subwords into
            an additional token with the same position as the last subword.
        :param mergenums: merge consecutive runs of numeric subwords into an
            additional token with the same position as the last subword.
        """

        from whoosh.support.unicode import digits, lowercase, uppercase

        self.delims = re.escape(delims)

        # Expression for text between delimiter characters
        self.between = re.compile(u("[^%s]+") % (self.delims,), re.UNICODE)
        # Expression for removing "'s" from the end of sub-words
        dispat = u("(?<=[%s%s])'[Ss](?=$|[%s])") % (lowercase, uppercase,
                                                    self.delims)
        self.possessive = re.compile(dispat, re.UNICODE)

        # Expression for finding case and letter-number transitions
        lower2upper = u("[%s][%s]") % (lowercase, uppercase)
        letter2digit = u("[%s%s][%s]") % (lowercase, uppercase, digits)
        digit2letter = u("[%s][%s%s]") % (digits, lowercase, uppercase)
        if splitwords and splitnums:
            splitpat = u("(%s|%s|%s)") % (lower2upper, letter2digit,
                                          digit2letter)
            self.boundary = re.compile(splitpat, re.UNICODE)
        elif splitwords:
            self.boundary = re.compile(text_type(lower2upper), re.UNICODE)
        elif splitnums:
            numpat = u("(%s|%s)") % (letter2digit, digit2letter)
            self.boundary = re.compile(numpat, re.UNICODE)

        self.splitting = splitwords or splitnums
        self.mergewords = mergewords
        self.mergenums = mergenums

    def __eq__(self, other):
        return other and self.__class__ is other.__class__\
        and self.__dict__ == other.__dict__

    def _split(self, string):
        bound = self.boundary

        # Yields (startchar, endchar) pairs for each indexable substring in
        # the given string, e.g. "WikiWord" -> (0, 4), (4, 8)

        # Whether we're splitting on transitions (case changes, letter -> num,
        # num -> letter, etc.)
        splitting = self.splitting

        # Make a list (dispos, for "dispossessed") of (startchar, endchar)
        # pairs for runs of text between "'s"
        if "'" in string:
            # Split on possessive 's
            dispos = []
            prev = 0
            for match in self.possessive.finditer(string):
                dispos.append((prev, match.start()))
                prev = match.end()
            if prev < len(string):
                dispos.append((prev, len(string)))
        else:
            # Shortcut if there's no apostrophe in the string
            dispos = ((0, len(string)),)

        # For each run between 's
        for sc, ec in dispos:
            # Split on boundary characters
            for part_match in self.between.finditer(string, sc, ec):
                part_start = part_match.start()
                part_end = part_match.end()

                if splitting:
                    # The point to start splitting at
                    prev = part_start
                    # Find transitions (e.g. "iW" or "a0")
                    for bmatch in bound.finditer(string, part_start, part_end):
                        # The point in the middle of the transition
                        pivot = bmatch.start() + 1
                        # Yield from the previous match to the transition
                        yield (prev, pivot)
                        # Make the transition the new starting point
                        prev = pivot

                    # If there's leftover text at the end, yield it too
                    if prev < part_end:
                        yield (prev, part_end)
                else:
                    # Not splitting on transitions, just yield the part
                    yield (part_start, part_end)

    def _merge(self, parts):
        mergewords = self.mergewords
        mergenums = self.mergenums

        # Current type (1=alpah, 2=digit)
        last = 0
        # Where to insert a merged term in the original list
        insertat = 0
        # Buffer for parts to merge
        buf = []
        # Iterate on a copy of the parts list so we can modify the original as
        # we go

        def insert_item(buf, at, newpos):
            newtext = "".join(item[0] for item in buf)
            newsc = buf[0][2]  # start char of first item in buffer
            newec = buf[-1][3]  # end char of last item in buffer
            parts.insert(insertat, (newtext, newpos, newsc, newec))

        for item in parts[:]:
            # item = (text, pos, startchar, endchar)
            text = item[0]
            pos = item[1]

            # Set the type of this part
            if text.isalpha():
                this = 1
            elif text.isdigit():
                this = 2

            # Is this the same type as the previous part?
            if (buf and (this == last == 1 and mergewords)
                or (this == last == 2 and mergenums)):
                # This part is the same type as the previous. Add it to the
                # buffer of parts to merge.
                buf.append(item)
            else:
                # This part is different than the previous.
                if len(buf) > 1:
                    # If the buffer has at least two parts in it, merge them
                    # and add them to the original list of parts.
                    insert_item(buf, insertat, pos - 1)
                    insertat += 1
                # Reset the buffer
                buf = [item]
                last = this
            insertat += 1

        # If there are parts left in the buffer at the end, merge them and add
        # them to the original list.
        if len(buf) > 1:
            insert_item(buf, len(parts), pos)

    def __call__(self, tokens):
        mergewords = self.mergewords
        mergenums = self.mergenums

        # This filter renumbers tokens as it expands them. New position
        # counter.
        newpos = None
        for t in tokens:
            text = t.text

            # If this is the first token we've seen, use it to set the new
            # position counter
            if newpos is None:
                if t.positions:
                    newpos = t.pos
                else:
                    # Token doesn't have positions, just use 0
                    newpos = 0

            if ((text.isalpha() and (text.islower() or text.isupper()))
                or text.isdigit()):
                # Short-circuit the common cases of no delimiters, no case
                # transitions, only digits, etc.
                t.pos = newpos
                yield t
                newpos += 1
            else:
                # Split the token text on delimiters, word and/or number
                # boundaries into a list of (text, pos, startchar, endchar)
                # tuples
                ranges = self._split(text)
                parts = [(text[sc:ec], i + newpos, sc, ec)
                         for i, (sc, ec) in enumerate(ranges)]

                # Did the split yield more than one part?
                if len(parts) > 1:
                    # If the options are set, merge consecutive runs of all-
                    # letters and/or all-numbers.
                    if mergewords or mergenums:
                        self._merge(parts)

                # Yield tokens for the parts
                chars = t.chars
                if chars:
                    base = t.startchar
                for text, pos, startchar, endchar in parts:
                    t.text = text
                    t.pos = pos
                    if t.chars:
                        t.startchar = base + startchar
                        t.endchar = base + endchar
                    yield t

                if parts:
                    # Set the new position counter based on the last part
                    newpos = parts[-1][1] + 1


class CompoundWordFilter(Filter):
    """Given a set of words (or any object with a ``__contains__`` method),
    break any tokens in the stream that are composites of words in the word set
    into their individual parts.
    
    Given the correct set of words, this filter can break apart run-together
    words and trademarks (e.g. "turbosquid", "applescript"). It can also be
    useful for agglutinative languages such as German.
    
    The ``keep_compound`` argument lets you decide whether to keep the
    compound word in the token stream along with the word segments.
    
    >>> cwf = CompoundWordFilter(wordset, keep_compound=True)
    >>> analyzer = RegexTokenizer(r"\S+") | cwf
    >>> [t.text for t in analyzer("I do not like greeneggs and ham")
    ["I", "do", "not", "like", "greeneggs", "green", "eggs", "and", "ham"]
    >>> cwf.keep_compound = False
    >>> [t.text for t in analyzer("I do not like greeneggs and ham")
    ["I", "do", "not", "like", "green", "eggs", "and", "ham"]
    """

    def __init__(self, wordset, keep_compound=True):
        """
        :param wordset: an object with a ``__contains__`` method, such as a
            set, containing strings to look for inside the tokens.
        :param keep_compound: if True (the default), the original compound
            token will be retained in the stream before the subwords.
        """

        self.wordset = wordset
        self.keep_compound = keep_compound

    def subwords(self, s, memo):
        if s in self.wordset:
            return [s]
        if s in memo:
            return memo[s]

        for i in xrange(1, len(s)):
            prefix = s[:i]
            if prefix in self.wordset:
                suffix = s[i:]
                suffix_subs = self.subwords(suffix, memo)
                if suffix_subs:
                    result = [prefix] + suffix_subs
                    memo[s] = result
                    return result

        return None

    def __call__(self, tokens):
        keep_compound = self.keep_compound
        memo = {}
        subwords = self.subwords
        for t in tokens:
            subs = subwords(t.text, memo)
            if subs:
                if len(subs) > 1 and keep_compound:
                    yield t
                for subword in subs:
                    t.text = subword
                    yield t
            else:
                yield t


class BiWordFilter(Filter):
    """Merges adjacent tokens into "bi-word" tokens, so that for example::
    
        "the", "sign", "of", "four"
        
    becomes::
    
        "the-sign", "sign-of", "of-four"
        
    This can be used to create fields for pseudo-phrase searching, where if
    all the terms match the document probably contains the phrase, but the
    searching is faster than actually doing a phrase search on individual word
    terms.
    
    The ``BiWordFilter`` is much faster than using the otherwise equivalent
    ``ShingleFilter(2)``.
    """

    def __init__(self, sep="-"):
        self.sep = sep

    def __call__(self, tokens):
        sep = self.sep
        prev_text = None
        prev_startchar = None
        prev_pos = None
        atleastone = False

        for token in tokens:
            # Save the original text of this token
            text = token.text

            # Save the original position
            positions = token.positions
            if positions:
                ps = token.pos

            # Save the original start char
            chars = token.chars
            if chars:
                sc = token.startchar

            if prev_text is not None:
                # Use the pos and startchar from the previous token
                if positions:
                    token.pos = prev_pos
                if chars:
                    token.startchar = prev_startchar

                # Join the previous token text and the current token text to
                # form the biword token
                token.text = "".join((prev_text, sep, text))
                yield token
                atleastone = True

            # Save the originals and the new "previous" values
            prev_text = text
            if chars:
                prev_startchar = sc
            if positions:
                prev_pos = ps

        # If no bi-words were emitted, that is, the token stream only had
        # a single token, then emit that single token.
        if not atleastone:
            yield token


class ShingleFilter(Filter):
    """Merges a certain number of adjacent tokens into multi-word tokens, so
    that for example::
    
        "better", "a", "witty", "fool", "than", "a", "foolish", "wit"
        
    with ``ShingleFilter(3, ' ')`` becomes::
    
        'better a witty', 'a witty fool', 'witty fool than', 'fool than a',
        'than a foolish', 'a foolish wit'
    
    This can be used to create fields for pseudo-phrase searching, where if
    all the terms match the document probably contains the phrase, but the
    searching is faster than actually doing a phrase search on individual word
    terms.
    
    If you're using two-word shingles, you should use the functionally
    equivalent ``BiWordFilter`` instead because it's faster than
    ``ShingleFilter``.
    """

    def __init__(self, size=2, sep="-"):
        self.size = size
        self.sep = sep

    def __call__(self, tokens):
        size = self.size
        sep = self.sep
        buf = deque()
        atleastone = False

        def make_token():
            tk = buf[0]
            tk.text = sep.join([t.text for t in buf])
            if tk.chars:
                tk.endchar = buf[-1].endchar
            return tk

        for token in tokens:
            buf.append(token.copy())
            if len(buf) == size:
                atleastone = True
                yield make_token()
                buf.popleft()

        # If no shingles were emitted, that is, the token stream had fewer than
        # 'size' tokens, then emit a single token with whatever tokens there
        # were
        if not atleastone:
            yield make_token()


class BoostTextFilter(Filter):
    "This filter is deprecated, use :class:`DelimitedAttributeFilter` instead."

    def __init__(self, expression, group=1, default=1.0):
        """
        :param expression: a compiled regular expression object representing
            the pattern to look for within each token.
        :param group: the group name or number to use as the boost number
            (what to pass to match.group()). The string value of this group is
            passed to float().
        :param default: the default boost to use for tokens that don't have
            the marker.
        """

        self.expression = expression
        self.group = group
        self.default = default

    def __eq__(self, other):
        return (other and self.__class__ is other.__class__
                and self.expression == other.expression
                and self.default == other.default
                and self.group == other.group)

    def __call__(self, tokens):
        expression = self.expression
        groupnum = self.group
        default = self.default

        for t in tokens:
            text = t.text
            m = expression.match(text)
            if m:
                text = text[:m.start()] + text[m.end():]
                t.boost = float(m.group(groupnum))
            else:
                t.boost = default

            yield t


class DelimitedAttributeFilter(Filter):
    """Looks for delimiter characters in the text of each token and stores the
    data after the delimiter in a named attribute on the token.
    
    The defaults are set up to use the ``^`` character as a delimiter and store
    the value after the ``^`` as the boost for the token.
    
    >>> daf = DelimitedAttributeFilter(delimiter="^", attribute="boost")
    >>> ana = RegexTokenizer("\\\\S+") | DelimitedAttributeFilter()
    >>> for t in ana(u("image render^2 file^0.5"))
    ...    print("%r %f" % (t.text, t.boost))
    'image' 1.0
    'render' 2.0
    'file' 0.5
    
    Note that you need to make sure your tokenizer includes the delimiter and
    data as part of the token!
    """

    def __init__(self, delimiter="^", attribute="boost", default=1.0,
                 type=float):
        """
        :param delimiter: a string that, when present in a token's text,
            separates the actual text from the "data" payload.
        :param attribute: the name of the attribute in which to store the
            data on the token.
        :param default: the value to use for the attribute for tokens that
            don't have delimited data.
        :param type: the type of the data, for example ``str`` or ``float``.
            This is used to convert the string value of the data before
            storing it in the attribute.
        """

        self.delim = delimiter
        self.attr = attribute
        self.default = default
        self.type = type

    def __eq__(self, other):
        return (other and self.__class__ is other.__class__
                and self.delim == other.delim
                and self.attr == other.attr
                and self.default == other.default)

    def __call__(self, tokens):
        delim = self.delim
        attr = self.attr
        default = self.default
        typ = self.type

        for t in tokens:
            text = t.text
            pos = text.find(delim)
            if pos > -1:
                setattr(t, attr, typ(text[pos + 1:]))
                t.text = text[:pos]
            else:
                setattr(t, attr, default)

            yield t


class DoubleMetaphoneFilter(Filter):
    """Transforms the text of the tokens using Lawrence Philips's Double
    Metaphone algorithm. This algorithm attempts to encode words in such a way
    that similar-sounding words reduce to the same code. This may be useful for
    fields containing the names of people and places, and other uses where
    tolerance of spelling differences is desireable.
    """

    is_morph = True

    def __init__(self, primary_boost=1.0, secondary_boost=0.5, combine=False):
        """
        :param primary_boost: the boost to apply to the token containing the
            primary code.
        :param secondary_boost: the boost to apply to the token containing the
            secondary code, if any.
        :param combine: if True, the original unencoded tokens are kept in the
            stream, preceding the encoded tokens.
        """

        self.primary_boost = primary_boost
        self.secondary_boost = secondary_boost
        self.combine = combine

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.primary_boost == other.primary_boost)

    def __call__(self, tokens):
        primary_boost = self.primary_boost
        secondary_boost = self.secondary_boost
        combine = self.combine

        for t in tokens:
            if combine:
                yield t

            primary, secondary = double_metaphone(t.text)
            b = t.boost
            # Overwrite the token's text and boost and yield it
            if primary:
                t.text = primary
                t.boost = b * primary_boost
                yield t
            if secondary:
                t.text = secondary
                t.boost = b * secondary_boost
                yield t


class SubstitutionFilter(Filter):
    """Performs a regular expression substitution on the token text.
    
    This is especially useful for removing text from tokens, for example
    hyphens::
    
        ana = RegexTokenizer(r"\\S+") | SubstitutionFilter("-", "")
        
    Because it has the full power of the re.sub() method behind it, this filter
    can perform some fairly complex transformations. For example, to take
    tokens like ``'a=b', 'c=d', 'e=f'`` and change them to ``'b=a', 'd=c',
    'f=e'``::
    
        # Analyzer that swaps the text on either side of an equal sign
        rt = RegexTokenizer(r"\\S+")
        sf = SubstitutionFilter("([^/]*)/(./*)", r"\\2/\\1")
        ana = rt | sf
    """

    def __init__(self, pattern, replacement):
        """
        :param pattern: a pattern string or compiled regular expression object
            describing the text to replace.
        :param replacement: the substitution text.
        """

        if isinstance(pattern, string_type):
            pattern = re.compile(pattern, re.UNICODE)
        self.pattern = pattern
        self.replacement = replacement

    def __eq__(self, other):
        return (other and self.__class__ is other.__class__
                and self.pattern == other.pattern
                and self.replacement == other.replacement)

    def __call__(self, tokens):
        pattern = self.pattern
        replacement = self.replacement

        for t in tokens:
            t.text = pattern.sub(replacement, t.text)
            yield t


# Analyzers

class Analyzer(Composable):
    """ Abstract base class for analyzers.
    """

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.__dict__ == other.__dict__)

    def __call__(self, value, **kwargs):
        raise NotImplementedError

    def clean(self):
        pass


class CompositeAnalyzer(Analyzer):
    def __init__(self, *composables):
        self.items = []
        for comp in composables:
            if isinstance(comp, CompositeAnalyzer):
                self.items.extend(comp.items)
            else:
                self.items.append(comp)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(repr(item) for item in self.items))

    def __call__(self, value, no_morph=False, **kwargs):
        items = self.items
        # Start with tokenizer
        gen = items[0](value, **kwargs)
        # Run filters
        for item in items[1:]:
            if not (no_morph and hasattr(item, "is_morph") and item.is_morph):
                gen = item(gen)
        return gen

    def __getitem__(self, item):
        return self.items.__getitem__(item)

    def __len__(self):
        return len(self.items)

    def __eq__(self, other):
        return (other
                and self.__class__ is other.__class__
                and self.items == other.items)

    def clean(self):
        for item in self.items:
            if hasattr(item, "clean"):
                item.clean()

    def has_morph(self):
        return any(item.is_morph for item in self.items)


def IDAnalyzer(lowercase=False):
    """Deprecated, just use an IDTokenizer directly, with a LowercaseFilter if
    desired.
    """

    tokenizer = IDTokenizer()
    if lowercase:
        tokenizer = tokenizer | LowercaseFilter()
    return tokenizer
IDAnalyzer.__inittypes__ = dict(lowercase=bool)


def KeywordAnalyzer(lowercase=False, commas=False):
    """Parses whitespace- or comma-separated tokens.
    
    >>> ana = KeywordAnalyzer()
    >>> [token.text for token in ana("Hello there, this is a TEST")]
    ["Hello", "there,", "this", "is", "a", "TEST"]
    
    :param lowercase: whether to lowercase the tokens.
    :param commas: if True, items are separated by commas rather than
        whitespace.
    """

    if commas:
        tokenizer = CommaSeparatedTokenizer()
    else:
        tokenizer = SpaceSeparatedTokenizer()
    if lowercase:
        tokenizer = tokenizer | LowercaseFilter()
    return tokenizer
KeywordAnalyzer.__inittypes__ = dict(lowercase=bool, commas=bool)


def RegexAnalyzer(expression=r"\w+(\.?\w+)*", gaps=False):
    """Deprecated, just use a RegexTokenizer directly.
    """

    return RegexTokenizer(expression=expression, gaps=gaps)
RegexAnalyzer.__inittypes__ = dict(expression=text_type, gaps=bool)


def SimpleAnalyzer(expression=default_pattern, gaps=False):
    """Composes a RegexTokenizer with a LowercaseFilter.
    
    >>> ana = SimpleAnalyzer()
    >>> [token.text for token in ana("Hello there, this is a TEST")]
    ["hello", "there", "this", "is", "a", "test"]
    
    :param expression: The regular expression pattern to use to extract tokens.
    :param gaps: If True, the tokenizer *splits* on the expression, rather
        than matching on the expression.
    """

    return RegexTokenizer(expression=expression, gaps=gaps) | LowercaseFilter()
SimpleAnalyzer.__inittypes__ = dict(expression=text_type, gaps=bool)


def StandardAnalyzer(expression=default_pattern, stoplist=STOP_WORDS,
                     minsize=2, maxsize=None, gaps=False):
    """Composes a RegexTokenizer with a LowercaseFilter and optional
    StopFilter.
    
    >>> ana = StandardAnalyzer()
    >>> [token.text for token in ana("Testing is testing and testing")]
    ["testing", "testing", "testing"]

    :param expression: The regular expression pattern to use to extract tokens.
    :param stoplist: A list of stop words. Set this to None to disable
        the stop word filter.
    :param minsize: Words smaller than this are removed from the stream.
    :param maxsize: Words longer that this are removed from the stream.
    :param gaps: If True, the tokenizer *splits* on the expression, rather
        than matching on the expression.
    """

    ret = RegexTokenizer(expression=expression, gaps=gaps)
    chain = ret | LowercaseFilter()
    if stoplist is not None:
        chain = chain | StopFilter(stoplist=stoplist, minsize=minsize,
                                   maxsize=maxsize)
    return chain
StandardAnalyzer.__inittypes__ = dict(expression=text_type, gaps=bool,
                                      stoplist=list, minsize=int, maxsize=int)


def StemmingAnalyzer(expression=default_pattern, stoplist=STOP_WORDS,
                     minsize=2, maxsize=None, gaps=False, stemfn=stem,
                     ignore=None, cachesize=50000):
    """Composes a RegexTokenizer with a lower case filter, an optional stop
    filter, and a stemming filter.
    
    >>> ana = StemmingAnalyzer()
    >>> [token.text for token in ana("Testing is testing and testing")]
    ["test", "test", "test"]
    
    :param expression: The regular expression pattern to use to extract tokens.
    :param stoplist: A list of stop words. Set this to None to disable
        the stop word filter.
    :param minsize: Words smaller than this are removed from the stream.
    :param maxsize: Words longer that this are removed from the stream.
    :param gaps: If True, the tokenizer *splits* on the expression, rather
        than matching on the expression.
    :param ignore: a set of words to not stem.
    :param cachesize: the maximum number of stemmed words to cache. The larger
        this number, the faster stemming will be but the more memory it will
        use.
    """

    ret = RegexTokenizer(expression=expression, gaps=gaps)
    chain = ret | LowercaseFilter()
    if stoplist is not None:
        chain = chain | StopFilter(stoplist=stoplist, minsize=minsize,
                                   maxsize=maxsize)
    return chain | StemFilter(stemfn=stemfn, ignore=ignore,
                              cachesize=cachesize)
StemmingAnalyzer.__inittypes__ = dict(expression=text_type, gaps=bool,
                                      stoplist=list, minsize=int, maxsize=int)


def FancyAnalyzer(expression=r"\s+", stoplist=STOP_WORDS, minsize=2,
                  maxsize=None, gaps=True, splitwords=True, splitnums=True,
                  mergewords=False, mergenums=False):
    """Composes a RegexTokenizer with an IntraWordFilter, LowercaseFilter, and
    StopFilter.
    
    >>> ana = FancyAnalyzer()
    >>> [token.text for token in ana("Should I call getInt or get_real?")]
    ["should", "call", "getInt", "get", "int", "get_real", "get", "real"]
    
    :param expression: The regular expression pattern to use to extract tokens.
    :param stoplist: A list of stop words. Set this to None to disable
        the stop word filter.
    :param minsize: Words smaller than this are removed from the stream.
    :param maxsize: Words longer that this are removed from the stream.
    :param gaps: If True, the tokenizer *splits* on the expression, rather
        than matching on the expression.
    """

    ret = RegexTokenizer(expression=expression, gaps=gaps)
    iwf = IntraWordFilter(splitwords=splitwords, splitnums=splitnums,
                          mergewords=mergewords, mergenums=mergenums)
    lcf = LowercaseFilter()
    swf = StopFilter(stoplist=stoplist, minsize=minsize)

    return ret | iwf | lcf | swf
FancyAnalyzer.__inittypes__ = dict(expression=text_type, gaps=bool,
                                   stoplist=list, minsize=int, maxsize=int)


def NgramAnalyzer(minsize, maxsize=None):
    """Composes an NgramTokenizer and a LowercaseFilter.
    
    >>> ana = NgramAnalyzer(4)
    >>> [token.text for token in ana("hi there")]
    ["hi t", "i th", " the", "ther", "here"]
    """

    return NgramTokenizer(minsize, maxsize=maxsize) | LowercaseFilter()
NgramAnalyzer.__inittypes__ = dict(minsize=int, maxsize=int)


def NgramWordAnalyzer(minsize, maxsize=None, tokenizer=None, at=None):
    if not tokenizer:
        tokenizer = RegexTokenizer()
    return tokenizer | LowercaseFilter() | NgramFilter(minsize, maxsize, at=at)


