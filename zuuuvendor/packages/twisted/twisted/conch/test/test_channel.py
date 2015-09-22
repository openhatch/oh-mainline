# Copyright (C) 2007-2008 Twisted Matrix Laboratories
# See LICENSE for details

"""
Test ssh/channel.py.
"""
from twisted.conch.ssh import channel
from twisted.trial import unittest


class MockTransport(object):
    """
    A mock Transport.  All we use is the getPeer() and getHost() methods.
    Channels implement the ITransport interface, and their getPeer() and
    getHost() methods return ('SSH', <transport's getPeer/Host value>) so
    we need to implement these methods so they have something to draw
    from.
    """
    def getPeer(self):
        return ('MockPeer',)

    def getHost(self):
        return ('MockHost',)


class MockConnection(object):
    """
    A mock for twisted.conch.ssh.connection.SSHConnection.  Record the data
    that channels send, and when they try to close the connection.

    @ivar data: a C{dict} mapping channel id #s to lists of data sent by that
        channel.
    @ivar extData: a C{dict} mapping channel id #s to lists of 2-tuples
        (extended data type, data) sent by that channel.
    @ivar closes: a C{dict} mapping channel id #s to True if that channel sent
        a close message.
    """
    transport = MockTransport()

    def __init__(self):
        self.data = {}
        self.extData = {}
        self.closes = {}

    def logPrefix(self):
        """
        Return our logging prefix.
        """
        return "MockConnection"

    def sendData(self, channel, data):
        """
        Record the sent data.
        """
        self.data.setdefault(channel, []).append(data)

    def sendExtendedData(self, channel, type, data):
        """
        Record the sent extended data.
        """
        self.extData.setdefault(channel, []).append((type, data))

    def sendClose(self, channel):
        """
        Record that the channel sent a close message.
        """
        self.closes[channel] = True


class ChannelTestCase(unittest.TestCase):

    def setUp(self):
        """
        Initialize the channel.  remoteMaxPacket is 10 so that data is able
        to be sent (the default of 0 means no data is sent because no packets
        are made).
        """
        self.conn = MockConnection()
        self.channel = channel.SSHChannel(conn=self.conn,
                remoteMaxPacket=10)
        self.channel.name = 'channel'

    def test_init(self):
        """
        Test that SSHChannel initializes correctly.  localWindowSize defaults
        to 131072 (2**17) and localMaxPacket to 32768 (2**15) as reasonable
        defaults (what OpenSSH uses for those variables).

        The values in the second set of assertions are meaningless; they serve
        only to verify that the instance variables are assigned in the correct
        order.
        """
        c = channel.SSHChannel(conn=self.conn)
        self.assertEquals(c.localWindowSize, 131072)
        self.assertEquals(c.localWindowLeft, 131072)
        self.assertEquals(c.localMaxPacket, 32768)
        self.assertEquals(c.remoteWindowLeft, 0)
        self.assertEquals(c.remoteMaxPacket, 0)
        self.assertEquals(c.conn, self.conn)
        self.assertEquals(c.data, None)
        self.assertEquals(c.avatar, None)

        c2 = channel.SSHChannel(1, 2, 3, 4, 5, 6, 7)
        self.assertEquals(c2.localWindowSize, 1)
        self.assertEquals(c2.localWindowLeft, 1)
        self.assertEquals(c2.localMaxPacket, 2)
        self.assertEquals(c2.remoteWindowLeft, 3)
        self.assertEquals(c2.remoteMaxPacket, 4)
        self.assertEquals(c2.conn, 5)
        self.assertEquals(c2.data, 6)
        self.assertEquals(c2.avatar, 7)

    def test_str(self):
        """
        Test that str(SSHChannel) works gives the channel name and local and
        remote windows at a glance..
        """
        self.assertEquals(str(self.channel), '<SSHChannel channel (lw 131072 '
                'rw 0)>')

    def test_logPrefix(self):
        """
        Test that SSHChannel.logPrefix gives the name of the channel, the
        local channel ID and the underlying connection.
        """
        self.assertEquals(self.channel.logPrefix(), 'SSHChannel channel '
                '(unknown) on MockConnection')

    def test_addWindowBytes(self):
        """
        Test that addWindowBytes adds bytes to the window and resumes writing
        if it was paused.
        """
        cb = [False]
        def stubStartWriting():
            cb[0] = True
        self.channel.startWriting = stubStartWriting
        self.channel.write('test')
        self.channel.writeExtended(1, 'test')
        self.channel.addWindowBytes(50)
        self.assertEquals(self.channel.remoteWindowLeft, 50 - 4 - 4)
        self.assertTrue(self.channel.areWriting)
        self.assertTrue(cb[0])
        self.assertEquals(self.channel.buf, '')
        self.assertEquals(self.conn.data[self.channel], ['test'])
        self.assertEquals(self.channel.extBuf, [])
        self.assertEquals(self.conn.extData[self.channel], [(1, 'test')])

        cb[0] = False
        self.channel.addWindowBytes(20)
        self.assertFalse(cb[0])

        self.channel.write('a'*80)
        self.channel.loseConnection()
        self.channel.addWindowBytes(20)
        self.assertFalse(cb[0])

    def test_requestReceived(self):
        """
        Test that requestReceived handles requests by dispatching them to
        request_* methods.
        """
        self.channel.request_test_method = lambda data: data == ''
        self.assertTrue(self.channel.requestReceived('test-method', ''))
        self.assertFalse(self.channel.requestReceived('test-method', 'a'))
        self.assertFalse(self.channel.requestReceived('bad-method', ''))

    def test_closeReceieved(self):
        """
        Test that the default closeReceieved closes the connection.
        """
        self.assertFalse(self.channel.closing)
        self.channel.closeReceived()
        self.assertTrue(self.channel.closing)

    def test_write(self):
        """
        Test that write handles data correctly.  Send data up to the size
        of the remote window, splitting the data into packets of length
        remoteMaxPacket.
        """
        cb = [False]
        def stubStopWriting():
            cb[0] = True
        # no window to start with
        self.channel.stopWriting = stubStopWriting
        self.channel.write('d')
        self.channel.write('a')
        self.assertFalse(self.channel.areWriting)
        self.assertTrue(cb[0])
        # regular write
        self.channel.addWindowBytes(20)
        self.channel.write('ta')
        data = self.conn.data[self.channel]
        self.assertEquals(data, ['da', 'ta'])
        self.assertEquals(self.channel.remoteWindowLeft, 16)
        # larger than max packet
        self.channel.write('12345678901')
        self.assertEquals(data, ['da', 'ta', '1234567890', '1'])
        self.assertEquals(self.channel.remoteWindowLeft, 5)
        # running out of window
        cb[0] = False
        self.channel.write('123456')
        self.assertFalse(self.channel.areWriting)
        self.assertTrue(cb[0])
        self.assertEquals(data, ['da', 'ta', '1234567890', '1', '12345'])
        self.assertEquals(self.channel.buf, '6')
        self.assertEquals(self.channel.remoteWindowLeft, 0)

    def test_writeExtended(self):
        """
        Test that writeExtended handles data correctly.  Send extended data
        up to the size of the window, splitting the extended data into packets
        of length remoteMaxPacket.
        """
        cb = [False]
        def stubStopWriting():
            cb[0] = True
        # no window to start with
        self.channel.stopWriting = stubStopWriting
        self.channel.writeExtended(1, 'd')
        self.channel.writeExtended(1, 'a')
        self.channel.writeExtended(2, 't')
        self.assertFalse(self.channel.areWriting)
        self.assertTrue(cb[0])
        # regular write
        self.channel.addWindowBytes(20)
        self.channel.writeExtended(2, 'a')
        data = self.conn.extData[self.channel]
        self.assertEquals(data, [(1, 'da'), (2, 't'), (2, 'a')])
        self.assertEquals(self.channel.remoteWindowLeft, 16)
        # larger than max packet
        self.channel.writeExtended(3, '12345678901')
        self.assertEquals(data, [(1, 'da'), (2, 't'), (2, 'a'),
            (3, '1234567890'), (3, '1')])
        self.assertEquals(self.channel.remoteWindowLeft, 5)
        # running out of window
        cb[0] = False
        self.channel.writeExtended(4, '123456')
        self.assertFalse(self.channel.areWriting)
        self.assertTrue(cb[0])
        self.assertEquals(data, [(1, 'da'), (2, 't'), (2, 'a'),
            (3, '1234567890'), (3, '1'), (4, '12345')])
        self.assertEquals(self.channel.extBuf, [[4, '6']])
        self.assertEquals(self.channel.remoteWindowLeft, 0)

    def test_writeSequence(self):
        """
        Test that writeSequence is equivalent to write(''.join(sequece)).
        """
        self.channel.addWindowBytes(20)
        self.channel.writeSequence(map(str, range(10)))
        self.assertEquals(self.conn.data[self.channel], ['0123456789'])

    def test_loseConnection(self):
        """
        Tesyt that loseConnection() doesn't close the channel until all
        the data is sent.
        """
        self.channel.write('data')
        self.channel.writeExtended(1, 'datadata')
        self.channel.loseConnection()
        self.assertEquals(self.conn.closes.get(self.channel), None)
        self.channel.addWindowBytes(4) # send regular data
        self.assertEquals(self.conn.closes.get(self.channel), None)
        self.channel.addWindowBytes(8) # send extended data
        self.assertTrue(self.conn.closes.get(self.channel))

    def test_getPeer(self):
        """
        Test that getPeer() returns ('SSH', <connection transport peer>).
        """
        self.assertEquals(self.channel.getPeer(), ('SSH', 'MockPeer'))

    def test_getHost(self):
        """
        Test that getHost() returns ('SSH', <connection transport host>).
        """
        self.assertEquals(self.channel.getHost(), ('SSH', 'MockHost'))
