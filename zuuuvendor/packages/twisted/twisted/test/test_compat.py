# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Tests for L{twisted.python.compat}.
"""

import types, socket

from twisted.trial import unittest

from twisted.python.compat import set, frozenset, reduce



class IterableCounter:
    def __init__(self, lim=0):
        self.lim = lim
        self.i = -1

    def __iter__(self):
        return self

    def next(self):
        self.i += 1
        if self.i >= self.lim:
            raise StopIteration
        return self.i

class CompatTestCase(unittest.TestCase):
    def testDict(self):
        d1 = {'a': 'b'}
        d2 = dict(d1)
        self.assertEquals(d1, d2)
        d1['a'] = 'c'
        self.assertNotEquals(d1, d2)
        d2 = dict(d1.items())
        self.assertEquals(d1, d2)

    def testBool(self):
        self.assertEquals(bool('hi'), True)
        self.assertEquals(bool(True), True)
        self.assertEquals(bool(''), False)
        self.assertEquals(bool(False), False)

    def testIteration(self):
        lst1, lst2 = range(10), []

        for i in iter(lst1):
            lst2.append(i)
        self.assertEquals(lst1, lst2)
        del lst2[:]

        try:
            iterable = iter(lst1)
            while 1:
                lst2.append(iterable.next())
        except StopIteration:
            pass
        self.assertEquals(lst1, lst2)
        del lst2[:]

        for i in iter(IterableCounter(10)):
            lst2.append(i)
        self.assertEquals(lst1, lst2)
        del lst2[:]

        try:
            iterable = iter(IterableCounter(10))
            while 1:
                lst2.append(iterable.next())
        except StopIteration:
            pass
        self.assertEquals(lst1, lst2)
        del lst2[:]

        for i in iter(IterableCounter(20).next, 10):
            lst2.append(i)
        self.assertEquals(lst1, lst2)

    def testIsinstance(self):
        self.assert_(isinstance(u'hi', types.StringTypes))
        self.assert_(isinstance(self, unittest.TestCase))
        # I'm pretty sure it's impossible to implement this
        # without replacing isinstance on 2.2 as well :(
        # self.assert_(isinstance({}, dict))

    def testStrip(self):
        self.assertEquals(' x '.lstrip(' '), 'x ')
        self.assertEquals(' x x'.lstrip(' '), 'x x')
        self.assertEquals(' x '.rstrip(' '), ' x')
        self.assertEquals('x x '.rstrip(' '), 'x x')

        self.assertEquals('\t x '.lstrip('\t '), 'x ')
        self.assertEquals(' \tx x'.lstrip('\t '), 'x x')
        self.assertEquals(' x\t '.rstrip(' \t'), ' x')
        self.assertEquals('x x \t'.rstrip(' \t'), 'x x')

        self.assertEquals('\t x '.strip('\t '), 'x')
        self.assertEquals(' \tx x'.strip('\t '), 'x x')
        self.assertEquals(' x\t '.strip(' \t'), 'x')
        self.assertEquals('x x \t'.strip(' \t'), 'x x')

    def testNToP(self):
        from twisted.python.compat import inet_ntop

        f = lambda a: inet_ntop(socket.AF_INET6, a)
        g = lambda a: inet_ntop(socket.AF_INET, a)

        self.assertEquals('::', f('\x00' * 16))
        self.assertEquals('::1', f('\x00' * 15 + '\x01'))
        self.assertEquals(
            'aef:b01:506:1001:ffff:9997:55:170',
            f('\x0a\xef\x0b\x01\x05\x06\x10\x01\xff\xff\x99\x97\x00\x55\x01\x70'))

        self.assertEquals('1.0.1.0', g('\x01\x00\x01\x00'))
        self.assertEquals('170.85.170.85', g('\xaa\x55\xaa\x55'))
        self.assertEquals('255.255.255.255', g('\xff\xff\xff\xff'))

        self.assertEquals('100::', f('\x01' + '\x00' * 15))
        self.assertEquals('100::1', f('\x01' + '\x00' * 14 + '\x01'))

    def testPToN(self):
        from twisted.python.compat import inet_pton

        f = lambda a: inet_pton(socket.AF_INET6, a)
        g = lambda a: inet_pton(socket.AF_INET, a)

        self.assertEquals('\x00\x00\x00\x00', g('0.0.0.0'))
        self.assertEquals('\xff\x00\xff\x00', g('255.0.255.0'))
        self.assertEquals('\xaa\xaa\xaa\xaa', g('170.170.170.170'))

        self.assertEquals('\x00' * 16, f('::'))
        self.assertEquals('\x00' * 16, f('0::0'))
        self.assertEquals('\x00\x01' + '\x00' * 14, f('1::'))
        self.assertEquals(
            '\x45\xef\x76\xcb\x00\x1a\x56\xef\xaf\xeb\x0b\xac\x19\x24\xae\xae',
            f('45ef:76cb:1a:56ef:afeb:bac:1924:aeae'))

        self.assertEquals('\x00' * 14 + '\x00\x01', f('::1'))
        self.assertEquals('\x00' * 12 + '\x01\x02\x03\x04', f('::1.2.3.4'))
        self.assertEquals(
            '\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x01\x02\x03\xff',
            f('1:2:3:4:5:6:1.2.3.255'))

        for badaddr in ['1:2:3:4:5:6:7:8:', ':1:2:3:4:5:6:7:8', '1::2::3',
                        '1:::3', ':::', '1:2', '::1.2', '1.2.3.4::',
                        'abcd:1.2.3.4:abcd:abcd:abcd:abcd:abcd',
                        '1234:1.2.3.4:1234:1234:1234:1234:1234:1234',
                        '1.2.3.4']:
            self.assertRaises(ValueError, f, badaddr)

    def test_set(self):
        """
        L{set} should behave like the expected set interface.
        """
        a = set()
        a.add('b')
        a.add('c')
        a.add('a')
        b = list(a)
        b.sort()
        self.assertEquals(b, ['a', 'b', 'c'])
        a.remove('b')
        b = list(a)
        b.sort()
        self.assertEquals(b, ['a', 'c'])

        a.discard('d')

        b = set(['r', 's'])
        d = a.union(b)
        b = list(d)
        b.sort()
        self.assertEquals(b, ['a', 'c', 'r', 's'])


    def test_frozenset(self):
        """
        L{frozenset} should behave like the expected frozenset interface.
        """
        a = frozenset(['a', 'b'])
        self.assertRaises(AttributeError, getattr, a, "add")
        self.assertEquals(list(a), ['a', 'b'])

        b = frozenset(['r', 's'])
        d = a.union(b)
        b = list(d)
        b.sort()
        self.assertEquals(b, ['a', 'b', 'r', 's'])


    def test_reduce(self):
        """
        L{reduce} should behave like the builtin reduce.
        """
        self.assertEquals(15, reduce(lambda x, y: x + y, [1, 2, 3, 4, 5]))
        self.assertEquals(16, reduce(lambda x, y: x + y, [1, 2, 3, 4, 5], 1))
