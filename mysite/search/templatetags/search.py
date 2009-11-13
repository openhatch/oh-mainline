# From <http://www.djangosnippets.org/snippets/661/>
#
# Copyright (c) 2009 Brian Beck
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from django import template
from django.conf import settings
from django.template import Node, TemplateSyntaxError
from django.utils.safestring import mark_safe
from django.utils.datastructures import SortedDict
from itertools import ifilter, takewhile
import re
from django.utils.html import escape


register = template.Library()

SETTINGS_PREFIX = 'SEARCH_'
SETTINGS_DEFAULTS = {
        'CONTEXT_WORDS': 10,
        'IGNORE_CASE': True,
        'WORD_BOUNDARY': False,
        'HIGHLIGHT_CLASS': "highlight"
        }

def get_setting(name):
    return getattr(settings, SETTINGS_PREFIX + name, SETTINGS_DEFAULTS[name])

def searchexcerpt(text, phrases, context_words=None, ignore_case=None, word_boundary=None):
    if isinstance(phrases, basestring):
        phrases = [phrases]
    if context_words is None:
        context_words = get_setting('CONTEXT_WORDS')
    if ignore_case is None:
        ignore_case = get_setting('IGNORE_CASE')
    if word_boundary is None:
        word_boundary = get_setting('WORD_BOUNDARY')

    phrases = map(re.escape, phrases)
    flags = ignore_case and re.I or 0
    exprs = [re.compile(r"^%s$" % p, flags) for p in phrases]
    whitespace = re.compile(r'\s+')

    re_template = word_boundary and r"\b(%s)\b" or r"(%s)"
    pieces = re.compile(re_template % "|".join(phrases), flags).split(text)
    matches = {}
    word_lists = []
    index = {}
    for i, piece in enumerate(pieces):
        word_lists.append(whitespace.split(piece))
        if i % 2:
            index[i] = expr = ifilter(lambda e: e.match(piece), exprs).next()
            matches.setdefault(expr, []).append(i)

    def merge(lists):
        merged = []
        for words in lists:
            if merged:
                merged[-1] += words[0]
                del words[0]
            merged.extend(words)
        return merged

    i = 0
    merged = []
    for j in map(min, matches.itervalues()):
        merged.append(merge(word_lists[i:j]))
        merged.append(word_lists[j])
        i = j + 1
    merged.append(merge(word_lists[i:]))

    output = []
    for i, words in enumerate(merged):
        omit = None
        if i == len(merged) - 1:
            omit = slice(max(1, 2 - i) * context_words + 1, None)
        elif i == 0:
            omit = slice(-context_words - 1)
        elif not i % 2:
            omit = slice(context_words + 1, -context_words - 1)
        if omit and words[omit]:
            words[omit] = ["..."]
        output.append(" ".join(words))

    return dict(original=text, excerpt="".join(output), hits=len(index))

class FunctionProxyNode(Node):
    def __init__(self, nodelist, args, variable_name=None):
        self.nodelist = nodelist
        self.args = args
        self.variable_name = variable_name

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        text = self.nodelist.render(context)
        value = self.get_value(text, *args)
        if self.variable_name:
            context[self.variable_name] = value
            return ""
        else:
            return self.string_value(value)

    def get_value(self, *args):
        raise NotImplementedError

    def string_value(self, value):
        return value

class SearchContextNode(FunctionProxyNode):
    def get_value(self, *args):
        return searchexcerpt(*args)

    def string_value(self, value):
        return value['excerpt']

@register.tag(name='searchexcerpt')
def searchexcerpt_tag(parser, token):
    """
        {% searchexcerpt search_terms [context_words] [ignore_case] [word_boundary] [as name] %}
        ...text...
        {% endsearchexcerpt %}
    """
    bits = list(token.split_contents())
    if not 3 <= len(bits) <= 8:
        usage = searchexcerpt_tag.__doc__.strip()
        raise TemplateSyntaxError("%r expected usage: %s" % (bits[0], usage))

    if len(bits) > 4 and bits[-2] == "as":
        args, name = bits[1:-2], bits[-1]
    else:
        args, name = bits[1:], None

    nodelist = parser.parse(('endsearchexcerpt',))
    parser.delete_first_token()
    return SearchContextNode(nodelist, map(parser.compile_filter, args), name)

@register.filter(name='searchexcerpt')
def searchexcerpt_filter(value, arg):
    return searchexcerpt(value, arg)['excerpt']
searchexcerpt_filter.is_safe = True

def highlight(text, phrases, ignore_case=None, word_boundary=None, class_name=None):
    if isinstance(phrases, basestring):
        phrases = [phrases]
    if ignore_case is None:
        ignore_case = get_setting('IGNORE_CASE')
    if word_boundary is None:
        word_boundary = get_setting('WORD_BOUNDARY')
    if class_name is None:
        class_name = get_setting('HIGHLIGHT_CLASS')

    phrases = map(re.escape, phrases)
    flags = ignore_case and re.I or 0
    re_template = word_boundary and r"\b(%s)\b" or r"(%s)"
    expr = re.compile(re_template % "|".join(phrases), flags)
    template = '<span class="%s">%%s</span>' % class_name
    matches = []

    def replace(match):
        matches.append(match)
        return template % match.group(0)

    # Brian Beck's code reads:
    #highlighted = mark_safe(expr.sub(replace, text))
    # We changed this to:
    highlighted = mark_safe(expr.sub(replace, escape(text)))
    count = len(matches)
    return dict(original=text, highlighted=highlighted, hits=count)

class HighlightNode(FunctionProxyNode):
    def get_value(self, *args):
        return highlight(*args)

    def string_value(self, value):
        return value['highlighted']

@register.tag(name='highlight')
def highlight_tag(parser, token):
    """
        {% highlight search_terms [ignore_case] [word_boundary] [class_name] [as name] %}
        ...text...
        {% endhighlight %}
    """
    bits = list(token.split_contents())
    if not 2 <= len(bits) <= 7:
        usage = highlight_tag.__doc__.strip()
        raise TemplateSyntaxError("%r expected usage: %s" % (bits[0], usage))

    if len(bits) > 3 and bits[-2] == "as":
        args, name = bits[1:-2], bits[-1]
    else:
        args, name = bits[1:], None

    nodelist = parser.parse(('endhighlight',))
    parser.delete_first_token()
    return HighlightNode(nodelist, map(parser.compile_filter, args), name)

@register.filter(name='highlight')
def highlight_filter(value, arg):
    return highlight(value, arg)['highlighted']

def hits(text, phrases, ignore_case=None, word_boundary=None):
    if isinstance(phrases, basestring):
        phrases = [phrases]
    if ignore_case is None:
        ignore_case = get_setting('IGNORE_CASE')
    if word_boundary is None:
        word_boundary = get_setting('WORD_BOUNDARY')    

    phrases = map(re.escape, phrases)
    flags = ignore_case and re.I or 0
    re_template = word_boundary and r"\b(%s)\b" or r"(%s)"
    expr = re.compile(re_template % "|".join(phrases), flags)
    return len(expr.findall(text))

class HitsNode(FunctionProxyNode):
    def get_value(self, *args):
        return hits(*args)

    def string_value(self, value):
        return "%d" % value

@register.tag(name='hits')
def hits_tag(parser, token):
    """
        {% hits search_terms [ignore_case] [word_boundary] [as name] %}
        ...text...
        {% endhits %}
    """
    bits = list(token.split_contents())
    if not 2 <= len(bits) <= 6:
        usage = hits_tag.__doc__.strip()
        raise TemplateSyntaxError("%r expected usage: %s" % (bits[0], usage))

    if len(bits) > 3 and bits[-2] == "as":
        args, name = bits[1:-2], bits[-1]
    else:
        args, name = bits[1:], None

    nodelist = parser.parse(('endhits',))
    parser.delete_first_token()
    return HitsNode(nodelist, map(parser.compile_filter, args), name)

@register.filter(name='hits')
def hits_filter(value, arg):
    return hits(value, arg)
hits.is_safe = True
