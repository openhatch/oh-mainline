# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Test cases for defer module.
"""

import gc, traceback

from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.internet.task import Clock
from twisted.python import failure, log
from twisted.python.util import unsignedID

class GenericError(Exception):
    pass



class DeferredTestCase(unittest.TestCase):

    def setUp(self):
        self.callbackResults = None
        self.errbackResults = None
        self.callback2Results = None

    def _callback(self, *args, **kw):
        self.callbackResults = args, kw
        return args[0]

    def _callback2(self, *args, **kw):
        self.callback2Results = args, kw

    def _errback(self, *args, **kw):
        self.errbackResults = args, kw

    def testCallbackWithoutArgs(self):
        deferred = defer.Deferred()
        deferred.addCallback(self._callback)
        deferred.callback("hello")
        self.failUnlessEqual(self.errbackResults, None)
        self.failUnlessEqual(self.callbackResults, (('hello',), {}))

    def testCallbackWithArgs(self):
        deferred = defer.Deferred()
        deferred.addCallback(self._callback, "world")
        deferred.callback("hello")
        self.failUnlessEqual(self.errbackResults, None)
        self.failUnlessEqual(self.callbackResults, (('hello', 'world'), {}))

    def testCallbackWithKwArgs(self):
        deferred = defer.Deferred()
        deferred.addCallback(self._callback, world="world")
        deferred.callback("hello")
        self.failUnlessEqual(self.errbackResults, None)
        self.failUnlessEqual(self.callbackResults,
                             (('hello',), {'world': 'world'}))

    def testTwoCallbacks(self):
        deferred = defer.Deferred()
        deferred.addCallback(self._callback)
        deferred.addCallback(self._callback2)
        deferred.callback("hello")
        self.failUnlessEqual(self.errbackResults, None)
        self.failUnlessEqual(self.callbackResults,
                             (('hello',), {}))
        self.failUnlessEqual(self.callback2Results,
                             (('hello',), {}))

    def testDeferredList(self):
        defr1 = defer.Deferred()
        defr2 = defer.Deferred()
        defr3 = defer.Deferred()
        dl = defer.DeferredList([defr1, defr2, defr3])
        result = []
        def cb(resultList, result=result):
            result.extend(resultList)
        def catch(err):
            return None
        dl.addCallbacks(cb, cb)
        defr1.callback("1")
        defr2.addErrback(catch)
        # "catch" is added to eat the GenericError that will be passed on by
        # the DeferredList's callback on defr2. If left unhandled, the
        # Failure object would cause a log.err() warning about "Unhandled
        # error in Deferred". Twisted's pyunit watches for log.err calls and
        # treats them as failures. So "catch" must eat the error to prevent
        # it from flunking the test.
        defr2.errback(GenericError("2"))
        defr3.callback("3")
        self.failUnlessEqual([result[0],
                    #result[1][1] is now a Failure instead of an Exception
                              (result[1][0], str(result[1][1].value)),
                              result[2]],

                             [(defer.SUCCESS, "1"),
                              (defer.FAILURE, "2"),
                              (defer.SUCCESS, "3")])

    def testEmptyDeferredList(self):
        result = []
        def cb(resultList, result=result):
            result.append(resultList)

        dl = defer.DeferredList([])
        dl.addCallbacks(cb)
        self.failUnlessEqual(result, [[]])

        result[:] = []
        dl = defer.DeferredList([], fireOnOneCallback=1)
        dl.addCallbacks(cb)
        self.failUnlessEqual(result, [])

    def testDeferredListFireOnOneError(self):
        defr1 = defer.Deferred()
        defr2 = defer.Deferred()
        defr3 = defer.Deferred()
        dl = defer.DeferredList([defr1, defr2, defr3], fireOnOneErrback=1)
        result = []
        dl.addErrback(result.append)

        # consume errors after they pass through the DeferredList (to avoid
        # 'Unhandled error in Deferred'.
        def catch(err):
            return None
        defr2.addErrback(catch)

        # fire one Deferred's callback, no result yet
        defr1.callback("1")
        self.failUnlessEqual(result, [])

        # fire one Deferred's errback -- now we have a result
        defr2.errback(GenericError("from def2"))
        self.failUnlessEqual(len(result), 1)

        # extract the result from the list
        aFailure = result[0]

        # the type of the failure is a FirstError
        self.failUnless(issubclass(aFailure.type, defer.FirstError),
            'issubclass(aFailure.type, defer.FirstError) failed: '
            "failure's type is %r" % (aFailure.type,)
        )

        firstError = aFailure.value

        # check that the GenericError("2") from the deferred at index 1
        # (defr2) is intact inside failure.value
        self.failUnlessEqual(firstError.subFailure.type, GenericError)
        self.failUnlessEqual(firstError.subFailure.value.args, ("from def2",))
        self.failUnlessEqual(firstError.index, 1)


    def testDeferredListDontConsumeErrors(self):
        d1 = defer.Deferred()
        dl = defer.DeferredList([d1])

        errorTrap = []
        d1.addErrback(errorTrap.append)

        result = []
        dl.addCallback(result.append)

        d1.errback(GenericError('Bang'))
        self.failUnlessEqual('Bang', errorTrap[0].value.args[0])
        self.failUnlessEqual(1, len(result))
        self.failUnlessEqual('Bang', result[0][0][1].value.args[0])

    def testDeferredListConsumeErrors(self):
        d1 = defer.Deferred()
        dl = defer.DeferredList([d1], consumeErrors=True)

        errorTrap = []
        d1.addErrback(errorTrap.append)

        result = []
        dl.addCallback(result.append)

        d1.errback(GenericError('Bang'))
        self.failUnlessEqual([], errorTrap)
        self.failUnlessEqual(1, len(result))
        self.failUnlessEqual('Bang', result[0][0][1].value.args[0])

    def testDeferredListFireOnOneErrorWithAlreadyFiredDeferreds(self):
        # Create some deferreds, and errback one
        d1 = defer.Deferred()
        d2 = defer.Deferred()
        d1.errback(GenericError('Bang'))

        # *Then* build the DeferredList, with fireOnOneErrback=True
        dl = defer.DeferredList([d1, d2], fireOnOneErrback=True)
        result = []
        dl.addErrback(result.append)
        self.failUnlessEqual(1, len(result))

        d1.addErrback(lambda e: None)  # Swallow error

    def testDeferredListWithAlreadyFiredDeferreds(self):
        # Create some deferreds, and err one, call the other
        d1 = defer.Deferred()
        d2 = defer.Deferred()
        d1.errback(GenericError('Bang'))
        d2.callback(2)

        # *Then* build the DeferredList
        dl = defer.DeferredList([d1, d2])

        result = []
        dl.addCallback(result.append)

        self.failUnlessEqual(1, len(result))

        d1.addErrback(lambda e: None)  # Swallow error


    def testImmediateSuccess(self):
        l = []
        d = defer.succeed("success")
        d.addCallback(l.append)
        self.assertEquals(l, ["success"])


    def testImmediateFailure(self):
        l = []
        d = defer.fail(GenericError("fail"))
        d.addErrback(l.append)
        self.assertEquals(str(l[0].value), "fail")

    def testPausedFailure(self):
        l = []
        d = defer.fail(GenericError("fail"))
        d.pause()
        d.addErrback(l.append)
        self.assertEquals(l, [])
        d.unpause()
        self.assertEquals(str(l[0].value), "fail")

    def testCallbackErrors(self):
        l = []
        d = defer.Deferred().addCallback(lambda _: 1 / 0).addErrback(l.append)
        d.callback(1)
        self.assert_(isinstance(l[0].value, ZeroDivisionError))
        l = []
        d = defer.Deferred().addCallback(
            lambda _: failure.Failure(ZeroDivisionError())).addErrback(l.append)
        d.callback(1)
        self.assert_(isinstance(l[0].value, ZeroDivisionError))

    def testUnpauseBeforeCallback(self):
        d = defer.Deferred()
        d.pause()
        d.addCallback(self._callback)
        d.unpause()

    def testReturnDeferred(self):
        d = defer.Deferred()
        d2 = defer.Deferred()
        d2.pause()
        d.addCallback(lambda r, d2=d2: d2)
        d.addCallback(self._callback)
        d.callback(1)
        assert self.callbackResults is None, "Should not have been called yet."
        d2.callback(2)
        assert self.callbackResults is None, "Still should not have been called yet."
        d2.unpause()
        assert self.callbackResults[0][0] == 2, "Result should have been from second deferred:%s" % (self.callbackResults,)


    def test_chainedPausedDeferredWithResult(self):
        """
        When a paused Deferred with a result is returned from a callback on
        another Deferred, the other Deferred is chained to the first and waits
        for it to be unpaused.
        """
        expected = object()
        paused = defer.Deferred()
        paused.callback(expected)
        paused.pause()
        chained = defer.Deferred()
        chained.addCallback(lambda ignored: paused)
        chained.callback(None)

        result = []
        chained.addCallback(result.append)
        self.assertEquals(result, [])
        paused.unpause()
        self.assertEquals(result, [expected])


    def test_pausedDeferredChained(self):
        """
        A paused Deferred encountered while pushing a result forward through a
        chain does not prevent earlier Deferreds from continuing to execute
        their callbacks.
        """
        first = defer.Deferred()
        second = defer.Deferred()
        first.addCallback(lambda ignored: second)
        first.callback(None)
        first.pause()
        second.callback(None)
        result = []
        second.addCallback(result.append)
        self.assertEquals(result, [None])


    def testGatherResults(self):
        # test successful list of deferreds
        l = []
        defer.gatherResults([defer.succeed(1), defer.succeed(2)]).addCallback(l.append)
        self.assertEquals(l, [[1, 2]])
        # test failing list of deferreds
        l = []
        dl = [defer.succeed(1), defer.fail(ValueError)]
        defer.gatherResults(dl).addErrback(l.append)
        self.assertEquals(len(l), 1)
        self.assert_(isinstance(l[0], failure.Failure))
        # get rid of error
        dl[1].addErrback(lambda e: 1)


    def test_maybeDeferredSync(self):
        """
        L{defer.maybeDeferred} should retrieve the result of a synchronous
        function and pass it to its resulting L{defer.Deferred}.
        """
        S, E = [], []
        d = defer.maybeDeferred((lambda x: x + 5), 10)
        d.addCallbacks(S.append, E.append)
        self.assertEquals(E, [])
        self.assertEquals(S, [15])
        return d


    def test_maybeDeferredSyncError(self):
        """
        L{defer.maybeDeferred} should catch exception raised by a synchronous
        function and errback its resulting L{defer.Deferred} with it.
        """
        S, E = [], []
        try:
            '10' + 5
        except TypeError, e:
            expected = str(e)
        d = defer.maybeDeferred((lambda x: x + 5), '10')
        d.addCallbacks(S.append, E.append)
        self.assertEquals(S, [])
        self.assertEquals(len(E), 1)
        self.assertEquals(str(E[0].value), expected)
        return d


    def test_maybeDeferredAsync(self):
        """
        L{defer.maybeDeferred} should let L{defer.Deferred} instance pass by
        so that original result is the same.
        """
        d = defer.Deferred()
        d2 = defer.maybeDeferred(lambda: d)
        d.callback('Success')
        return d2.addCallback(self.assertEquals, 'Success')


    def test_maybeDeferredAsyncError(self):
        """
        L{defer.maybeDeferred} should let L{defer.Deferred} instance pass by
        so that L{failure.Failure} returned by the original instance is the
        same.
        """
        d = defer.Deferred()
        d2 = defer.maybeDeferred(lambda: d)
        d.errback(failure.Failure(RuntimeError()))
        return self.assertFailure(d2, RuntimeError)


    def test_innerCallbacksPreserved(self):
        """
        When a L{Deferred} encounters a result which is another L{Deferred}
        which is waiting on a third L{Deferred}, the middle L{Deferred}'s
        callbacks are executed after the third L{Deferred} fires and before the
        first receives a result.
        """
        results = []
        failures = []
        inner = defer.Deferred()
        def cb(result):
            results.append(('start-of-cb', result))
            d = defer.succeed('inner')
            def firstCallback(result):
                results.append(('firstCallback', 'inner'))
                return inner
            def secondCallback(result):
                results.append(('secondCallback', result))
                return result * 2
            d.addCallback(firstCallback).addCallback(secondCallback)
            d.addErrback(failures.append)
            return d
        outer = defer.succeed('outer')
        outer.addCallback(cb)
        inner.callback('orange')
        outer.addCallback(results.append)
        inner.addErrback(failures.append)
        outer.addErrback(failures.append)
        self.assertEqual([], failures)
        self.assertEqual(
            results,
            [('start-of-cb', 'outer'),
             ('firstCallback', 'inner'),
             ('secondCallback', 'orange'),
             'orangeorange'])


    def test_continueCallbackNotFirst(self):
        """
        The continue callback of a L{Deferred} waiting for another L{Deferred}
        is not necessarily the first one. This is somewhat a whitebox test
        checking that we search for that callback among the whole list of
        callbacks.
        """
        results = []
        failures = []
        a = defer.Deferred()

        def cb(result):
            results.append(('cb', result))
            d = defer.Deferred()

            def firstCallback(ignored):
                results.append(('firstCallback', ignored))
                return defer.gatherResults([a])

            def secondCallback(result):
                results.append(('secondCallback', result))

            d.addCallback(firstCallback)
            d.addCallback(secondCallback)
            d.addErrback(failures.append)
            d.callback(None)
            return d

        outer = defer.succeed('outer')
        outer.addCallback(cb)
        outer.addErrback(failures.append)
        self.assertEquals([('cb', 'outer'), ('firstCallback', None)], results)
        a.callback('withers')
        self.assertEquals([], failures)
        self.assertEquals(
            results,
            [('cb', 'outer'),
             ('firstCallback', None),
             ('secondCallback', ['withers'])])


    def test_callbackOrderPreserved(self):
        """
        A callback added to a L{Deferred} after a previous callback attached
        another L{Deferred} as a result is run after the callbacks of the other
        L{Deferred} are run.
        """
        results = []
        failures = []
        a = defer.Deferred()

        def cb(result):
            results.append(('cb', result))
            d = defer.Deferred()

            def firstCallback(ignored):
                results.append(('firstCallback', ignored))
                return defer.gatherResults([a])

            def secondCallback(result):
                results.append(('secondCallback', result))

            d.addCallback(firstCallback)
            d.addCallback(secondCallback)
            d.addErrback(failures.append)
            d.callback(None)
            return d

        outer = defer.Deferred()
        outer.addCallback(cb)
        outer.addCallback(lambda x: results.append('final'))
        outer.addErrback(failures.append)
        outer.callback('outer')
        self.assertEquals([('cb', 'outer'), ('firstCallback', None)], results)
        a.callback('withers')
        self.assertEquals([], failures)
        self.assertEquals(
            results,
            [('cb', 'outer'),
             ('firstCallback', None),
             ('secondCallback', ['withers']), 'final'])


    def test_reentrantRunCallbacks(self):
        """
        A callback added to a L{Deferred} by a callback on that L{Deferred}
        should be added to the end of the callback chain.
        """
        deferred = defer.Deferred()
        called = []
        def callback3(result):
            called.append(3)
        def callback2(result):
            called.append(2)
        def callback1(result):
            called.append(1)
            deferred.addCallback(callback3)
        deferred.addCallback(callback1)
        deferred.addCallback(callback2)
        deferred.callback(None)
        self.assertEqual(called, [1, 2, 3])


    def test_nonReentrantCallbacks(self):
        """
        A callback added to a L{Deferred} by a callback on that L{Deferred}
        should not be executed until the running callback returns.
        """
        deferred = defer.Deferred()
        called = []
        def callback2(result):
            called.append(2)
        def callback1(result):
            called.append(1)
            deferred.addCallback(callback2)
            self.assertEquals(called, [1])
        deferred.addCallback(callback1)
        deferred.callback(None)
        self.assertEqual(called, [1, 2])


    def test_reentrantRunCallbacksWithFailure(self):
        """
        After an exception is raised by a callback which was added to a
        L{Deferred} by a callback on that L{Deferred}, the L{Deferred} should
        call the first errback with a L{Failure} wrapping that exception.
        """
        exceptionMessage = "callback raised exception"
        deferred = defer.Deferred()
        def callback2(result):
            raise Exception(exceptionMessage)
        def callback1(result):
            deferred.addCallback(callback2)
        deferred.addCallback(callback1)
        deferred.callback(None)
        self.assertFailure(deferred, Exception)
        def cbFailed(exception):
            self.assertEqual(exception.args, (exceptionMessage,))
        deferred.addCallback(cbFailed)
        return deferred


    def test_synchronousImplicitChain(self):
        """
        If a first L{Deferred} with a result is returned from a callback on a
        second L{Deferred}, the result of the second L{Deferred} becomes the
        result of the first L{Deferred} and the result of the first L{Deferred}
        becomes C{None}.
        """
        result = object()
        first = defer.succeed(result)
        second = defer.Deferred()
        second.addCallback(lambda ign: first)
        second.callback(None)

        results = []
        first.addCallback(results.append)
        self.assertIdentical(results[0], None)
        second.addCallback(results.append)
        self.assertIdentical(results[1], result)


    def test_asynchronousImplicitChain(self):
        """
        If a first L{Deferred} without a result is returned from a callback on
        a second L{Deferred}, the result of the second L{Deferred} becomes the
        result of the first L{Deferred} as soon as the first L{Deferred} has
        one and the result of the first L{Deferred} becomes C{None}.
        """
        first = defer.Deferred()
        second = defer.Deferred()
        second.addCallback(lambda ign: first)
        second.callback(None)

        firstResult = []
        first.addCallback(firstResult.append)
        secondResult = []
        second.addCallback(secondResult.append)

        self.assertEquals(firstResult, [])
        self.assertEquals(secondResult, [])

        result = object()
        first.callback(result)

        self.assertEquals(firstResult, [None])
        self.assertEquals(secondResult, [result])


    def test_synchronousImplicitErrorChain(self):
        """
        If a first L{Deferred} with a L{Failure} result is returned from a
        callback on a second L{Deferred}, the first L{Deferred}'s result is
        converted to L{None} and no unhandled error is logged when it is
        garbage collected.
        """
        first = defer.fail(RuntimeError("First Deferred's Failure"))
        second = defer.Deferred()
        second.addCallback(lambda ign, first=first: first)
        self.assertFailure(second, RuntimeError)
        second.callback(None)
        firstResult = []
        first.addCallback(firstResult.append)
        self.assertIdentical(firstResult[0], None)
        return second


    def test_asynchronousImplicitErrorChain(self):
        """
        Let C{a} and C{b} be two L{Deferred}s.

        If C{a} has no result and is returned from a callback on C{b} then when
        C{a} fails, C{b}'s result becomes the L{Failure} that was C{a}'s result,
        the result of C{a} becomes C{None} so that no unhandled error is logged
        when it is garbage collected.
        """
        first = defer.Deferred()
        second = defer.Deferred()
        second.addCallback(lambda ign: first)
        second.callback(None)
        self.assertFailure(second, RuntimeError)

        firstResult = []
        first.addCallback(firstResult.append)
        secondResult = []
        second.addCallback(secondResult.append)

        self.assertEquals(firstResult, [])
        self.assertEquals(secondResult, [])

        first.errback(RuntimeError("First Deferred's Failure"))

        self.assertEquals(firstResult, [None])
        self.assertEquals(len(secondResult), 1)


    def test_doubleAsynchronousImplicitChaining(self):
        """
        L{Deferred} chaining is transitive.

        In other words, let A, B, and C be Deferreds.  If C is returned from a
        callback on B and B is returned from a callback on A then when C fires,
        A fires.
        """
        first = defer.Deferred()
        second = defer.Deferred()
        second.addCallback(lambda ign: first)
        third = defer.Deferred()
        third.addCallback(lambda ign: second)

        thirdResult = []
        third.addCallback(thirdResult.append)

        result = object()
        # After this, second is waiting for first to tell it to continue.
        second.callback(None)
        # And after this, third is waiting for second to tell it to continue.
        third.callback(None)

        # Still waiting
        self.assertEquals(thirdResult, [])

        # This will tell second to continue which will tell third to continue.
        first.callback(result)

        self.assertEquals(thirdResult, [result])


    def test_nestedAsynchronousChainedDeferreds(self):
        """
        L{Deferred}s can have callbacks that themselves return L{Deferred}s.
        When these "inner" L{Deferred}s fire (even asynchronously), the
        callback chain continues.
        """
        results = []
        failures = []

        # A Deferred returned in the inner callback.
        inner = defer.Deferred()

        def cb(result):
            results.append(('start-of-cb', result))
            d = defer.succeed('inner')

            def firstCallback(result):
                results.append(('firstCallback', 'inner'))
                # Return a Deferred that definitely has not fired yet, so we
                # can fire the Deferreds out of order.
                return inner

            def secondCallback(result):
                results.append(('secondCallback', result))
                return result * 2

            d.addCallback(firstCallback).addCallback(secondCallback)
            d.addErrback(failures.append)
            return d

        # Create a synchronous Deferred that has a callback 'cb' that returns
        # a Deferred 'd' that has fired but is now waiting on an unfired
        # Deferred 'inner'.
        outer = defer.succeed('outer')
        outer.addCallback(cb)
        outer.addCallback(results.append)
        # At this point, the callback 'cb' has been entered, and the first
        # callback of 'd' has been called.
        self.assertEquals(
            results, [('start-of-cb', 'outer'), ('firstCallback', 'inner')])

        # Once the inner Deferred is fired, processing of the outer Deferred's
        # callback chain continues.
        inner.callback('orange')

        # Make sure there are no errors.
        inner.addErrback(failures.append)
        outer.addErrback(failures.append)
        self.assertEquals(
            [], failures, "Got errbacks but wasn't expecting any.")

        self.assertEquals(
            results,
            [('start-of-cb', 'outer'),
             ('firstCallback', 'inner'),
             ('secondCallback', 'orange'),
             'orangeorange'])


    def test_nestedAsynchronousChainedDeferredsWithExtraCallbacks(self):
        """
        L{Deferred}s can have callbacks that themselves return L{Deferred}s.
        These L{Deferred}s can have other callbacks added before they are
        returned, which subtly changes the callback chain. When these "inner"
        L{Deferred}s fire (even asynchronously), the outer callback chain
        continues.
        """
        results = []
        failures = []

        # A Deferred returned in the inner callback after a callback is
        # added explicitly and directly to it.
        inner = defer.Deferred()

        def cb(result):
            results.append(('start-of-cb', result))
            d = defer.succeed('inner')

            def firstCallback(ignored):
                results.append(('firstCallback', ignored))
                # Return a Deferred that definitely has not fired yet with a
                # result-transforming callback so we can fire the Deferreds
                # out of order and see how the callback affects the ultimate
                # results.
                return inner.addCallback(lambda x: [x])

            def secondCallback(result):
                results.append(('secondCallback', result))
                return result * 2

            d.addCallback(firstCallback)
            d.addCallback(secondCallback)
            d.addErrback(failures.append)
            return d

        # Create a synchronous Deferred that has a callback 'cb' that returns
        # a Deferred 'd' that has fired but is now waiting on an unfired
        # Deferred 'inner'.
        outer = defer.succeed('outer')
        outer.addCallback(cb)
        outer.addCallback(results.append)
        # At this point, the callback 'cb' has been entered, and the first
        # callback of 'd' has been called.
        self.assertEquals(
            results, [('start-of-cb', 'outer'), ('firstCallback', 'inner')])

        # Once the inner Deferred is fired, processing of the outer Deferred's
        # callback chain continues.
        inner.callback('withers')

        # Make sure there are no errors.
        outer.addErrback(failures.append)
        inner.addErrback(failures.append)
        self.assertEquals(
            [], failures, "Got errbacks but wasn't expecting any.")

        self.assertEquals(
            results,
            [('start-of-cb', 'outer'),
             ('firstCallback', 'inner'),
             ('secondCallback', ['withers']),
             ['withers', 'withers']])


    def test_chainDeferredRecordsExplicitChain(self):
        """
        When we chain a L{Deferred}, that chaining is recorded explicitly.
        """
        a = defer.Deferred()
        b = defer.Deferred()
        b.chainDeferred(a)
        self.assertIdentical(a._chainedTo, b)


    def test_explicitChainClearedWhenResolved(self):
        """
        Any recorded chaining is cleared once the chaining is resolved, since
        it no longer exists.

        In other words, if one L{Deferred} is recorded as depending on the
        result of another, and I{that} L{Deferred} has fired, then the
        dependency is resolved and we no longer benefit from recording it.
        """
        a = defer.Deferred()
        b = defer.Deferred()
        b.chainDeferred(a)
        b.callback(None)
        self.assertIdentical(a._chainedTo, None)


    def test_chainDeferredRecordsImplicitChain(self):
        """
        We can chain L{Deferred}s implicitly by adding callbacks that return
        L{Deferred}s. When this chaining happens, we record it explicitly as
        soon as we can find out about it.
        """
        a = defer.Deferred()
        b = defer.Deferred()
        a.addCallback(lambda ignored: b)
        a.callback(None)
        self.assertIdentical(a._chainedTo, b)


    def test_repr(self):
        """
        The C{repr()} of a L{Deferred} contains the class name and a
        representation of the internal Python ID.
        """
        d = defer.Deferred()
        address = hex(unsignedID(d))
        self.assertEquals(
            repr(d), '<Deferred at %s>' % (address,))


    def test_reprWithResult(self):
        """
        If a L{Deferred} has been fired, then its C{repr()} contains its
        result.
        """
        d = defer.Deferred()
        d.callback('orange')
        self.assertEquals(
            repr(d), "<Deferred at %s current result: 'orange'>" % (
                hex(unsignedID(d))))


    def test_reprWithChaining(self):
        """
        If a L{Deferred} C{a} has been fired, but is waiting on another
        L{Deferred} C{b} that appears in its callback chain, then C{repr(a)}
        says that it is waiting on C{b}.
        """
        a = defer.Deferred()
        b = defer.Deferred()
        b.chainDeferred(a)
        self.assertEquals(
            repr(a), "<Deferred at %s waiting on Deferred at %s>" % (
                hex(unsignedID(a)), hex(unsignedID(b))))


    def test_boundedStackDepth(self):
        """
        The depth of the call stack does not grow as more L{Deferred} instances
        are chained together.
        """
        def chainDeferreds(howMany):
            stack = []
            def recordStackDepth(ignored):
                stack.append(len(traceback.extract_stack()))

            top = defer.Deferred()
            innerDeferreds = [defer.Deferred() for ignored in range(howMany)]
            originalInners = innerDeferreds[:]
            last = defer.Deferred()

            inner = innerDeferreds.pop()
            top.addCallback(lambda ign, inner=inner: inner)
            top.addCallback(recordStackDepth)

            while innerDeferreds:
                newInner = innerDeferreds.pop()
                inner.addCallback(lambda ign, inner=newInner: inner)
                inner = newInner
            inner.addCallback(lambda ign: last)

            top.callback(None)
            for inner in originalInners:
                inner.callback(None)

            # Sanity check - the record callback is not intended to have
            # fired yet.
            self.assertEquals(stack, [])

            # Now fire the last thing and return the stack depth at which the
            # callback was invoked.
            last.callback(None)
            return stack[0]

        # Callbacks should be invoked at the same stack depth regardless of
        # how many Deferreds are chained.
        self.assertEquals(chainDeferreds(1), chainDeferreds(2))


    def test_resultOfDeferredResultOfDeferredOfFiredDeferredCalled(self):
        """
        Given three Deferreds, one chained to the next chained to the next,
        callbacks on the middle Deferred which are added after the chain is
        created are called once the last Deferred fires.

        This is more of a regression-style test.  It doesn't exercise any
        particular code path through the current implementation of Deferred, but
        it does exercise a broken codepath through one of the variations of the
        implementation proposed as a resolution to ticket #411.
        """
        first = defer.Deferred()
        second = defer.Deferred()
        third = defer.Deferred()
        first.addCallback(lambda ignored: second)
        second.addCallback(lambda ignored: third)
        second.callback(None)
        first.callback(None)
        third.callback(None)
        L = []
        second.addCallback(L.append)
        self.assertEquals(L, [None])



class FirstErrorTests(unittest.TestCase):
    """
    Tests for L{FirstError}.
    """
    def test_repr(self):
        """
        The repr of a L{FirstError} instance includes the repr of the value of
        the sub-failure and the index which corresponds to the L{FirstError}.
        """
        exc = ValueError("some text")
        try:
            raise exc
        except:
            f = failure.Failure()

        error = defer.FirstError(f, 3)
        self.assertEqual(
            repr(error),
            "FirstError[#3, %s]" % (repr(exc),))


    def test_str(self):
        """
        The str of a L{FirstError} instance includes the str of the
        sub-failure and the index which corresponds to the L{FirstError}.
        """
        exc = ValueError("some text")
        try:
            raise exc
        except:
            f = failure.Failure()

        error = defer.FirstError(f, 5)
        self.assertEqual(
            str(error),
            "FirstError[#5, %s]" % (str(f),))


    def test_comparison(self):
        """
        L{FirstError} instances compare equal to each other if and only if
        their failure and index compare equal.  L{FirstError} instances do not
        compare equal to instances of other types.
        """
        try:
            1 / 0
        except:
            firstFailure = failure.Failure()

        one = defer.FirstError(firstFailure, 13)
        anotherOne = defer.FirstError(firstFailure, 13)

        try:
            raise ValueError("bar")
        except:
            secondFailure = failure.Failure()

        another = defer.FirstError(secondFailure, 9)

        self.assertTrue(one == anotherOne)
        self.assertFalse(one == another)
        self.assertTrue(one != another)
        self.assertFalse(one != anotherOne)

        self.assertFalse(one == 10)



class AlreadyCalledTestCase(unittest.TestCase):
    def setUp(self):
        self._deferredWasDebugging = defer.getDebugging()
        defer.setDebugging(True)

    def tearDown(self):
        defer.setDebugging(self._deferredWasDebugging)

    def _callback(self, *args, **kw):
        pass
    def _errback(self, *args, **kw):
        pass

    def _call_1(self, d):
        d.callback("hello")
    def _call_2(self, d):
        d.callback("twice")
    def _err_1(self, d):
        d.errback(failure.Failure(RuntimeError()))
    def _err_2(self, d):
        d.errback(failure.Failure(RuntimeError()))

    def testAlreadyCalled_CC(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._call_1(d)
        self.failUnlessRaises(defer.AlreadyCalledError, self._call_2, d)

    def testAlreadyCalled_CE(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._call_1(d)
        self.failUnlessRaises(defer.AlreadyCalledError, self._err_2, d)

    def testAlreadyCalled_EE(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._err_1(d)
        self.failUnlessRaises(defer.AlreadyCalledError, self._err_2, d)

    def testAlreadyCalled_EC(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._err_1(d)
        self.failUnlessRaises(defer.AlreadyCalledError, self._call_2, d)


    def _count(self, linetype, func, lines, expected):
        count = 0
        for line in lines:
            if (line.startswith(' %s:' % linetype) and
                line.endswith(' %s' % func)):
                count += 1
        self.failUnless(count == expected)

    def _check(self, e, caller, invoker1, invoker2):
        # make sure the debugging information is vaguely correct
        lines = e.args[0].split("\n")
        # the creator should list the creator (testAlreadyCalledDebug) but not
        # _call_1 or _call_2 or other invokers
        self._count('C', caller, lines, 1)
        self._count('C', '_call_1', lines, 0)
        self._count('C', '_call_2', lines, 0)
        self._count('C', '_err_1', lines, 0)
        self._count('C', '_err_2', lines, 0)
        # invoker should list the first invoker but not the second
        self._count('I', invoker1, lines, 1)
        self._count('I', invoker2, lines, 0)

    def testAlreadyCalledDebug_CC(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._call_1(d)
        try:
            self._call_2(d)
        except defer.AlreadyCalledError, e:
            self._check(e, "testAlreadyCalledDebug_CC", "_call_1", "_call_2")
        else:
            self.fail("second callback failed to raise AlreadyCalledError")

    def testAlreadyCalledDebug_CE(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._call_1(d)
        try:
            self._err_2(d)
        except defer.AlreadyCalledError, e:
            self._check(e, "testAlreadyCalledDebug_CE", "_call_1", "_err_2")
        else:
            self.fail("second errback failed to raise AlreadyCalledError")

    def testAlreadyCalledDebug_EC(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._err_1(d)
        try:
            self._call_2(d)
        except defer.AlreadyCalledError, e:
            self._check(e, "testAlreadyCalledDebug_EC", "_err_1", "_call_2")
        else:
            self.fail("second callback failed to raise AlreadyCalledError")

    def testAlreadyCalledDebug_EE(self):
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._err_1(d)
        try:
            self._err_2(d)
        except defer.AlreadyCalledError, e:
            self._check(e, "testAlreadyCalledDebug_EE", "_err_1", "_err_2")
        else:
            self.fail("second errback failed to raise AlreadyCalledError")

    def testNoDebugging(self):
        defer.setDebugging(False)
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        self._call_1(d)
        try:
            self._call_2(d)
        except defer.AlreadyCalledError, e:
            self.failIf(e.args)
        else:
            self.fail("second callback failed to raise AlreadyCalledError")


    def testSwitchDebugging(self):
        # Make sure Deferreds can deal with debug state flipping
        # around randomly.  This is covering a particular fixed bug.
        defer.setDebugging(False)
        d = defer.Deferred()
        d.addBoth(lambda ign: None)
        defer.setDebugging(True)
        d.callback(None)

        defer.setDebugging(False)
        d = defer.Deferred()
        d.callback(None)
        defer.setDebugging(True)
        d.addBoth(lambda ign: None)



class DeferredCancellerTest(unittest.TestCase):
    def setUp(self):
        self.callbackResults = None
        self.errbackResults = None
        self.callback2Results = None
        self.cancellerCallCount = 0


    def tearDown(self):
        # Sanity check that the canceller was called at most once.
        self.assertTrue(self.cancellerCallCount in (0, 1))


    def _callback(self, data):
        self.callbackResults = data
        return data


    def _callback2(self, data):
        self.callback2Results = data


    def _errback(self, data):
        self.errbackResults = data


    def test_noCanceller(self):
        """
        A L{defer.Deferred} without a canceller must errback with a
        L{defer.CancelledError} and not callback.
        """
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        self.assertEquals(self.errbackResults.type, defer.CancelledError)
        self.assertEquals(self.callbackResults, None)


    def test_raisesAfterCancelAndCallback(self):
        """
        A L{defer.Deferred} without a canceller, when cancelled must allow
        a single extra call to callback, and raise
        L{defer.AlreadyCalledError} if callbacked or errbacked thereafter.
        """
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        d.cancel()

        # A single extra callback should be swallowed.
        d.callback(None)

        # But a second call to callback or errback is not.
        self.assertRaises(defer.AlreadyCalledError, d.callback, None)
        self.assertRaises(defer.AlreadyCalledError, d.errback, Exception())


    def test_raisesAfterCancelAndErrback(self):
        """
        A L{defer.Deferred} without a canceller, when cancelled must allow
        a single extra call to errback, and raise
        L{defer.AlreadyCalledError} if callbacked or errbacked thereafter.
        """
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        d.cancel()

        # A single extra errback should be swallowed.
        d.errback(Exception())

        # But a second call to callback or errback is not.
        self.assertRaises(defer.AlreadyCalledError, d.callback, None)
        self.assertRaises(defer.AlreadyCalledError, d.errback, Exception())


    def test_noCancellerMultipleCancelsAfterCancelAndCallback(self):
        """
        A L{Deferred} without a canceller, when cancelled and then
        callbacked, ignores multiple cancels thereafter.
        """
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        currentFailure = self.errbackResults
        # One callback will be ignored
        d.callback(None)
        # Cancel should have no effect.
        d.cancel()
        self.assertIdentical(currentFailure, self.errbackResults)


    def test_noCancellerMultipleCancelsAfterCancelAndErrback(self):
        """
        A L{defer.Deferred} without a canceller, when cancelled and then
        errbacked, ignores multiple cancels thereafter.
        """
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        self.assertEquals(self.errbackResults.type, defer.CancelledError)
        currentFailure = self.errbackResults
        # One errback will be ignored
        d.errback(GenericError())
        # I.e., we should still have a CancelledError.
        self.assertEquals(self.errbackResults.type, defer.CancelledError)
        d.cancel()
        self.assertIdentical(currentFailure, self.errbackResults)


    def test_noCancellerMultipleCancel(self):
        """
        Calling cancel multiple times on a deferred with no canceller
        results in a L{defer.CancelledError}. Subsequent calls to cancel
        do not cause an error.
        """
        d = defer.Deferred()
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        self.assertEquals(self.errbackResults.type, defer.CancelledError)
        currentFailure = self.errbackResults
        d.cancel()
        self.assertIdentical(currentFailure, self.errbackResults)


    def test_cancellerMultipleCancel(self):
        """
        Verify that calling cancel multiple times on a deferred with a
        canceller that does not errback results in a
        L{defer.CancelledError} and that subsequent calls to cancel do not
        cause an error and that after all that, the canceller was only
        called once.
        """
        def cancel(d):
            self.cancellerCallCount += 1

        d = defer.Deferred(canceller=cancel)
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        self.assertEquals(self.errbackResults.type, defer.CancelledError)
        currentFailure = self.errbackResults
        d.cancel()
        self.assertIdentical(currentFailure, self.errbackResults)
        self.assertEquals(self.cancellerCallCount, 1)


    def test_simpleCanceller(self):
        """
        Verify that a L{defer.Deferred} calls its specified canceller when
        it is cancelled, and that further call/errbacks raise
        L{defer.AlreadyCalledError}.
        """
        def cancel(d):
            self.cancellerCallCount += 1

        d = defer.Deferred(canceller=cancel)
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        self.assertEquals(self.cancellerCallCount, 1)
        self.assertEquals(self.errbackResults.type, defer.CancelledError)

        # Test that further call/errbacks are *not* swallowed
        self.assertRaises(defer.AlreadyCalledError, d.callback, None)
        self.assertRaises(defer.AlreadyCalledError, d.errback, Exception())


    def test_cancellerArg(self):
        """
        Verify that a canceller is given the correct deferred argument.
        """
        def cancel(d1):
            self.assertIdentical(d1, d)
        d = defer.Deferred(canceller=cancel)
        d.addCallbacks(self._callback, self._errback)
        d.cancel()


    def test_cancelAfterCallback(self):
        """
        Test that cancelling a deferred after it has been callbacked does
        not cause an error.
        """
        def cancel(d):
            self.cancellerCallCount += 1
            d.errback(GenericError())
        d = defer.Deferred(canceller=cancel)
        d.addCallbacks(self._callback, self._errback)
        d.callback('biff!')
        d.cancel()
        self.assertEquals(self.cancellerCallCount, 0)
        self.assertEquals(self.errbackResults, None)
        self.assertEquals(self.callbackResults, 'biff!')


    def test_cancelAfterErrback(self):
        """
        Test that cancelling a L{Deferred} after it has been errbacked does
        not result in a L{defer.CancelledError}.
        """
        def cancel(d):
            self.cancellerCallCount += 1
            d.errback(GenericError())
        d = defer.Deferred(canceller=cancel)
        d.addCallbacks(self._callback, self._errback)
        d.errback(GenericError())
        d.cancel()
        self.assertEquals(self.cancellerCallCount, 0)
        self.assertEquals(self.errbackResults.type, GenericError)
        self.assertEquals(self.callbackResults, None)


    def test_cancellerThatErrbacks(self):
        """
        Test a canceller which errbacks its deferred.
        """
        def cancel(d):
            self.cancellerCallCount += 1
            d.errback(GenericError())
        d = defer.Deferred(canceller=cancel)
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        self.assertEquals(self.cancellerCallCount, 1)
        self.assertEquals(self.errbackResults.type, GenericError)


    def test_cancellerThatCallbacks(self):
        """
        Test a canceller which calls its deferred.
        """
        def cancel(d):
            self.cancellerCallCount += 1
            d.callback('hello!')
        d = defer.Deferred(canceller=cancel)
        d.addCallbacks(self._callback, self._errback)
        d.cancel()
        self.assertEquals(self.cancellerCallCount, 1)
        self.assertEquals(self.callbackResults, 'hello!')
        self.assertEquals(self.errbackResults, None)


    def test_cancelNestedDeferred(self):
        """
        Verify that a Deferred, a, which is waiting on another Deferred, b,
        returned from one of its callbacks, will propagate
        L{defer.CancelledError} when a is cancelled.
        """
        def innerCancel(d):
            self.cancellerCallCount += 1
        def cancel(d):
            self.assert_(False)

        b = defer.Deferred(canceller=innerCancel)
        a = defer.Deferred(canceller=cancel)
        a.callback(None)
        a.addCallback(lambda data: b)
        a.cancel()
        a.addCallbacks(self._callback, self._errback)
        # The cancel count should be one (the cancellation done by B)
        self.assertEquals(self.cancellerCallCount, 1)
        # B's canceller didn't errback, so defer.py will have called errback
        # with a CancelledError.
        self.assertEquals(self.errbackResults.type, defer.CancelledError)



class LogTestCase(unittest.TestCase):
    """
    Test logging of unhandled errors.
    """

    def setUp(self):
        """
        Add a custom observer to observer logging.
        """
        self.c = []
        log.addObserver(self.c.append)

    def tearDown(self):
        """
        Remove the observer.
        """
        log.removeObserver(self.c.append)


    def _loggedErrors(self):
        return [e for e in self.c if e["isError"]]


    def _check(self):
        """
        Check the output of the log observer to see if the error is present.
        """
        c2 = self._loggedErrors()
        self.assertEquals(len(c2), 2)
        c2[1]["failure"].trap(ZeroDivisionError)
        self.flushLoggedErrors(ZeroDivisionError)

    def test_errorLog(self):
        """
        Verify that when a L{Deferred} with no references to it is fired,
        and its final result (the one not handled by any callback) is an
        exception, that exception will be logged immediately.
        """
        defer.Deferred().addCallback(lambda x: 1 / 0).callback(1)
        gc.collect()
        self._check()

    def test_errorLogWithInnerFrameRef(self):
        """
        Same as L{test_errorLog}, but with an inner frame.
        """
        def _subErrorLogWithInnerFrameRef():
            d = defer.Deferred()
            d.addCallback(lambda x: 1 / 0)
            d.callback(1)

        _subErrorLogWithInnerFrameRef()
        gc.collect()
        self._check()

    def test_errorLogWithInnerFrameCycle(self):
        """
        Same as L{test_errorLogWithInnerFrameRef}, plus create a cycle.
        """
        def _subErrorLogWithInnerFrameCycle():
            d = defer.Deferred()
            d.addCallback(lambda x, d=d: 1 / 0)
            d._d = d
            d.callback(1)

        _subErrorLogWithInnerFrameCycle()
        gc.collect()
        self._check()


    def test_chainedErrorCleanup(self):
        """
        If one Deferred with an error result is returned from a callback on
        another Deferred, when the first Deferred is garbage collected it does
        not log its error.
        """
        d = defer.Deferred()
        d.addCallback(lambda ign: defer.fail(RuntimeError("zoop")))
        d.callback(None)

        # Sanity check - this isn't too interesting, but we do want the original
        # Deferred to have gotten the failure.
        results = []
        errors = []
        d.addCallbacks(results.append, errors.append)
        self.assertEquals(results, [])
        self.assertEquals(len(errors), 1)
        errors[0].trap(Exception)

        # Get rid of any references we might have to the inner Deferred (none of
        # these should really refer to it, but we're just being safe).
        del results, errors, d
        # Force a collection cycle so that there's a chance for an error to be
        # logged, if it's going to be logged.
        gc.collect()
        # And make sure it is not.
        self.assertEquals(self._loggedErrors(), [])


    def test_errorClearedByChaining(self):
        """
        If a Deferred with a failure result has an errback which chains it to
        another Deferred, the initial failure is cleared by the errback so it is
        not logged.
        """
        # Start off with a Deferred with a failure for a result
        bad = defer.fail(Exception("oh no"))
        good = defer.Deferred()
        # Give it a callback that chains it to another Deferred
        bad.addErrback(lambda ignored: good)
        # That's all, clean it up.  No Deferred here still has a failure result,
        # so nothing should be logged.
        good = bad = None
        gc.collect()
        self.assertEquals(self._loggedErrors(), [])



class DeferredTestCaseII(unittest.TestCase):
    def setUp(self):
        self.callbackRan = 0

    def testDeferredListEmpty(self):
        """Testing empty DeferredList."""
        dl = defer.DeferredList([])
        dl.addCallback(self.cb_empty)

    def cb_empty(self, res):
        self.callbackRan = 1
        self.failUnlessEqual([], res)

    def tearDown(self):
        self.failUnless(self.callbackRan, "Callback was never run.")

class OtherPrimitives(unittest.TestCase):
    def _incr(self, result):
        self.counter += 1

    def setUp(self):
        self.counter = 0

    def testLock(self):
        lock = defer.DeferredLock()
        lock.acquire().addCallback(self._incr)
        self.failUnless(lock.locked)
        self.assertEquals(self.counter, 1)

        lock.acquire().addCallback(self._incr)
        self.failUnless(lock.locked)
        self.assertEquals(self.counter, 1)

        lock.release()
        self.failUnless(lock.locked)
        self.assertEquals(self.counter, 2)

        lock.release()
        self.failIf(lock.locked)
        self.assertEquals(self.counter, 2)

        self.assertRaises(TypeError, lock.run)

        firstUnique = object()
        secondUnique = object()

        controlDeferred = defer.Deferred()
        def helper(self, b):
            self.b = b
            return controlDeferred

        resultDeferred = lock.run(helper, self=self, b=firstUnique)
        self.failUnless(lock.locked)
        self.assertEquals(self.b, firstUnique)

        resultDeferred.addCallback(lambda x: setattr(self, 'result', x))

        lock.acquire().addCallback(self._incr)
        self.failUnless(lock.locked)
        self.assertEquals(self.counter, 2)

        controlDeferred.callback(secondUnique)
        self.assertEquals(self.result, secondUnique)
        self.failUnless(lock.locked)
        self.assertEquals(self.counter, 3)

        d = lock.acquire().addBoth(lambda x: setattr(self, 'result', x))
        d.cancel()
        self.assertEquals(self.result.type, defer.CancelledError)

        lock.release()
        self.failIf(lock.locked)


    def test_cancelLockAfterAcquired(self):
        """
        When canceling a L{Deferred} from a L{DeferredLock} that already
        has the lock, the cancel should have no effect.
        """
        def _failOnErrback(_):
            self.fail("Unexpected errback call!")
        lock = defer.DeferredLock()
        d = lock.acquire()
        d.addErrback(_failOnErrback)
        d.cancel()


    def test_cancelLockBeforeAcquired(self):
        """
        When canceling a L{Deferred} from a L{DeferredLock} that does not
        yet have the lock (i.e., the L{Deferred} has not fired), the cancel
        should cause a L{defer.CancelledError} failure.
        """
        lock = defer.DeferredLock()
        lock.acquire()
        d = lock.acquire()
        self.assertFailure(d, defer.CancelledError)
        d.cancel()


    def testSemaphore(self):
        N = 13
        sem = defer.DeferredSemaphore(N)

        controlDeferred = defer.Deferred()
        def helper(self, arg):
            self.arg = arg
            return controlDeferred

        results = []
        uniqueObject = object()
        resultDeferred = sem.run(helper, self=self, arg=uniqueObject)
        resultDeferred.addCallback(results.append)
        resultDeferred.addCallback(self._incr)
        self.assertEquals(results, [])
        self.assertEquals(self.arg, uniqueObject)
        controlDeferred.callback(None)
        self.assertEquals(results.pop(), None)
        self.assertEquals(self.counter, 1)

        self.counter = 0
        for i in range(1, 1 + N):
            sem.acquire().addCallback(self._incr)
            self.assertEquals(self.counter, i)


        success = []
        def fail(r):
            success.append(False)
        def succeed(r):
            success.append(True)
        d = sem.acquire().addCallbacks(fail, succeed)
        d.cancel()
        self.assertEquals(success, [True])

        sem.acquire().addCallback(self._incr)
        self.assertEquals(self.counter, N)

        sem.release()
        self.assertEquals(self.counter, N + 1)

        for i in range(1, 1 + N):
            sem.release()
            self.assertEquals(self.counter, N + 1)


    def test_semaphoreInvalidTokens(self):
        """
        If the token count passed to L{DeferredSemaphore} is less than one
        then L{ValueError} is raised.
        """
        self.assertRaises(ValueError, defer.DeferredSemaphore, 0)
        self.assertRaises(ValueError, defer.DeferredSemaphore, -1)


    def test_cancelSemaphoreAfterAcquired(self):
        """
        When canceling a L{Deferred} from a L{DeferredSemaphore} that
        already has the semaphore, the cancel should have no effect.
        """
        def _failOnErrback(_):
            self.fail("Unexpected errback call!")

        sem = defer.DeferredSemaphore(1)
        d = sem.acquire()
        d.addErrback(_failOnErrback)
        d.cancel()


    def test_cancelSemaphoreBeforeAcquired(self):
        """
        When canceling a L{Deferred} from a L{DeferredSemaphore} that does
        not yet have the semaphore (i.e., the L{Deferred} has not fired),
        the cancel should cause a L{defer.CancelledError} failure.
        """
        sem = defer.DeferredSemaphore(1)
        sem.acquire()
        d = sem.acquire()
        self.assertFailure(d, defer.CancelledError)
        d.cancel()
        return d


    def testQueue(self):
        N, M = 2, 2
        queue = defer.DeferredQueue(N, M)

        gotten = []

        for i in range(M):
            queue.get().addCallback(gotten.append)
        self.assertRaises(defer.QueueUnderflow, queue.get)

        for i in range(M):
            queue.put(i)
            self.assertEquals(gotten, range(i + 1))
        for i in range(N):
            queue.put(N + i)
            self.assertEquals(gotten, range(M))
        self.assertRaises(defer.QueueOverflow, queue.put, None)

        gotten = []
        for i in range(N):
            queue.get().addCallback(gotten.append)
            self.assertEquals(gotten, range(N, N + i + 1))

        queue = defer.DeferredQueue()
        gotten = []
        for i in range(N):
            queue.get().addCallback(gotten.append)
        for i in range(N):
            queue.put(i)
        self.assertEquals(gotten, range(N))

        queue = defer.DeferredQueue(size=0)
        self.assertRaises(defer.QueueOverflow, queue.put, None)

        queue = defer.DeferredQueue(backlog=0)
        self.assertRaises(defer.QueueUnderflow, queue.get)


    def test_cancelQueueAfterSynchronousGet(self):
        """
        When canceling a L{Deferred} from a L{DeferredQueue} that already has
        a result, the cancel should have no effect.
        """
        def _failOnErrback(_):
            self.fail("Unexpected errback call!")

        queue = defer.DeferredQueue()
        d = queue.get()
        d.addErrback(_failOnErrback)
        queue.put(None)
        d.cancel()


    def test_cancelQueueAfterGet(self):
        """
        When canceling a L{Deferred} from a L{DeferredQueue} that does not
        have a result (i.e., the L{Deferred} has not fired), the cancel
        causes a L{defer.CancelledError} failure. If the queue has a result
        later on, it doesn't try to fire the deferred.
        """
        queue = defer.DeferredQueue()
        d = queue.get()
        self.assertFailure(d, defer.CancelledError)
        d.cancel()
        def cb(ignore):
            # If the deferred is still linked with the deferred queue, it will
            # fail with an AlreadyCalledError
            queue.put(None)
            return queue.get().addCallback(self.assertIdentical, None)
        return d.addCallback(cb)



class DeferredFilesystemLockTestCase(unittest.TestCase):
    """
    Test the behavior of L{DeferredFilesystemLock}
    """
    def setUp(self):
        self.clock = Clock()
        self.lock = defer.DeferredFilesystemLock(self.mktemp(),
                                                 scheduler=self.clock)


    def test_waitUntilLockedWithNoLock(self):
        """
        Test that the lock can be acquired when no lock is held
        """
        d = self.lock.deferUntilLocked(timeout=1)

        return d


    def test_waitUntilLockedWithTimeoutLocked(self):
        """
        Test that the lock can not be acquired when the lock is held
        for longer than the timeout.
        """
        self.failUnless(self.lock.lock())

        d = self.lock.deferUntilLocked(timeout=5.5)
        self.assertFailure(d, defer.TimeoutError)

        self.clock.pump([1] * 10)

        return d


    def test_waitUntilLockedWithTimeoutUnlocked(self):
        """
        Test that a lock can be acquired while a lock is held
        but the lock is unlocked before our timeout.
        """
        def onTimeout(f):
            f.trap(defer.TimeoutError)
            self.fail("Should not have timed out")

        self.failUnless(self.lock.lock())

        self.clock.callLater(1, self.lock.unlock)
        d = self.lock.deferUntilLocked(timeout=10)
        d.addErrback(onTimeout)

        self.clock.pump([1] * 10)

        return d


    def test_defaultScheduler(self):
        """
        Test that the default scheduler is set up properly.
        """
        lock = defer.DeferredFilesystemLock(self.mktemp())

        self.assertEquals(lock._scheduler, reactor)


    def test_concurrentUsage(self):
        """
        Test that an appropriate exception is raised when attempting
        to use deferUntilLocked concurrently.
        """
        self.lock.lock()
        self.clock.callLater(1, self.lock.unlock)

        d = self.lock.deferUntilLocked()
        d2 = self.lock.deferUntilLocked()

        self.assertFailure(d2, defer.AlreadyTryingToLockError)

        self.clock.advance(1)

        return d


    def test_multipleUsages(self):
        """
        Test that a DeferredFilesystemLock can be used multiple times
        """
        def lockAquired(ign):
            self.lock.unlock()
            d = self.lock.deferUntilLocked()
            return d

        self.lock.lock()
        self.clock.callLater(1, self.lock.unlock)

        d = self.lock.deferUntilLocked()
        d.addCallback(lockAquired)

        self.clock.advance(1)

        return d
