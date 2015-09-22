# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.trial import unittest

from twisted.words.protocols.jabber.xmpp_stringprep import nodeprep, resourceprep, nameprep, crippled

class XMPPStringPrepTest(unittest.TestCase):
    """

    The nodeprep stringprep profile is similar to the resourceprep profile,
    but does an extra mapping of characters (table B.2) and disallows
    more characters (table C.1.1 and eight extra punctuation characters).
    Due to this similarity, the resourceprep tests are more extensive, and
    the nodeprep tests only address the mappings additional restrictions.

    The nameprep profile is nearly identical to the nameprep implementation in
    L{encodings.idna}, but that implementation assumes the C{UseSTD4ASCIIRules}
    flag to be false. This implementation assumes it to be true, and restricts
    the allowed set of characters.  The tests here only check for the
    differences.
    
    """

    def testResourcePrep(self):
        self.assertEquals(resourceprep.prepare(u'resource'), u'resource')
        self.assertNotEquals(resourceprep.prepare(u'Resource'), u'resource')
        self.assertEquals(resourceprep.prepare(u' '), u' ')

        if crippled:
            return

        self.assertEquals(resourceprep.prepare(u'Henry \u2163'), u'Henry IV')
        self.assertEquals(resourceprep.prepare(u'foo\xad\u034f\u1806\u180b'
                                               u'bar\u200b\u2060'
                                               u'baz\ufe00\ufe08\ufe0f\ufeff'),
                          u'foobarbaz')
        self.assertEquals(resourceprep.prepare(u'\u00a0'), u' ')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u1680')
        self.assertEquals(resourceprep.prepare(u'\u2000'), u' ')
        self.assertEquals(resourceprep.prepare(u'\u200b'), u'')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u0010\u007f')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u0085')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u180e')
        self.assertEquals(resourceprep.prepare(u'\ufeff'), u'')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\uf123')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\U000f1234')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\U0010f234')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\U0008fffe')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\U0010ffff')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\udf42')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\ufffd')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u2ff5')
        self.assertEquals(resourceprep.prepare(u'\u0341'), u'\u0301')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u200e')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u202a')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\U000e0001')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\U000e0042')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'foo\u05bebar')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'foo\ufd50bar')
        #self.assertEquals(resourceprep.prepare(u'foo\ufb38bar'),
        #                  u'foo\u064ebar')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\u06271')
        self.assertEquals(resourceprep.prepare(u'\u06271\u0628'),
                          u'\u06271\u0628')
        self.assertRaises(UnicodeError, resourceprep.prepare, u'\U000e0002')

    def testNodePrep(self):
        self.assertEquals(nodeprep.prepare(u'user'), u'user')
        self.assertEquals(nodeprep.prepare(u'User'), u'user')
        self.assertRaises(UnicodeError, nodeprep.prepare, u'us&er')


    def test_nodeprepUnassignedInUnicode32(self):
        """
        Make sure unassigned code points from Unicode 3.2 are rejected.
        """
        self.assertRaises(UnicodeError, nodeprep.prepare, u'\u1d39')


    def testNamePrep(self):
        self.assertEquals(nameprep.prepare(u'example.com'), u'example.com')
        self.assertEquals(nameprep.prepare(u'Example.com'), u'example.com')
        self.assertRaises(UnicodeError, nameprep.prepare, u'ex@mple.com')
        self.assertRaises(UnicodeError, nameprep.prepare, u'-example.com')
        self.assertRaises(UnicodeError, nameprep.prepare, u'example-.com')

        if crippled:
            return

        self.assertEquals(nameprep.prepare(u'stra\u00dfe.example.com'),
                          u'strasse.example.com')
