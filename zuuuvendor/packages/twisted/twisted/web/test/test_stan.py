
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for L{twisted.web._stan} portion of the L{twisted.web.template}
implementation.
"""

from twisted.web.template import Comment, CDATA, Tag
from twisted.trial.unittest import TestCase

def proto(*a, **kw):
    """
    Produce a new tag for testing.
    """
    return Tag('hello')(*a, **kw)


class TestTag(TestCase):
    def test_cloneShallow(self):
        """
        L{Tag.clone} copies all attributes and children of a tag, including its
        render attribute.  If the shallow flag is C{False}, that's where it
        stops.
        """
        innerList = ["inner list"]
        tag = proto("How are you", innerList,
                    hello="world", render="aSampleMethod")
        tag.fillSlots(foo='bar')
        tag.filename = "foo/bar"
        tag.lineNumber = 6
        tag.columnNumber = 12
        clone = tag.clone(deep=False)
        self.assertEquals(clone.attributes['hello'], 'world')
        self.assertNotIdentical(clone.attributes, tag.attributes)
        self.assertEquals(clone.children, ["How are you", innerList])
        self.assertNotIdentical(clone.children, tag.children)
        self.assertIdentical(clone.children[1], innerList)
        self.assertEquals(tag.slotData, clone.slotData)
        self.assertNotIdentical(tag.slotData, clone.slotData)
        self.assertEqual(clone.filename, "foo/bar")
        self.assertEqual(clone.lineNumber, 6)
        self.assertEqual(clone.columnNumber, 12)
        self.assertEqual(clone.render, "aSampleMethod")


    def test_cloneDeep(self):
        """
        L{Tag.clone} copies all attributes and children of a tag, including its
        render attribute.  In its normal operating mode (where the deep flag is
        C{True}, as is the default), it will clone all sub-lists and sub-tags.
        """
        innerTag = proto("inner")
        innerList = ["inner list"]
        tag = proto("How are you", innerTag, innerList,
                    hello="world", render="aSampleMethod")
        tag.fillSlots(foo='bar')
        tag.filename = "foo/bar"
        tag.lineNumber = 6
        tag.columnNumber = 12
        clone = tag.clone()
        self.assertEquals(clone.attributes['hello'], 'world')
        self.assertNotIdentical(clone.attributes, tag.attributes)
        self.assertNotIdentical(clone.children, tag.children)
        # sanity check
        self.assertIdentical(tag.children[1], innerTag)
        # clone should have sub-clone
        self.assertNotIdentical(clone.children[1], innerTag)
        # sanity check
        self.assertIdentical(tag.children[2], innerList)
        # clone should have sub-clone
        self.assertNotIdentical(clone.children[2], innerList)
        self.assertEquals(tag.slotData, clone.slotData)
        self.assertNotIdentical(tag.slotData, clone.slotData)
        self.assertEqual(clone.filename, "foo/bar")
        self.assertEqual(clone.lineNumber, 6)
        self.assertEqual(clone.columnNumber, 12)
        self.assertEqual(clone.render, "aSampleMethod")


    def test_clear(self):
        """
        L{Tag.clear} removes all children from a tag, but leaves its attributes
        in place.
        """
        tag = proto("these are", "children", "cool", andSoIs='this-attribute')
        tag.clear()
        self.assertEquals(tag.children, [])
        self.assertEquals(tag.attributes, {'andSoIs': 'this-attribute'})


    def test_suffix(self):
        """
        L{Tag.__call__} accepts Python keywords with a suffixed underscore as
        the DOM attribute of that literal suffix.
        """
        proto = Tag('div')
        tag = proto()
        tag(class_='a')
        self.assertEquals(tag.attributes, {'class': 'a'})


    def test_commentRepr(self):
        """
        L{Comment.__repr__} returns a value which makes it easy to see what's in
        the comment.
        """
        self.assertEquals(repr(Comment(u"hello there")),
                          "Comment(u'hello there')")


    def test_cdataRepr(self):
        """
        L{CDATA.__repr__} returns a value which makes it easy to see what's in
        the comment.
        """
        self.assertEquals(repr(CDATA(u"test data")),
                          "CDATA(u'test data')")

