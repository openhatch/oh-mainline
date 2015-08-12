# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for failure module.
"""

import sys
import StringIO
import traceback

from twisted.trial import unittest, util

from twisted.python import failure

try:
    from twisted.test import raiser
except ImportError:
    raiser = None


def getDivisionFailure():
    try:
        1/0
    except:
        f = failure.Failure()
    return f


class FailureTestCase(unittest.TestCase):

    def testFailAndTrap(self):
        """Trapping a failure."""
        try:
            raise NotImplementedError('test')
        except:
            f = failure.Failure()
        error = f.trap(SystemExit, RuntimeError)
        self.assertEquals(error, RuntimeError)
        self.assertEquals(f.type, NotImplementedError)

    def test_notTrapped(self):
        """Making sure trap doesn't trap what it shouldn't."""
        try:
            raise ValueError()
        except:
            f = failure.Failure()
        self.assertRaises(failure.Failure, f.trap, OverflowError)

    def testPrinting(self):
        out = StringIO.StringIO()
        try:
            1/0
        except:
            f = failure.Failure()
        f.printDetailedTraceback(out)
        f.printBriefTraceback(out)
        f.printTraceback(out)

    def testExplictPass(self):
        e = RuntimeError()
        f = failure.Failure(e)
        f.trap(RuntimeError)
        self.assertEquals(f.value, e)


    def _getInnermostFrameLine(self, f):
        try:
            f.raiseException()
        except ZeroDivisionError:
            tb = traceback.extract_tb(sys.exc_info()[2])
            return tb[-1][-1]
        else:
            raise Exception(
                "f.raiseException() didn't raise ZeroDivisionError!?")


    def testRaiseExceptionWithTB(self):
        f = getDivisionFailure()
        innerline = self._getInnermostFrameLine(f)
        self.assertEquals(innerline, '1/0')


    def testLackOfTB(self):
        f = getDivisionFailure()
        f.cleanFailure()
        innerline = self._getInnermostFrameLine(f)
        self.assertEquals(innerline, '1/0')

    testLackOfTB.todo = "the traceback is not preserved, exarkun said he'll try to fix this! god knows how"


    _stringException = "bugger off"
    def _getStringFailure(self):
        try:
            raise self._stringException
        except:
            f = failure.Failure()
        return f

    def test_raiseStringExceptions(self):
        # String exceptions used to totally bugged f.raiseException
        f = self._getStringFailure()
        try:
            f.raiseException()
        except:
            self.assertEquals(sys.exc_info()[0], self._stringException)
        else:
            raise AssertionError("Should have raised")
    test_raiseStringExceptions.suppress = [
        util.suppress(message='raising a string exception is deprecated')]


    def test_printStringExceptions(self):
        """
        L{Failure.printTraceback} should write out stack and exception
        information, even for string exceptions.
        """
        failure = self._getStringFailure()
        output = StringIO.StringIO()
        failure.printTraceback(file=output)
        lines = output.getvalue().splitlines()
        # The last line should be the value of the raised string
        self.assertEqual(lines[-1], self._stringException)

    test_printStringExceptions.suppress = [
        util.suppress(message='raising a string exception is deprecated')]

    if sys.version_info[:2] >= (2, 6):
        skipMsg = ("String exceptions aren't supported anymore starting "
                   "Python 2.6")
        test_raiseStringExceptions.skip = skipMsg
        test_printStringExceptions.skip = skipMsg


    def testConstructionFails(self):
        """
        Creating a Failure with no arguments causes it to try to discover the
        current interpreter exception state.  If no such state exists, creating
        the Failure should raise a synchronous exception.
        """
        self.assertRaises(failure.NoCurrentExceptionError, failure.Failure)

    def test_getTracebackObject(self):
        """
        If the C{Failure} has not been cleaned, then C{getTracebackObject}
        should return the traceback object that it was given in the
        constructor.
        """
        f = getDivisionFailure()
        self.assertEqual(f.getTracebackObject(), f.tb)

    def test_getTracebackObjectFromClean(self):
        """
        If the Failure has been cleaned, then C{getTracebackObject} should
        return an object that looks the same to L{traceback.extract_tb}.
        """
        f = getDivisionFailure()
        expected = traceback.extract_tb(f.getTracebackObject())
        f.cleanFailure()
        observed = traceback.extract_tb(f.getTracebackObject())
        self.assertEqual(expected, observed)

    def test_getTracebackObjectWithoutTraceback(self):
        """
        L{failure.Failure}s need not be constructed with traceback objects. If
        a C{Failure} has no traceback information at all, C{getTracebackObject}
        should just return None.

        None is a good value, because traceback.extract_tb(None) -> [].
        """
        f = failure.Failure(Exception("some error"))
        self.assertEqual(f.getTracebackObject(), None)



class BrokenStr(Exception):
    """
    An exception class the instances of which cannot be presented as strings via
    C{str}.
    """
    def __str__(self):
        # Could raise something else, but there's no point as yet.
        raise self



class BrokenExceptionMetaclass(type):
    """
    A metaclass for an exception type which cannot be presented as a string via
    C{str}.
    """
    def __str__(self):
        raise ValueError("You cannot make a string out of me.")



class BrokenExceptionType(Exception, object):
    """
    The aforementioned exception type which cnanot be presented as a string via
    C{str}.
    """
    __metaclass__ = BrokenExceptionMetaclass



class GetTracebackTests(unittest.TestCase):
    """
    Tests for L{Failure.getTraceback}.
    """
    def _brokenValueTest(self, detail):
        """
        Construct a L{Failure} with an exception that raises an exception from
        its C{__str__} method and then call C{getTraceback} with the specified
        detail and verify that it returns a string.
        """
        x = BrokenStr()
        f = failure.Failure(x)
        traceback = f.getTraceback(detail=detail)
        self.assertIsInstance(traceback, str)


    def test_brokenValueBriefDetail(self):
        """
        A L{Failure} might wrap an exception with a C{__str__} method which
        raises an exception.  In this case, calling C{getTraceback} on the
        failure with the C{"brief"} detail does not raise an exception.
        """
        self._brokenValueTest("brief")


    def test_brokenValueDefaultDetail(self):
        """
        Like test_brokenValueBriefDetail, but for the C{"default"} detail case.
        """
        self._brokenValueTest("default")


    def test_brokenValueVerboseDetail(self):
        """
        Like test_brokenValueBriefDetail, but for the C{"default"} detail case.
        """
        self._brokenValueTest("verbose")


    def _brokenTypeTest(self, detail):
        """
        Construct a L{Failure} with an exception type that raises an exception
        from its C{__str__} method and then call C{getTraceback} with the
        specified detail and verify that it returns a string.
        """
        f = failure.Failure(BrokenExceptionType())
        traceback = f.getTraceback(detail=detail)
        self.assertIsInstance(traceback, str)


    def test_brokenTypeBriefDetail(self):
        """
        A L{Failure} might wrap an exception the type object of which has a
        C{__str__} method which raises an exception.  In this case, calling
        C{getTraceback} on the failure with the C{"brief"} detail does not raise
        an exception.
        """
        self._brokenTypeTest("brief")


    def test_brokenTypeDefaultDetail(self):
        """
        Like test_brokenTypeBriefDetail, but for the C{"default"} detail case.
        """
        self._brokenTypeTest("default")


    def test_brokenTypeVerboseDetail(self):
        """
        Like test_brokenTypeBriefDetail, but for the C{"verbose"} detail case.
        """
        self._brokenTypeTest("verbose")



class FindFailureTests(unittest.TestCase):
    """
    Tests for functionality related to L{Failure._findFailure}.
    """

    def test_findNoFailureInExceptionHandler(self):
        """
        Within an exception handler, _findFailure should return
        C{None} in case no Failure is associated with the current
        exception.
        """
        try:
            1/0
        except:
            self.assertEqual(failure.Failure._findFailure(), None)
        else:
            self.fail("No exception raised from 1/0!?")


    def test_findNoFailure(self):
        """
        Outside of an exception handler, _findFailure should return None.
        """
        self.assertEqual(sys.exc_info()[-1], None) #environment sanity check
        self.assertEqual(failure.Failure._findFailure(), None)


    def test_findFailure(self):
        """
        Within an exception handler, it should be possible to find the
        original Failure that caused the current exception (if it was
        caused by raiseException).
        """
        f = getDivisionFailure()
        f.cleanFailure()
        try:
            f.raiseException()
        except:
            self.assertEqual(failure.Failure._findFailure(), f)
        else:
            self.fail("No exception raised from raiseException!?")


    def test_failureConstructionFindsOriginalFailure(self):
        """
        When a Failure is constructed in the context of an exception
        handler that is handling an exception raised by
        raiseException, the new Failure should be chained to that
        original Failure.
        """
        f = getDivisionFailure()
        f.cleanFailure()
        try:
            f.raiseException()
        except:
            newF = failure.Failure()
            self.assertEqual(f.getTraceback(), newF.getTraceback())
        else:
            self.fail("No exception raised from raiseException!?")


    def test_failureConstructionWithMungedStackSucceeds(self):
        """
        Pyrex and Cython are known to insert fake stack frames so as to give
        more Python-like tracebacks. These stack frames with empty code objects
        should not break extraction of the exception.
        """
        try:
            raiser.raiseException()
        except raiser.RaiserException:
            f = failure.Failure()
            self.assertTrue(f.check(raiser.RaiserException))
        else:
            self.fail("No exception raised from extension?!")


    if raiser is None:
        skipMsg = "raiser extension not available"
        test_failureConstructionWithMungedStackSucceeds.skip = skipMsg



class TestFormattableTraceback(unittest.TestCase):
    """
    Whitebox tests that show that L{failure._Traceback} constructs objects that
    can be used by L{traceback.extract_tb}.

    If the objects can be used by L{traceback.extract_tb}, then they can be
    formatted using L{traceback.format_tb} and friends.
    """

    def test_singleFrame(self):
        """
        A C{_Traceback} object constructed with a single frame should be able
        to be passed to L{traceback.extract_tb}, and we should get a singleton
        list containing a (filename, lineno, methodname, line) tuple.
        """
        tb = failure._Traceback([['method', 'filename.py', 123, {}, {}]])
        # Note that we don't need to test that extract_tb correctly extracts
        # the line's contents. In this case, since filename.py doesn't exist,
        # it will just use None.
        self.assertEqual(traceback.extract_tb(tb),
                         [('filename.py', 123, 'method', None)])

    def test_manyFrames(self):
        """
        A C{_Traceback} object constructed with multiple frames should be able
        to be passed to L{traceback.extract_tb}, and we should get a list
        containing a tuple for each frame.
        """
        tb = failure._Traceback([
            ['method1', 'filename.py', 123, {}, {}],
            ['method2', 'filename.py', 235, {}, {}]])
        self.assertEqual(traceback.extract_tb(tb),
                         [('filename.py', 123, 'method1', None),
                          ('filename.py', 235, 'method2', None)])



class TestFrameAttributes(unittest.TestCase):
    """
    _Frame objects should possess some basic attributes that qualify them as
    fake python Frame objects.
    """

    def test_fakeFrameAttributes(self):
        """
        L{_Frame} instances have the C{f_globals} and C{f_locals} attributes
        bound to C{dict} instance.  They also have the C{f_code} attribute
        bound to something like a code object.
        """
        frame = failure._Frame("dummyname", "dummyfilename")
        self.assertIsInstance(frame.f_globals, dict)
        self.assertIsInstance(frame.f_locals, dict)
        self.assertIsInstance(frame.f_code, failure._Code)


if sys.version_info[:2] >= (2, 5):
    from twisted.test.generator_failure_tests import TwoPointFiveFailureTests
