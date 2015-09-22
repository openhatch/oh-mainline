# -*- test-case-name: twisted.test.test_internet -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Select reactor

Maintainer: Itamar Shtull-Trauring
"""

from time import sleep
import sys
import select
from errno import EINTR, EBADF

from zope.interface import implements

from twisted.internet.interfaces import IReactorFDSet
from twisted.internet import error
from twisted.internet import posixbase
from twisted.python import log
from twisted.python.runtime import platformType


def win32select(r, w, e, timeout=None):
    """Win32 select wrapper."""
    if not (r or w):
        # windows select() exits immediately when no sockets
        if timeout is None:
            timeout = 0.01
        else:
            timeout = min(timeout, 0.001)
        sleep(timeout)
        return [], [], []
    # windows doesn't process 'signals' inside select(), so we set a max
    # time or ctrl-c will never be recognized
    if timeout is None or timeout > 0.5:
        timeout = 0.5
    r, w, e = select.select(r, w, w, timeout)
    return r, w + e, []

if platformType == "win32":
    _select = win32select
else:
    _select = select.select

# Exceptions that doSelect might return frequently
_NO_FILENO = error.ConnectionFdescWentAway('Handler has no fileno method')
_NO_FILEDESC = error.ConnectionFdescWentAway('Filedescriptor went away')

class SelectReactor(posixbase.PosixReactorBase):
    """
    A select() based reactor - runs on all POSIX platforms and on Win32.

    @ivar _reads: A dictionary mapping L{FileDescriptor} instances to arbitrary
        values (this is essentially a set).  Keys in this dictionary will be
        checked for read events.

    @ivar _writes: A dictionary mapping L{FileDescriptor} instances to
        arbitrary values (this is essentially a set).  Keys in this dictionary
        will be checked for writability.
    """
    implements(IReactorFDSet)

    def __init__(self):
        """
        Initialize file descriptor tracking dictionaries and the base class.
        """
        self._reads = {}
        self._writes = {}
        posixbase.PosixReactorBase.__init__(self)


    def _preenDescriptors(self):
        log.msg("Malformed file descriptor found.  Preening lists.")
        readers = self._reads.keys()
        writers = self._writes.keys()
        self._reads.clear()
        self._writes.clear()
        for selDict, selList in ((self._reads, readers),
                                 (self._writes, writers)):
            for selectable in selList:
                try:
                    select.select([selectable], [selectable], [selectable], 0)
                except Exception, e:
                    log.msg("bad descriptor %s" % selectable)
                    self._disconnectSelectable(selectable, e, False)
                else:
                    selDict[selectable] = 1


    def doSelect(self, timeout):
        """
        Run one iteration of the I/O monitor loop.

        This will run all selectables who had input or output readiness
        waiting for them.
        """
        while 1:
            try:
                r, w, ignored = _select(self._reads.keys(),
                                        self._writes.keys(),
                                        [], timeout)
                break
            except ValueError, ve:
                # Possibly a file descriptor has gone negative?
                log.err()
                self._preenDescriptors()
            except TypeError, te:
                # Something *totally* invalid (object w/o fileno, non-integral
                # result) was passed
                log.err()
                self._preenDescriptors()
            except (select.error, IOError), se:
                # select(2) encountered an error
                if se.args[0] in (0, 2):
                    # windows does this if it got an empty list
                    if (not self._reads) and (not self._writes):
                        return
                    else:
                        raise
                elif se.args[0] == EINTR:
                    return
                elif se.args[0] == EBADF:
                    self._preenDescriptors()
                else:
                    # OK, I really don't know what's going on.  Blow up.
                    raise
        _drdw = self._doReadOrWrite
        _logrun = log.callWithLogger
        for selectables, method, fdset in ((r, "doRead", self._reads),
                                           (w,"doWrite", self._writes)):
            for selectable in selectables:
                # if this was disconnected in another thread, kill it.
                # ^^^^ --- what the !@#*?  serious!  -exarkun
                if selectable not in fdset:
                    continue
                # This for pausing input when we're not ready for more.
                _logrun(selectable, _drdw, selectable, method, dict)

    doIteration = doSelect

    def _doReadOrWrite(self, selectable, method, dict):
        try:
            why = getattr(selectable, method)()
            handfn = getattr(selectable, 'fileno', None)
            if not handfn:
                why = _NO_FILENO
            elif handfn() == -1:
                why = _NO_FILEDESC
        except:
            why = sys.exc_info()[1]
            log.err()
        if why:
            self._disconnectSelectable(selectable, why, method=="doRead")

    def addReader(self, reader):
        """
        Add a FileDescriptor for notification of data available to read.
        """
        self._reads[reader] = 1

    def addWriter(self, writer):
        """
        Add a FileDescriptor for notification of data available to write.
        """
        self._writes[writer] = 1

    def removeReader(self, reader):
        """
        Remove a Selectable for notification of data available to read.
        """
        if reader in self._reads:
            del self._reads[reader]

    def removeWriter(self, writer):
        """
        Remove a Selectable for notification of data available to write.
        """
        if writer in self._writes:
            del self._writes[writer]

    def removeAll(self):
        return self._removeAll(self._reads, self._writes)


    def getReaders(self):
        return self._reads.keys()


    def getWriters(self):
        return self._writes.keys()



def install():
    """Configure the twisted mainloop to be run using the select() reactor.
    """
    reactor = SelectReactor()
    from twisted.internet.main import installReactor
    installReactor(reactor)

__all__ = ['install']
