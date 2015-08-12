# -*- coding: utf-8 -*-
"""
    sphinx.search
    ~~~~~~~~~~~~~

    Create a full-text search index for offline search.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import with_statement
import re
import itertools
import cPickle as pickle

from docutils.nodes import comment, title, Text, NodeVisitor, SkipNode

from sphinx.util import jsdump, rpartition


class SearchLanguage(object):
    """
    This class is the base class for search natural language preprocessors.  If
    you want to add support for a new language, you should override the methods
    of this class.

    You should override `lang` class property too (e.g. 'en', 'fr' and so on).

    .. attribute:: stopwords

       This is a set of stop words of the target language.  Default `stopwords`
       is empty.  This word is used for building index and embedded in JS.

    .. attribute:: js_stemmer_code

       Return stemmer class of JavaScript version.  This class' name should be
       ``Stemmer`` and this class must have ``stemWord`` method.  This string is
       embedded as-is in searchtools.js.

       This class is used to preprocess search word which Sphinx HTML readers
       type, before searching index. Default implementation does nothing.
    """
    lang = None
    stopwords = set()
    js_stemmer_code = """
/**
 * Dummy stemmer for languages without stemming rules.
 */
var Stemmer = function() {
  this.stemWord = function(w) {
    return w;
  }
}
"""

    _word_re = re.compile(r'\w+(?u)')

    def __init__(self, options):
        self.options = options
        self.init(options)

    def init(self, options):
        """
        Initialize the class with the options the user has given.
        """

    def split(self, input):
        """
        This method splits a sentence into words.  Default splitter splits input
        at white spaces, which should be enough for most languages except CJK
        languages.
        """
        return self._word_re.findall(input)

    def stem(self, word):
        """
        This method implements stemming algorithm of the Python version.

        Default implementation does nothing.  You should implement this if the
        language has any stemming rules.

        This class is used to preprocess search words before registering them in
        the search index.  The stemming of the Python version and the JS version
        (given in the js_stemmer_code attribute) must be compatible.
        """
        return word

    def word_filter(self, word):
        """
        Return true if the target word should be registered in the search index.
        This method is called after stemming.
        """
        return not (((len(word) < 3) and (12353 < ord(word[0]) < 12436)) or
            (ord(word[0]) < 256 and (len(word) < 3 or word in self.stopwords or
                                     word.isdigit())))


from sphinx.search import en, ja

languages = {
    'en': en.SearchEnglish,
    'ja': ja.SearchJapanese,
}


class _JavaScriptIndex(object):
    """
    The search index as javascript file that calls a function
    on the documentation search object to register the index.
    """

    PREFIX = 'Search.setIndex('
    SUFFIX = ')'

    def dumps(self, data):
        return self.PREFIX + jsdump.dumps(data) + self.SUFFIX

    def loads(self, s):
        data = s[len(self.PREFIX):-len(self.SUFFIX)]
        if not data or not s.startswith(self.PREFIX) or not \
           s.endswith(self.SUFFIX):
            raise ValueError('invalid data')
        return jsdump.loads(data)

    def dump(self, data, f):
        f.write(self.dumps(data))

    def load(self, f):
        return self.loads(f.read())


js_index = _JavaScriptIndex()


class WordCollector(NodeVisitor):
    """
    A special visitor that collects words for the `IndexBuilder`.
    """

    def __init__(self, document, lang):
        NodeVisitor.__init__(self, document)
        self.found_words = []
        self.found_title_words = []
        self.lang = lang

    def dispatch_visit(self, node):
        if node.__class__ is comment:
            raise SkipNode
        elif node.__class__ is Text:
            self.found_words.extend(self.lang.split(node.astext()))
        elif node.__class__ is title:
            self.found_title_words.extend(self.lang.split(node.astext()))


class IndexBuilder(object):
    """
    Helper class that creates a searchindex based on the doctrees
    passed to the `feed` method.
    """
    formats = {
        'jsdump':   jsdump,
        'pickle':   pickle
    }

    def __init__(self, env, lang, options, scoring):
        self.env = env
        # filename -> title
        self._titles = {}
        # stemmed word -> set(filenames)
        self._mapping = {}
        # stemmed words in titles -> set(filenames)
        self._title_mapping = {}
        # word -> stemmed word
        self._stem_cache = {}
        # objtype -> index
        self._objtypes = {}
        # objtype index -> (domain, type, objname (localized))
        self._objnames = {}
        # add language-specific SearchLanguage instance
        self.lang = languages[lang](options)

        if scoring:
            with open(scoring, 'rb') as fp:
                self.js_scorer_code = fp.read().decode('utf-8')
        else:
            self.js_scorer_code = u''

    def load(self, stream, format):
        """Reconstruct from frozen data."""
        if isinstance(format, basestring):
            format = self.formats[format]
        frozen = format.load(stream)
        # if an old index is present, we treat it as not existing.
        if not isinstance(frozen, dict) or \
           frozen.get('envversion') != self.env.version:
            raise ValueError('old format')
        index2fn = frozen['filenames']
        self._titles = dict(zip(index2fn, frozen['titles']))

        def load_terms(mapping):
            rv = {}
            for k, v in mapping.iteritems():
                if isinstance(v, int):
                    rv[k] = set([index2fn[v]])
                else:
                    rv[k] = set(index2fn[i] for i in v)
            return rv

        self._mapping = load_terms(frozen['terms'])
        self._title_mapping = load_terms(frozen['titleterms'])
        # no need to load keywords/objtypes

    def dump(self, stream, format):
        """Dump the frozen index to a stream."""
        if isinstance(format, basestring):
            format = self.formats[format]
        format.dump(self.freeze(), stream)

    def get_objects(self, fn2index):
        rv = {}
        otypes = self._objtypes
        onames = self._objnames
        for domainname, domain in self.env.domains.iteritems():
            for fullname, dispname, type, docname, anchor, prio in \
                    domain.get_objects():
                # XXX use dispname?
                if docname not in fn2index:
                    continue
                if prio < 0:
                    continue
                prefix, name = rpartition(fullname, '.')
                pdict = rv.setdefault(prefix, {})
                try:
                    typeindex = otypes[domainname, type]
                except KeyError:
                    typeindex = len(otypes)
                    otypes[domainname, type] = typeindex
                    otype = domain.object_types.get(type)
                    if otype:
                        # use unicode() to fire translation proxies
                        onames[typeindex] = (domainname, type,
                            unicode(domain.get_type_name(otype)))
                    else:
                        onames[typeindex] = (domainname, type, type)
                if anchor == fullname:
                    shortanchor = ''
                elif anchor == type + '-' + fullname:
                    shortanchor = '-'
                else:
                    shortanchor = anchor
                pdict[name] = (fn2index[docname], typeindex, prio, shortanchor)
        return rv

    def get_terms(self, fn2index):
        rvs = {}, {}
        for rv, mapping in zip(rvs, (self._mapping, self._title_mapping)):
            for k, v in mapping.iteritems():
                if len(v) == 1:
                    fn, = v
                    if fn in fn2index:
                        rv[k] = fn2index[fn]
                else:
                    rv[k] = [fn2index[fn] for fn in v if fn in fn2index]
        return rvs

    def freeze(self):
        """Create a usable data structure for serializing."""
        filenames = self._titles.keys()
        titles = self._titles.values()
        fn2index = dict((f, i) for (i, f) in enumerate(filenames))
        terms, title_terms = self.get_terms(fn2index)

        objects = self.get_objects(fn2index)  # populates _objtypes
        objtypes = dict((v, k[0] + ':' + k[1])
                        for (k, v) in self._objtypes.iteritems())
        objnames = self._objnames
        return dict(filenames=filenames, titles=titles, terms=terms,
                    objects=objects, objtypes=objtypes, objnames=objnames,
                    titleterms=title_terms, envversion=self.env.version)

    def prune(self, filenames):
        """Remove data for all filenames not in the list."""
        new_titles = {}
        for filename in filenames:
            if filename in self._titles:
                new_titles[filename] = self._titles[filename]
        self._titles = new_titles
        for wordnames in self._mapping.itervalues():
            wordnames.intersection_update(filenames)
        for wordnames in self._title_mapping.itervalues():
            wordnames.intersection_update(filenames)

    def feed(self, filename, title, doctree):
        """Feed a doctree to the index."""
        self._titles[filename] = title

        visitor = WordCollector(doctree, self.lang)
        doctree.walk(visitor)

        # memoize self.lang.stem
        def stem(word):
            try:
                return self._stem_cache[word]
            except KeyError:
                self._stem_cache[word] = self.lang.stem(word)
                return self._stem_cache[word]
        _filter =  self.lang.word_filter

        for word in itertools.chain(visitor.found_title_words,
                                    self.lang.split(title)):
            word = stem(word)
            if _filter(word):
                self._title_mapping.setdefault(word, set()).add(filename)

        for word in visitor.found_words:
            word = stem(word)
            if word not in self._title_mapping and _filter(word):
                self._mapping.setdefault(word, set()).add(filename)

    def context_for_searchtool(self):
        return dict(
            search_language_stemming_code = self.lang.js_stemmer_code,
            search_language_stop_words =
                jsdump.dumps(sorted(self.lang.stopwords)),
            search_scorer_tool = self.js_scorer_code,
        )
