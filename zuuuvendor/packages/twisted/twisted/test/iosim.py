# -*- test-case-name: twisted.test.test_amp.TLSTest -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Utilities and helpers for simulating a network
"""

import itertools

try:
    from OpenSSL.SSL import Error as NativeOpenSSLError
except ImportError:
    pass

from zope.interface import implements, directlyProvides

from twisted.python.failure import Failure
from twisted.internet import error
from twisted.internet import interfaces

class TLSNegotiation:
    def __init__(self, obj, connectState):
        self.obj = obj
        self.connectState = connectState
        self.sent = False
        self.readyToSend = connectState

    def __repr__(self):
        return 'TLSNegotiation(%r)' % (self.obj,)

    def pretendToVerify(self, other, tpt):
        # Set the transport problems list here?  disconnections?
        # hmmmmm... need some negative path tests.

        if not self.obj.iosimVerify(other.obj):
            tpt.disconnectReason = NativeOpenSSLError()
            tpt.loseConnection()


class FakeTransport:
    """
    A wrapper around a file-like object to make it behave as a Transport.

    This doesn't actually stream the file to the attached protocol,
    and is thus useful mainly as a utility for debugging protocols.
    """
    implements(interfaces.ITransport,
               interfaces.ITLSTransport) # ha ha not really

    _nextserial = itertools.count().next
    closed = 0
    disconnecting = 0
    disconnected = 0
    disconnectReason = error.ConnectionDone("Connection done")
    producer = None
    streamingProducer = 0
    tls = None

    def __init__(self):
        self.stream = []
        self.serial = self._nextserial()

    def __repr__(self):
        return 'FakeTransport<%s,%s,%s>' % (
            self.isServer and 'S' or 'C', self.serial,
            self.protocol.__class__.__name__)

    def write(self, data):
        if self.tls is not None:
            self.tlsbuf.append(data)
        else:
            self.stream.append(data)

    def _checkProducer(self):
        # Cheating; this is called at "idle" times to allow producers to be
        # found and dealt with
        if self.producer:
            self.producer.resumeProducing()

    def registerProducer(self, producer, streaming):
        """From abstract.FileDescriptor
        """
        self.producer = producer
        self.streamingProducer = streaming
        if not streaming:
            producer.resumeProducing()

    def unregisterProducer(self):
        self.producer = None

    def stopConsuming(self):
        self.unregisterProducer()
        self.loseConnection()

    def writeSequence(self, iovec):
        self.write("".join(iovec))

    def loseConnection(self):
        self.disconnecting = True

    def reportDisconnect(self):
        if self.tls is not None:
            # We were in the middle of negotiating!  Must have been a TLS problem.
            err = NativeOpenSSLError()
        else:
            err = self.disconnectReason
        self.protocol.connectionLost(Failure(err))

    def getPeer(self):
        # XXX: According to ITransport, this should return an IAddress!
        return 'file', 'file'

    def getHost(self):
        # XXX: According to ITransport, this should return an IAddress!
        return 'file'

    def resumeProducing(self):
        # Never sends data anyways
        pass

    def pauseProducing(self):
        # Never sends data anyways
        pass

    def stopProducing(self):
        self.loseConnection()

    def startTLS(self, contextFactory, beNormal=True):
        # Nothing's using this feature yet, but startTLS has an undocumented
        # second argument which defaults to true; if set to False, servers will
        # behave like clients and clients will behave like servers.
        connectState = self.isServer ^ beNormal
        self.tls = TLSNegotiation(contextFactory, connectState)
        self.tlsbuf = []

    def getOutBuffer(self):
        S = self.stream
        if S:
            self.stream = []
            return ''.join(S)
        elif self.tls is not None:
            if self.tls.readyToSend:
                # Only _send_ the TLS negotiation "packet" if I'm ready to.
                self.tls.sent = True
                return self.tls
            else:
                return None
        else:
            return None

    def bufferReceived(self, buf):
        if isinstance(buf, TLSNegotiation):
            assert self.tls is not None # By the time you're receiving a
                                        # negotiation, you have to have called
                                        # startTLS already.
            if self.tls.sent:
                self.tls.pretendToVerify(buf, self)
                self.tls = None # we're done with the handshake if we've gotten
                                # this far... although maybe it failed...?
                # TLS started!  Unbuffer...
                b, self.tlsbuf = self.tlsbuf, None
                self.writeSequence(b)
                directlyProvides(self, interfaces.ISSLTransport)
            else:
                # We haven't sent our own TLS negotiation: time to do that!
                self.tls.readyToSend = True
        else:
            self.protocol.dataReceived(buf)



def makeFakeClient(c):
    ft = FakeTransport()
    ft.isServer = False
    ft.protocol = c
    return ft

def makeFakeServer(s):
    ft = FakeTransport()
    ft.isServer = True
    ft.protocol = s
    return ft

class IOPump:
    """Utility to pump data between clients and servers for protocol testing.

    Perhaps this is a utility worthy of being in protocol.py?
    """
    def __init__(self, client, server, clientIO, serverIO, debug):
        self.client = client
        self.server = server
        self.clientIO = clientIO
        self.serverIO = serverIO
        self.debug = debug

    def flush(self, debug=False):
        """Pump until there is no more input or output.

        Returns whether any data was moved.
        """
        result = False
        for x in range(1000):
            if self.pump(debug):
                result = True
            else:
                break
        else:
            assert 0, "Too long"
        return result


    def pump(self, debug=False):
        """Move data back and forth.

        Returns whether any data was moved.
        """
        if self.debug or debug:
            print '-- GLUG --'
        sData = self.serverIO.getOutBuffer()
        cData = self.clientIO.getOutBuffer()
        self.clientIO._checkProducer()
        self.serverIO._checkProducer()
        if self.debug or debug:
            print '.'
            # XXX slightly buggy in the face of incremental output
            if cData:
                print 'C: '+repr(cData)
            if sData:
                print 'S: '+repr(sData)
        if cData:
            self.serverIO.bufferReceived(cData)
        if sData:
            self.clientIO.bufferReceived(sData)
        if cData or sData:
            return True
        if (self.serverIO.disconnecting and
            not self.serverIO.disconnected):
            if self.debug or debug:
                print '* C'
            self.serverIO.disconnected = True
            self.clientIO.disconnecting = True
            self.clientIO.reportDisconnect()
            return True
        if self.clientIO.disconnecting and not self.clientIO.disconnected:
            if self.debug or debug:
                print '* S'
            self.clientIO.disconnected = True
            self.serverIO.disconnecting = True
            self.serverIO.reportDisconnect()
            return True
        return False


def connectedServerAndClient(ServerClass, ClientClass,
                             clientTransportFactory=makeFakeClient,
                             serverTransportFactory=makeFakeServer,
                             debug=False):
    """Returns a 3-tuple: (client, server, pump)
    """
    c = ClientClass()
    s = ServerClass()
    cio = clientTransportFactory(c)
    sio = serverTransportFactory(s)
    c.makeConnection(cio)
    s.makeConnection(sio)
    pump = IOPump(c, s, cio, sio, debug)
    # kick off server greeting, etc
    pump.flush()
    return c, s, pump
