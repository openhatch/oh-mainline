# -*- test-case-name: twisted.web.test.test_template -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


"""
HTML rendering for twisted.web.

@var VALID_HTML_TAG_NAMES: A list of recognized HTML tag names, used by the
    L{tag} object.

@var TEMPLATE_NAMESPACE: The XML namespace used to identify attributes and
    elements used by the templating system, which should be removed from the
    final output document.

@var tags: A convenience object which can produce L{Tag} objects on demand via
    attribute access.  For example: C{tags.div} is equivalent to C{Tag("div")}.
    Tags not specified in L{VALID_HTML_TAG_NAMES} will result in an
    L{AttributeError}.
"""

from zope.interface import implements

from cStringIO import StringIO
from xml.sax import make_parser, handler

from twisted.web._stan import Tag, slot, Comment, CDATA

TEMPLATE_NAMESPACE = 'http://twistedmatrix.com/ns/twisted.web.template/0.1'

from twisted.web.iweb import ITemplateLoader

class _NSContext(object):
    """
    A mapping from XML namespaces onto their prefixes in the document.
    """

    def __init__(self, parent=None):
        """
        Pull out the parent's namespaces, if there's no parent then default to
        XML.
        """
        self.parent = parent
        if parent is not None:
            self.nss = dict(parent.nss)
        else:
            self.nss = {'http://www.w3.org/XML/1998/namespace':'xml'}


    def get(self, k, d=None):
        """
        Get a prefix for a namespace.

        @param d: The default prefix value.
        """
        return self.nss.get(k, d)


    def __setitem__(self, k, v):
        """
        Proxy through to setting the prefix for the namespace.
        """
        self.nss.__setitem__(k, v)


    def __getitem__(self, k):
        """
        Proxy through to getting the prefix for the namespace.
        """
        return self.nss.__getitem__(k)



class _ToStan(handler.ContentHandler, handler.EntityResolver):
    """
    A SAX parser which converts an XML document to the Twisted STAN
    Document Object Model.
    """

    def __init__(self, sourceFilename):
        """
        @param sourceFilename: the filename to load the XML out of.
        """
        self.sourceFilename = sourceFilename
        self.prefixMap = _NSContext()
        self.inCDATA = False


    def setDocumentLocator(self, locator):
        """
        Set the document locator, which knows about line and character numbers.
        """
        self.locator = locator


    def startDocument(self):
        """
        Initialise the document.
        """
        self.document = []
        self.current = self.document
        self.stack = []
        self.xmlnsAttrs = []


    def endDocument(self):
        """
        Document ended.
        """


    def processingInstruction(self, target, data):
        """
        Processing instructions are ignored.
        """


    def startPrefixMapping(self, prefix, uri):
        """
        Set up the prefix mapping, which maps fully qualified namespace URIs
        onto namespace prefixes.

        This gets called before startElementNS whenever an C{xmlns} attribute
        is seen.
        """

        self.prefixMap = _NSContext(self.prefixMap)
        self.prefixMap[uri] = prefix

        # Ignore the template namespace; we'll replace those during parsing.
        if uri == TEMPLATE_NAMESPACE:
            return

        # Add to a list that will be applied once we have the element.
        if prefix is None:
            self.xmlnsAttrs.append(('xmlns',uri))
        else:
            self.xmlnsAttrs.append(('xmlns:%s'%prefix,uri))


    def endPrefixMapping(self, prefix):
        """
        "Pops the stack" on the prefix mapping.

        Gets called after endElementNS.
        """
        self.prefixMap = self.prefixMap.parent


    def startElementNS(self, namespaceAndName, qname, attrs):
        """
        Gets called when we encounter a new xmlns attribute.

        @param namespaceAndName: a (namespace, name) tuple, where name
            determines which type of action to take, if the namespace matches
            L{TEMPLATE_NAMESPACE}.
        @param qname: ignored.
        @param attrs: attributes on the element being started.
        """

        filename = self.sourceFilename
        lineNumber = self.locator.getLineNumber()
        columnNumber = self.locator.getColumnNumber()

        ns, name = namespaceAndName
        if ns == TEMPLATE_NAMESPACE:
            if name == 'transparent':
                name = ''
            elif name == 'slot':
                try:
                    # Try to get the default value for the slot
                    default = attrs[(None, 'default')]
                except KeyError:
                    # If there wasn't one, then use None to indicate no
                    # default.
                    default = None
                el = slot(
                    attrs[(None, 'name')], default=default,
                    filename=filename, lineNumber=lineNumber,
                    columnNumber=columnNumber)
                self.stack.append(el)
                self.current.append(el)
                self.current = el.children
                return

        render = None

        attrs = dict(attrs)
        for k, v in attrs.items():
            attrNS, justTheName = k
            if attrNS != TEMPLATE_NAMESPACE:
                continue
            if justTheName == 'render':
                render = v
                del attrs[k]

        # nonTemplateAttrs is a dictionary mapping attributes that are *not* in
        # TEMPLATE_NAMESPACE to their values.  Those in TEMPLATE_NAMESPACE were
        # just removed from 'attrs' in the loop immediately above.  The key in
        # nonTemplateAttrs is either simply the attribute name (if it was not
        # specified as having a namespace in the template) or prefix:name,
        # preserving the xml namespace prefix given in the document.

        nonTemplateAttrs = {}
        for (attrNs, attrName), v in attrs.items():
            nsPrefix = self.prefixMap.get(attrNs)
            if nsPrefix is None:
                attrKey = attrName
            else:
                attrKey = '%s:%s' % (nsPrefix, attrName)
            nonTemplateAttrs[attrKey] = v

        if ns == TEMPLATE_NAMESPACE and name == 'attr':
            if not self.stack:
                # TODO: define a better exception for this?
                raise AssertionError(
                    '<{%s}attr> as top-level element' % (TEMPLATE_NAMESPACE,))
            if 'name' not in nonTemplateAttrs:
                # TODO: same here
                raise AssertionError(
                    '<{%s}attr> requires a name attribute' % (TEMPLATE_NAMESPACE,))
            el = Tag('', render=render, filename=filename,
                     lineNumber=lineNumber, columnNumber=columnNumber)
            self.stack[-1].attributes[nonTemplateAttrs['name']] = el
            self.stack.append(el)
            self.current = el.children
            return

        # Apply any xmlns attributes
        if self.xmlnsAttrs:
            nonTemplateAttrs.update(dict(self.xmlnsAttrs))
            self.xmlnsAttrs = []

        # Add the prefix that was used in the parsed template for non-template
        # namespaces (which will not be consumed anyway).
        if ns != TEMPLATE_NAMESPACE and ns is not None:
            prefix = self.prefixMap[ns]
            if prefix is not None:
                name = '%s:%s' % (self.prefixMap[ns],name)
        el = Tag(
            name, attributes=dict(nonTemplateAttrs), render=render,
            filename=filename, lineNumber=lineNumber,
            columnNumber=columnNumber)
        self.stack.append(el)
        self.current.append(el)
        self.current = el.children


    def characters(self, ch):
        """
        Called when we receive some characters.  CDATA characters get passed
        through as is.

        @type ch: C{string}
        """
        if self.inCDATA:
            self.stack[-1].append(ch)
            return
        self.current.append(ch)


    def endElementNS(self, name, qname):
        """
        A namespace tag is closed.  Pop the stack, if there's anything left in
        it, otherwise return to the document's namespace.
        """
        self.stack.pop()
        if self.stack:
            self.current = self.stack[-1].children
        else:
            self.current = self.document


    def startDTD(self, name, publicId, systemId):
        """
        DTDs are ignored.
        """


    def endDTD(self, *args):
        """
        DTDs are ignored.
        """


    def startCDATA(self):
        """
        We're starting to be in a CDATA element, make a note of this.
        """
        self.inCDATA = True
        self.stack.append([])


    def endCDATA(self):
        """
        We're no longer in a CDATA element.  Collect up the characters we've
        parsed and put them in a new CDATA object.
        """
        self.inCDATA = False
        comment = ''.join(self.stack.pop())
        self.current.append(CDATA(comment))


    def comment(self, content):
        """
        Add an XML comment which we've encountered.
        """
        self.current.append(Comment(content))



def _flatsaxParse(fl):
    """
    Perform a SAX parse of an XML document with the _ToStan class.

    @param fl: The XML document to be parsed.
    """
    parser = make_parser()
    parser.setFeature(handler.feature_validation, 0)
    parser.setFeature(handler.feature_namespaces, 1)
    parser.setFeature(handler.feature_external_ges, 0)
    parser.setFeature(handler.feature_external_pes, 0)

    s = _ToStan(getattr(fl, "name", None))
    parser.setContentHandler(s)
    parser.setEntityResolver(s)
    parser.setProperty(handler.property_lexical_handler, s)

    parser.parse(fl)

    return s.document


class XMLString(object):
    """
    An L{ITemplateLoader} that loads and parses XML from a string.

    @type s: C{string}
    @param s: The string from which to load the XML.
    """
    implements(ITemplateLoader)

    def __init__(self, s):
        """
        Run the parser on a StringIO copy of the string.
        """
        self._loadedTemplate = _flatsaxParse(StringIO(s))


    def load(self):
        return self._loadedTemplate



class XMLFile(object):
    """
    An L{ITemplateLoader} that loads and parses XML from a file.

    @type fobj: file object
    @param fobj: The file object from which to load the XML.
    """
    implements(ITemplateLoader)

    def __init__(self, fobj):
        self._loadDoc = lambda: _flatsaxParse(fobj)
        self._loadedTemplate = None


    def load(self):
        """
        Load the document if it's not already loaded.
        """
        if self._loadedTemplate is None:
            self._loadedTemplate = self._loadDoc()
        return self._loadedTemplate



VALID_HTML_TAG_NAMES = set([
    'a', 'abbr', 'acronym', 'address', 'applet', 'area', 'b', 'base',
    'basefont', 'bdo', 'big', 'blockquote', 'body', 'br', 'button', 'caption',
    'center', 'cite', 'code', 'col', 'colgroup', 'dd', 'del', 'dfn', 'dir',
    'div', 'dl', 'dt', 'em', 'fieldset', 'font', 'form', 'frame', 'frameset',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'hr', 'html', 'i', 'iframe',
    'img', 'input', 'ins', 'isindex', 'kbd', 'label', 'legend', 'li', 'link',
    'map', 'menu', 'meta', 'noframes', 'noscript', 'object', 'ol', 'optgroup',
    'option', 'p', 'param', 'pre', 'q', 's', 'samp', 'script', 'select',
    'small', 'span', 'strike', 'strong', 'style', 'sub', 'sup', 'table',
    'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'title', 'tr', 'tt', 'u',
    'ul', 'var'
])



class _TagFactory(object):
    """
    A factory for L{Tag} objects; the implementation of the L{tags} object.

    This allows for the syntactic convenience of C{from twisted.web.html import
    tags; tags.a(href="linked-page.html")}, where 'a' can be basically any HTML
    tag.

    The class is not exposed publicly because you only ever need one of these,
    and we already made it for you.

    @see: L{tags}
    """
    def __getattr__(self, tagName):
        if tagName == 'transparent':
            return Tag('')
        # allow for E.del as E.del_
        tagName = tagName.rstrip('_')
        if tagName not in VALID_HTML_TAG_NAMES:
            raise AttributeError('unknown tag %r' % (tagName,))
        return Tag(tagName)



tags = _TagFactory()



from twisted.web._element import Element, renderer
from twisted.web._flatten import flatten, flattenString

__all__ = [
    'TEMPLATE_NAMESPACE', 'VALID_HTML_TAG_NAMES', 'Element', 'renderer',
    'flatten', 'flattenString', 'tags', 'Comment', 'CDATA', 'Tag', 'slot'
]

