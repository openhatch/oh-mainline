# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for implementations of L{IReactorProcess}.
"""

__metaclass__ = type

import os, sys, signal, threading

from twisted.trial.unittest import TestCase, SkipTest
from twisted.internet.test.reactormixins import ReactorBuilder
from twisted.python.compat import set
from twisted.python.log import msg, err
from twisted.python.runtime import platform
from twisted.python.filepath import FilePath
from twisted.internet import utils
from twisted.internet.interfaces import IReactorProcess, IProcessTransport
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.error import ProcessDone, ProcessTerminated
from twisted.internet import _signals
from twisted.python import runtime
if not runtime.platform.isWindows():
    from twisted.internet import process



class _ShutdownCallbackProcessProtocol(ProcessProtocol):
    """
    An L{IProcessProtocol} which fires a Deferred when the process it is
    associated with ends.
    """
    def __init__(self, whenFinished):
        self.whenFinished = whenFinished


    def processEnded(self, reason):
        self.whenFinished.callback(None)



class ProcessTestsBuilderBase(ReactorBuilder):
    """
    Base class for L{IReactorProcess} tests which defines some tests which
    can be applied to PTY or non-PTY uses of C{spawnProcess}.

    Subclasses are expected to set the C{usePTY} attribute to C{True} or
    C{False}.
    """
    requiredInterfaces = [IReactorProcess]


    def test_processTransportInterface(self):
        """
        L{IReactorProcess.spawnProcess} connects the protocol passed to it
        to a transport which provides L{IProcessTransport}.
        """
        ended = Deferred()
        protocol = _ShutdownCallbackProcessProtocol(ended)

        reactor = self.buildReactor()
        transport = reactor.spawnProcess(
            protocol, sys.executable, [sys.executable, "-c", ""],
            usePTY=self.usePTY)

        # The transport is available synchronously, so we can check it right
        # away (unlike many transport-based tests).  This is convenient even
        # though it's probably not how the spawnProcess interface should really
        # work.
        # We're not using verifyObject here because part of
        # IProcessTransport is a lie - there are no getHost or getPeer
        # methods.  See #1124.
        self.assertTrue(IProcessTransport.providedBy(transport))

        # Let the process run and exit so we don't leave a zombie around.
        ended.addCallback(lambda ignored: reactor.stop())
        self.runReactor(reactor)


    def test_spawnProcessEarlyIsReaped(self):
        """
        If, before the reactor is started with L{IReactorCore.run}, a
        process is started with L{IReactorProcess.spawnProcess} and
        terminates, the process is reaped once the reactor is started.
        """
        reactor = self.buildReactor()

        # Create the process with no shared file descriptors, so that there
        # are no other events for the reactor to notice and "cheat" with.
        # We want to be sure it's really dealing with the process exiting,
        # not some associated event.
        if self.usePTY:
            childFDs = None
        else:
            childFDs = {}

        # Arrange to notice the SIGCHLD.
        signaled = threading.Event()
        def handler(*args):
            signaled.set()
        signal.signal(signal.SIGCHLD, handler)

        # Start a process - before starting the reactor!
        ended = Deferred()
        reactor.spawnProcess(
            _ShutdownCallbackProcessProtocol(ended), sys.executable,
            [sys.executable, "-c", ""], usePTY=self.usePTY, childFDs=childFDs)

        # Wait for the SIGCHLD (which might have been delivered before we got
        # here, but that's okay because the signal handler was installed above,
        # before we could have gotten it).
        signaled.wait(120)
        if not signaled.isSet():
            self.fail("Timed out waiting for child process to exit.")

        # Capture the processEnded callback.
        result = []
        ended.addCallback(result.append)

        if result:
            # The synchronous path through spawnProcess / Process.__init__ /
            # registerReapProcessHandler was encountered.  There's no reason to
            # start the reactor, because everything is done already.
            return

        # Otherwise, though, start the reactor so it can tell us the process
        # exited.
        ended.addCallback(lambda ignored: reactor.stop())
        self.runReactor(reactor)

        # Make sure the reactor stopped because the Deferred fired.
        self.assertTrue(result)

    if getattr(signal, 'SIGCHLD', None) is None:
        test_spawnProcessEarlyIsReaped.skip = (
            "Platform lacks SIGCHLD, early-spawnProcess test can't work.")


    def test_processExitedWithSignal(self):
        """
        The C{reason} argument passed to L{IProcessProtocol.processExited} is a
        L{ProcessTerminated} instance if the child process exits with a signal.
        """
        sigName = 'TERM'
        sigNum = getattr(signal, 'SIG' + sigName)
        exited = Deferred()
        source = (
            "import sys\n"
            # Talk so the parent process knows the process is running.  This is
            # necessary because ProcessProtocol.makeConnection may be called
            # before this process is exec'd.  It would be unfortunate if we
            # SIGTERM'd the Twisted process while it was on its way to doing
            # the exec.
            "sys.stdout.write('x')\n"
            "sys.stdout.flush()\n"
            "sys.stdin.read()\n")

        class Exiter(ProcessProtocol):
            def childDataReceived(self, fd, data):
                msg('childDataReceived(%d, %r)' % (fd, data))
                self.transport.signalProcess(sigName)

            def childConnectionLost(self, fd):
                msg('childConnectionLost(%d)' % (fd,))

            def processExited(self, reason):
                msg('processExited(%r)' % (reason,))
                # Protect the Deferred from the failure so that it follows
                # the callback chain.  This doesn't use the errback chain
                # because it wants to make sure reason is a Failure.  An
                # Exception would also make an errback-based test pass, and
                # that would be wrong.
                exited.callback([reason])

            def processEnded(self, reason):
                msg('processEnded(%r)' % (reason,))

        reactor = self.buildReactor()
        reactor.callWhenRunning(
            reactor.spawnProcess, Exiter(), sys.executable,
            [sys.executable, "-c", source], usePTY=self.usePTY)

        def cbExited((failure,)):
            # Trapping implicitly verifies that it's a Failure (rather than
            # an exception) and explicitly makes sure it's the right type.
            failure.trap(ProcessTerminated)
            err = failure.value
            if platform.isWindows():
                # Windows can't really /have/ signals, so it certainly can't
                # report them as the reason for termination.  Maybe there's
                # something better we could be doing here, anyway?  Hard to
                # say.  Anyway, this inconsistency between different platforms
                # is extremely unfortunate and I would remove it if I
                # could. -exarkun
                self.assertIdentical(err.signal, None)
                self.assertEqual(err.exitCode, 1)
            else:
                self.assertEqual(err.signal, sigNum)
                self.assertIdentical(err.exitCode, None)

        exited.addCallback(cbExited)
        exited.addErrback(err)
        exited.addCallback(lambda ign: reactor.stop())

        self.runReactor(reactor)


    def test_systemCallUninterruptedByChildExit(self):
        """
        If a child process exits while a system call is in progress, the system
        call should not be interfered with.  In particular, it should not fail
        with EINTR.

        Older versions of Twisted installed a SIGCHLD handler on POSIX without
        using the feature exposed by the SA_RESTART flag to sigaction(2).  The
        most noticable problem this caused was for blocking reads and writes to
        sometimes fail with EINTR.
        """
        reactor = self.buildReactor()

        # XXX Since pygobject/pygtk wants to use signal.set_wakeup_fd,
        # we aren't actually providing this functionality on the glib2
        # or gtk2 reactors yet.  See #4286 for the possibility of
        # improving this.
        skippedReactors = ["Glib2Reactor", "Gtk2Reactor"]
        hasSigInterrupt = getattr(signal, "siginterrupt", None) is not None
        reactorClassName = reactor.__class__.__name__
        if reactorClassName in skippedReactors and not hasSigInterrupt:
            raise SkipTest(
                "%s is not supported without siginterrupt" % reactorClassName)
        if _signals.installHandler.__name__  == "_installHandlerUsingSignal":
            raise SkipTest("_signals._installHandlerUsingSignal doesn't support this feature")

        result = []

        def f():
            try:
                f1 = os.popen('%s -c "import time; time.sleep(0.1)"' %
                    (sys.executable,))
                f2 = os.popen('%s -c "import time; time.sleep(0.5); print \'Foo\'"' %
                    (sys.executable,))
                # The read call below will blow up with an EINTR from the
                # SIGCHLD from the first process exiting if we install a
                # SIGCHLD handler without SA_RESTART.  (which we used to do)
                result.append(f2.read())
            finally:
                reactor.stop()

        reactor.callWhenRunning(f)
        self.runReactor(reactor)
        self.assertEqual(result, ["Foo\n"])


    def test_openFileDescriptors(self):
        """
        A spawned process has only stdin, stdout and stderr open
        (file descriptor 3 is also reported as open, because of the call to
        'os.listdir()').
        """
        from twisted.python.runtime import platformType
        if platformType != "posix":
            raise SkipTest("Test only applies to POSIX platforms")

        here = FilePath(__file__)
        top = here.parent().parent().parent().parent()
        source = (
            "import sys",
            "sys.path.insert(0, '%s')" % (top.path,),
            "from twisted.internet import process",
            "sys.stdout.write(str(process._listOpenFDs()))",
            "sys.stdout.flush()")

        def checkOutput(output):
            self.assertEquals('[0, 1, 2, 3]', output)

        reactor = self.buildReactor()

        class Protocol(ProcessProtocol):
            def __init__(self):
                self.output = []

            def outReceived(self, data):
                self.output.append(data)

            def processEnded(self, reason):
                try:
                    checkOutput("".join(self.output))
                finally:
                    reactor.stop()

        proto = Protocol()
        reactor.callWhenRunning(
            reactor.spawnProcess, proto, sys.executable,
            [sys.executable, "-Wignore", "-c", "\n".join(source)],
            usePTY=self.usePTY)
        self.runReactor(reactor)


class ProcessTestsBuilder(ProcessTestsBuilderBase):
    """
    Builder defining tests relating to L{IReactorProcess} for child processes
    which do not have a PTY.
    """
    usePTY = False

    keepStdioOpenProgram = FilePath(__file__).sibling('process_helper.py').path
    if platform.isWindows():
        keepStdioOpenArg = "windows"
    else:
        # Just a value that doesn't equal "windows"
        keepStdioOpenArg = ""

    # Define this test here because PTY-using processes only have stdin and
    # stdout and the test would need to be different for that to work.
    def test_childConnectionLost(self):
        """
        L{IProcessProtocol.childConnectionLost} is called each time a file
        descriptor associated with a child process is closed.
        """
        connected = Deferred()
        lost = {0: Deferred(), 1: Deferred(), 2: Deferred()}

        class Closer(ProcessProtocol):
            def makeConnection(self, transport):
                connected.callback(transport)

            def childConnectionLost(self, childFD):
                lost[childFD].callback(None)

        source = (
            "import os, sys\n"
            "while 1:\n"
            "    line = sys.stdin.readline().strip()\n"
            "    if not line:\n"
            "        break\n"
            "    os.close(int(line))\n")

        reactor = self.buildReactor()
        reactor.callWhenRunning(
            reactor.spawnProcess, Closer(), sys.executable,
            [sys.executable, "-c", source], usePTY=self.usePTY)

        def cbConnected(transport):
            transport.write('2\n')
            return lost[2].addCallback(lambda ign: transport)
        connected.addCallback(cbConnected)

        def lostSecond(transport):
            transport.write('1\n')
            return lost[1].addCallback(lambda ign: transport)
        connected.addCallback(lostSecond)

        def lostFirst(transport):
            transport.write('\n')
        connected.addCallback(lostFirst)
        connected.addErrback(err)

        def cbEnded(ignored):
            reactor.stop()
        connected.addCallback(cbEnded)

        self.runReactor(reactor)


    # This test is here because PTYProcess never delivers childConnectionLost.
    def test_processEnded(self):
        """
        L{IProcessProtocol.processEnded} is called after the child process
        exits and L{IProcessProtocol.childConnectionLost} is called for each of
        its file descriptors.
        """
        ended = Deferred()
        lost = []

        class Ender(ProcessProtocol):
            def childDataReceived(self, fd, data):
                msg('childDataReceived(%d, %r)' % (fd, data))
                self.transport.loseConnection()

            def childConnectionLost(self, childFD):
                msg('childConnectionLost(%d)' % (childFD,))
                lost.append(childFD)

            def processExited(self, reason):
                msg('processExited(%r)' % (reason,))

            def processEnded(self, reason):
                msg('processEnded(%r)' % (reason,))
                ended.callback([reason])

        reactor = self.buildReactor()
        reactor.callWhenRunning(
            reactor.spawnProcess, Ender(), sys.executable,
            [sys.executable, self.keepStdioOpenProgram, "child",
             self.keepStdioOpenArg],
            usePTY=self.usePTY)

        def cbEnded((failure,)):
            failure.trap(ProcessDone)
            self.assertEqual(set(lost), set([0, 1, 2]))
        ended.addCallback(cbEnded)

        ended.addErrback(err)
        ended.addCallback(lambda ign: reactor.stop())

        self.runReactor(reactor)


    # This test is here because PTYProcess.loseConnection does not actually
    # close the file descriptors to the child process.  This test needs to be
    # written fairly differently for PTYProcess.
    def test_processExited(self):
        """
        L{IProcessProtocol.processExited} is called when the child process
        exits, even if file descriptors associated with the child are still
        open.
        """
        exited = Deferred()
        allLost = Deferred()
        lost = []

        class Waiter(ProcessProtocol):
            def childDataReceived(self, fd, data):
                msg('childDataReceived(%d, %r)' % (fd, data))

            def childConnectionLost(self, childFD):
                msg('childConnectionLost(%d)' % (childFD,))
                lost.append(childFD)
                if len(lost) == 3:
                    allLost.callback(None)

            def processExited(self, reason):
                msg('processExited(%r)' % (reason,))
                # See test_processExitedWithSignal
                exited.callback([reason])
                self.transport.loseConnection()

        reactor = self.buildReactor()
        reactor.callWhenRunning(
            reactor.spawnProcess, Waiter(), sys.executable,
            [sys.executable, self.keepStdioOpenProgram, "child",
             self.keepStdioOpenArg],
            usePTY=self.usePTY)

        def cbExited((failure,)):
            failure.trap(ProcessDone)
            msg('cbExited; lost = %s' % (lost,))
            self.assertEqual(lost, [])
            return allLost
        exited.addCallback(cbExited)

        def cbAllLost(ignored):
            self.assertEqual(set(lost), set([0, 1, 2]))
        exited.addCallback(cbAllLost)

        exited.addErrback(err)
        exited.addCallback(lambda ign: reactor.stop())

        self.runReactor(reactor)


    def makeSourceFile(self, sourceLines):
        """
        Write the given list of lines to a text file and return the absolute
        path to it.
        """
        script = self.mktemp()
        scriptFile = file(script, 'wt')
        scriptFile.write(os.linesep.join(sourceLines) + os.linesep)
        scriptFile.close()
        return os.path.abspath(script)


    def test_shebang(self):
        """
        Spawning a process with an executable which is a script starting
        with an interpreter definition line (#!) uses that interpreter to
        evaluate the script.
        """
        SHEBANG_OUTPUT = 'this is the shebang output'

        scriptFile = self.makeSourceFile([
                "#!%s" % (sys.executable,),
                "import sys",
                "sys.stdout.write('%s')" % (SHEBANG_OUTPUT,),
                "sys.stdout.flush()"])
        os.chmod(scriptFile, 0700)

        reactor = self.buildReactor()

        def cbProcessExited((out, err, code)):
            msg("cbProcessExited((%r, %r, %d))" % (out, err, code))
            self.assertEqual(out, SHEBANG_OUTPUT)
            self.assertEqual(err, "")
            self.assertEqual(code, 0)

        def shutdown(passthrough):
            reactor.stop()
            return passthrough

        def start():
            d = utils.getProcessOutputAndValue(scriptFile, reactor=reactor)
            d.addBoth(shutdown)
            d.addCallback(cbProcessExited)
            d.addErrback(err)

        reactor.callWhenRunning(start)
        self.runReactor(reactor)


    def test_processCommandLineArguments(self):
        """
        Arguments given to spawnProcess are passed to the child process as
        originally intended.
        """
        source = (
            # On Windows, stdout is not opened in binary mode by default,
            # so newline characters are munged on writing, interfering with
            # the tests.
            'import sys, os\n'
            'try:\n'
            '  import msvcrt\n'
            '  msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)\n'
            'except ImportError:\n'
            '  pass\n'
            'for arg in sys.argv[1:]:\n'
            '  sys.stdout.write(arg + chr(0))\n'
            '  sys.stdout.flush()')

        args = ['hello', '"', ' \t|<>^&', r'"\\"hello\\"', r'"foo\ bar baz\""']
        # Ensure that all non-NUL characters can be passed too.
        args.append(''.join(map(chr, xrange(1, 256))))

        reactor = self.buildReactor()

        def processFinished(output):
            output = output.split('\0')
            # Drop the trailing \0.
            output.pop()
            self.assertEquals(args, output)

        def shutdown(result):
            reactor.stop()
            return result

        def spawnChild():
            d = succeed(None)
            d.addCallback(lambda dummy: utils.getProcessOutput(
                sys.executable, ['-c', source] + args, reactor=reactor))
            d.addCallback(processFinished)
            d.addBoth(shutdown)

        reactor.callWhenRunning(spawnChild)
        self.runReactor(reactor)
globals().update(ProcessTestsBuilder.makeTestCaseClasses())



class PTYProcessTestsBuilder(ProcessTestsBuilderBase):
    """
    Builder defining tests relating to L{IReactorProcess} for child processes
    which have a PTY.
    """
    usePTY = True

    if platform.isWindows():
        skip = "PTYs are not supported on Windows."
    elif platform.isMacOSX():
        skippedReactors = {
            "twisted.internet.pollreactor.PollReactor":
                "OS X's poll() does not support PTYs"}
globals().update(PTYProcessTestsBuilder.makeTestCaseClasses())



class PotentialZombieWarningTests(TestCase):
    """
    Tests for L{twisted.internet.error.PotentialZombieWarning}.
    """
    def test_deprecated(self):
        """
        Accessing L{PotentialZombieWarning} via the
        I{PotentialZombieWarning} attribute of L{twisted.internet.error}
        results in a deprecation warning being emitted.
        """
        from twisted.internet import error
        error.PotentialZombieWarning

        warnings = self.flushWarnings([self.test_deprecated])
        self.assertEquals(warnings[0]['category'], DeprecationWarning)
        self.assertEquals(
            warnings[0]['message'],
            "twisted.internet.error.PotentialZombieWarning was deprecated in "
            "Twisted 10.0.0: There is no longer any potential for zombie "
            "process.")
        self.assertEquals(len(warnings), 1)



class FakeResourceModule(object):
    """
    Fake version of L{resource} which hard-codes a particular rlimit for maximum
    open files.
    """
    RLIMIT_NOFILE = 1
    def getrlimit(self, no):
        """
        Mocks just the getrlimit method of the resource module, simulating what
        happens on OS-X when a ridiculous number is returned.
        """
        return [0, 9223372036854775808]



class FDDetectorTest(TestCase):
    """
    Tests for _FDDetector class in twisted.internet.process, which detects
    which function to drop in place for the _listOpenFDs method.

    @ivar devfs: A flag indicating whether the filesystem fake will indicate
        that /dev/fd exists.

    @ivar accurateDevFDResults: A flag indicating whether the /dev/fd fake
        returns accurate open file information.

    @ivar procfs: A flag indicating whether the filesystem fake will indicate
        that /proc/<pid>/fd exists.

    @ivar openedFile: A flag indicating whether to include an extra file
        descriptor in the result of listing /dev/fd.
    """
    if runtime.platform.isWindows():
        skip = (
            "Process support does not need to detect open file descriptors on "
            "Windows")

    devfs = False
    accurateDevFDResults = False

    procfs = False
    openedFile = False

    savedResourceModule = None

    def getpid(self):
        """
        Fake os.getpid, always return the same thing
        """
        return 123


    def listdir(self, arg):
        """
        Fake os.listdir, depending on what mode we're in to simulate
        behaviour.

        @param arg: the directory to list
        """
        if arg == '/proc/123/fd':
            if self.procfs:
                return ["0","1","2"]
            else:
                raise OSError

        if arg == '/dev/fd':
            if self.devfs:
                if not self.accurateDevFDResults:
                    # Always return the same thing
                    return ["0","1","2"]
                else:
                    if self.openedFile:
                        return ["0","1","2","3"]
                    else:
                        return ["0","1","2"]
            else:
                raise OSError()


    def openfile(self, fname, mode):
        """
        This is a mock for L{open}.  It just keeps track of the fact that a file
        has opened so an extra file descriptor is found in /dev/fd.
        """
        self.openedFile = True


    def saveResourceModule(self):
        """
        Save the resource module so we can restore it later.
        """
        try:
            import resource
        except ImportError:
            resource = None
        self.savedResourceModule = resource


    def hideResourceModule(self):
        """
        Make the L{resource} module unimportable for the remainder of the
        current test method.
        """
        sys.modules['resource'] = None
        self.addCleanup(self.replaceResourceModule)


    def revealResourceModule(self):
        """
        Make a L{FakeResourceModule} instance importable at the L{resource}
        name.
        """
        sys.modules['resource'] = FakeResourceModule()
        self.addCleanup(self.replaceResourceModule)


    def replaceResourceModule(self):
        """
        Restore the original resource module to L{sys.modules}.
        """
        sys.modules['resource'] = self.savedResourceModule


    def setUp(self):
        """
        Set up the tests, giving ourselves a detector object to play with and
        setting up its testable knobs to refer to our mocked versions.
        """
        self.detector = process._FDDetector()
        self.detector.listdir = self.listdir
        self.detector.getpid = self.getpid
        self.detector.openfile = self.openfile


    def test_identityOfListOpenFDsChanges(self):
        """
        Check that the identity of _listOpenFDs changes after running _listOpenFDs
        the first time, but not after the second time it's run.

        In other words, check that the monkey patching actually works.
        """
        # Create a new instance
        detector = process._FDDetector()

        first = detector._listOpenFDs.func_name
        detector._listOpenFDs()
        second = detector._listOpenFDs.func_name
        detector._listOpenFDs()
        third = detector._listOpenFDs.func_name

        self.assertNotEquals(first, second)
        self.assertEquals(second, third)


    def test_accurateDevFDResults(self):
        """
        If there is no proc filesystem and /dev/fd returns accurate open file
        descriptor information, L{process._devFDImplementation} is chosen.  This
        is like FreeBSD with I{fdescfs} mounted.
        """
        self.procfs = False
        self.devfs = True
        self.accurateDevFDResults = True
        self.assertEquals(
            self.detector._getImplementation().func_name,
            '_devFDImplementation')


    def test_inaccurateDevFDResults(self):
        """
        If there is no proc filesystem and /dev/fd returns inaccurate
        information, L{_process._fallbackFDImplementation} is selected.  This is
        like FreeBSD without I{fdescfs} mounted.
        """
        self.procfs = False
        self.devfs = True
        self.accurateDevFDResults = False
        self.assertEquals(
            self.detector._getImplementation().func_name,
            '_fallbackFDImplementation')


    def test_procFilesystem(self):
        """
        If there is a proc filesystem, L{process._procFDImplementation} is
        selected.  This is like Linux.
        """
        self.devfs = False
        self.procfs = True
        self.assertEquals(
            self.detector._getImplementation().func_name,
            '_procFDImplementation')


    def test_resourceModuleOnly(self):
        """
        If there is no proc filesystem and no /dev/fd but the L{resource} module
        is available, L{process._resourceFDImplementation} is selected.  We
        shall conjecture that this is like most proprietary UNIXes.
        """
        self.devfs = False
        self.procfs = False
        self.revealResourceModule()
        self.assertEquals(
            self.detector._getImplementation().func_name,
            '_resourceFDImplementation')


    def test_withoutResourceModule(self):
        """
        If there is no proc filesystem, no /dev/fd, and no L{resource} module is
        available, L{process._fallbackFDImplementation} is selected.  This maybe
        be like certain proprietary UNIXes without a nicely compiled Python
        runtime.
        """
        self.devfs = False
        self.procfs = False
        self.hideResourceModule()
        self.assertEquals(
            self.detector._getImplementation().func_name,
            '_fallbackFDImplementation')
