# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
This module contains tests for L{twisted.internet.task.Cooperator} and
related functionality.
"""

from twisted.internet import reactor, defer, task
from twisted.trial import unittest



class FakeDelayedCall(object):
    """
    Fake delayed call which lets us simulate the scheduler.
    """
    def __init__(self, func):
        """
        A function to run, later.
        """
        self.func = func
        self.cancelled = False


    def cancel(self):
        """
        Don't run my function later.
        """
        self.cancelled = True



class FakeScheduler(object):
    """
    A fake scheduler for testing against.
    """
    def __init__(self):
        """
        Create a fake scheduler with a list of work to do.
        """
        self.work = []


    def __call__(self, thunk):
        """
        Schedule a unit of work to be done later.
        """
        unit = FakeDelayedCall(thunk)
        self.work.append(unit)
        return unit


    def pump(self):
        """
        Do all of the work that is currently available to be done.
        """
        work, self.work = self.work, []
        for unit in work:
            if not unit.cancelled:
                unit.func()



class TestCooperator(unittest.TestCase):
    RESULT = 'done'

    def ebIter(self, err):
        err.trap(task.SchedulerStopped)
        return self.RESULT


    def cbIter(self, ign):
        self.fail()


    def testStoppedRejectsNewTasks(self):
        """
        Test that Cooperators refuse new tasks when they have been stopped.
        """
        def testwith(stuff):
            c = task.Cooperator()
            c.stop()
            d = c.coiterate(iter(()), stuff)
            d.addCallback(self.cbIter)
            d.addErrback(self.ebIter)
            return d.addCallback(lambda result:
                                 self.assertEquals(result, self.RESULT))
        return testwith(None).addCallback(lambda ign: testwith(defer.Deferred()))


    def testStopRunning(self):
        """
        Test that a running iterator will not run to completion when the
        cooperator is stopped.
        """
        c = task.Cooperator()
        def myiter():
            for myiter.value in range(3):
                yield myiter.value
        myiter.value = -1
        d = c.coiterate(myiter())
        d.addCallback(self.cbIter)
        d.addErrback(self.ebIter)
        c.stop()
        def doasserts(result):
            self.assertEquals(result, self.RESULT)
            self.assertEquals(myiter.value, -1)
        d.addCallback(doasserts)
        return d


    def testStopOutstanding(self):
        """
        An iterator run with L{Cooperator.coiterate} paused on a L{Deferred}
        yielded by that iterator will fire its own L{Deferred} (the one
        returned by C{coiterate}) when L{Cooperator.stop} is called.
        """
        testControlD = defer.Deferred()
        outstandingD = defer.Deferred()
        def myiter():
            reactor.callLater(0, testControlD.callback, None)
            yield outstandingD
            self.fail()
        c = task.Cooperator()
        d = c.coiterate(myiter())
        def stopAndGo(ign):
            c.stop()
            outstandingD.callback('arglebargle')

        testControlD.addCallback(stopAndGo)
        d.addCallback(self.cbIter)
        d.addErrback(self.ebIter)

        return d.addCallback(
            lambda result: self.assertEquals(result, self.RESULT))


    def testUnexpectedError(self):
        c = task.Cooperator()
        def myiter():
            if 0:
                yield None
            else:
                raise RuntimeError()
        d = c.coiterate(myiter())
        return self.assertFailure(d, RuntimeError)


    def testUnexpectedErrorActuallyLater(self):
        def myiter():
            D = defer.Deferred()
            reactor.callLater(0, D.errback, RuntimeError())
            yield D

        c = task.Cooperator()
        d = c.coiterate(myiter())
        return self.assertFailure(d, RuntimeError)


    def testUnexpectedErrorNotActuallyLater(self):
        def myiter():
            yield defer.fail(RuntimeError())

        c = task.Cooperator()
        d = c.coiterate(myiter())
        return self.assertFailure(d, RuntimeError)


    def testCooperation(self):
        L = []
        def myiter(things):
            for th in things:
                L.append(th)
                yield None

        groupsOfThings = ['abc', (1, 2, 3), 'def', (4, 5, 6)]

        c = task.Cooperator()
        tasks = []
        for stuff in groupsOfThings:
            tasks.append(c.coiterate(myiter(stuff)))

        return defer.DeferredList(tasks).addCallback(
            lambda ign: self.assertEquals(tuple(L), sum(zip(*groupsOfThings), ())))


    def testResourceExhaustion(self):
        output = []
        def myiter():
            for i in range(100):
                output.append(i)
                if i == 9:
                    _TPF.stopped = True
                yield i

        class _TPF:
            stopped = False
            def __call__(self):
                return self.stopped

        c = task.Cooperator(terminationPredicateFactory=_TPF)
        c.coiterate(myiter()).addErrback(self.ebIter)
        c._delayedCall.cancel()
        # testing a private method because only the test case will ever care
        # about this, so we have to carefully clean up after ourselves.
        c._tick()
        c.stop()
        self.failUnless(_TPF.stopped)
        self.assertEquals(output, range(10))


    def testCallbackReCoiterate(self):
        """
        If a callback to a deferred returned by coiterate calls coiterate on
        the same Cooperator, we should make sure to only do the minimal amount
        of scheduling work.  (This test was added to demonstrate a specific bug
        that was found while writing the scheduler.)
        """
        calls = []

        class FakeCall:
            def __init__(self, func):
                self.func = func

            def __repr__(self):
                return '<FakeCall %r>' % (self.func,)

        def sched(f):
            self.failIf(calls, repr(calls))
            calls.append(FakeCall(f))
            return calls[-1]

        c = task.Cooperator(scheduler=sched, terminationPredicateFactory=lambda: lambda: True)
        d = c.coiterate(iter(()))

        done = []
        def anotherTask(ign):
            c.coiterate(iter(())).addBoth(done.append)

        d.addCallback(anotherTask)

        work = 0
        while not done:
            work += 1
            while calls:
                calls.pop(0).func()
                work += 1
            if work > 50:
                self.fail("Cooperator took too long")



class UnhandledException(Exception):
    """
    An exception that should go unhandled.
    """



class AliasTests(unittest.TestCase):
    """
    Integration test to verify that the global singleton aliases do what
    they're supposed to.
    """

    def test_cooperate(self):
        """
        L{twisted.internet.task.cooperate} ought to run the generator that it is
        """
        d = defer.Deferred()
        def doit():
            yield 1
            yield 2
            yield 3
            d.callback("yay")
        it = doit()
        theTask = task.cooperate(it)
        self.assertIn(theTask, task._theCooperator._tasks)
        return d



class RunStateTests(unittest.TestCase):
    """
    Tests to verify the behavior of L{CooperativeTask.pause},
    L{CooperativeTask.resume}, L{CooperativeTask.stop}, exhausting the
    underlying iterator, and their interactions with each other.
    """

    def setUp(self):
        """
        Create a cooperator with a fake scheduler and a termination predicate
        that ensures only one unit of work will take place per tick.
        """
        self._doDeferNext = False
        self._doStopNext = False
        self._doDieNext = False
        self.work = []
        self.scheduler = FakeScheduler()
        self.cooperator = task.Cooperator(
            scheduler=self.scheduler,
            # Always stop after one iteration of work (return a function which
            # returns a function which always returns True)
            terminationPredicateFactory=lambda: lambda: True)
        self.task = self.cooperator.cooperate(self.worker())
        self.cooperator.start()


    def worker(self):
        """
        This is a sample generator which yields Deferreds when we are testing
        deferral and an ascending integer count otherwise.
        """
        i = 0
        while True:
            i += 1
            if self._doDeferNext:
                self._doDeferNext = False
                d = defer.Deferred()
                self.work.append(d)
                yield d
            elif self._doStopNext:
                return
            elif self._doDieNext:
                raise UnhandledException()
            else:
                self.work.append(i)
                yield i


    def tearDown(self):
        """
        Drop references to interesting parts of the fixture to allow Deferred
        errors to be noticed when things start failing.
        """
        del self.task
        del self.scheduler


    def deferNext(self):
        """
        Defer the next result from my worker iterator.
        """
        self._doDeferNext = True


    def stopNext(self):
        """
        Make the next result from my worker iterator be completion (raising
        StopIteration).
        """
        self._doStopNext = True


    def dieNext(self):
        """
        Make the next result from my worker iterator be raising an
        L{UnhandledException}.
        """
        def ignoreUnhandled(failure):
            failure.trap(UnhandledException)
            return None
        self._doDieNext = True


    def test_pauseResume(self):
        """
        Cooperators should stop running their tasks when they're paused, and
        start again when they're resumed.
        """
        # first, sanity check
        self.scheduler.pump()
        self.assertEquals(self.work, [1])
        self.scheduler.pump()
        self.assertEquals(self.work, [1, 2])

        # OK, now for real
        self.task.pause()
        self.scheduler.pump()
        self.assertEquals(self.work, [1, 2])
        self.task.resume()
        # Resuming itself shoult not do any work
        self.assertEquals(self.work, [1, 2])
        self.scheduler.pump()
        # But when the scheduler rolls around again...
        self.assertEquals(self.work, [1, 2, 3])


    def test_resumeNotPaused(self):
        """
        L{CooperativeTask.resume} should raise a L{TaskNotPaused} exception if
        it was not paused; e.g. if L{CooperativeTask.pause} was not invoked
        more times than L{CooperativeTask.resume} on that object.
        """
        self.assertRaises(task.NotPaused, self.task.resume)
        self.task.pause()
        self.task.resume()
        self.assertRaises(task.NotPaused, self.task.resume)


    def test_pauseTwice(self):
        """
        Pauses on tasks should behave like a stack. If a task is paused twice,
        it needs to be resumed twice.
        """
        # pause once
        self.task.pause()
        self.scheduler.pump()
        self.assertEquals(self.work, [])
        # pause twice
        self.task.pause()
        self.scheduler.pump()
        self.assertEquals(self.work, [])
        # resume once (it shouldn't)
        self.task.resume()
        self.scheduler.pump()
        self.assertEquals(self.work, [])
        # resume twice (now it should go)
        self.task.resume()
        self.scheduler.pump()
        self.assertEquals(self.work, [1])


    def test_pauseWhileDeferred(self):
        """
        C{pause()}ing a task while it is waiting on an outstanding
        L{defer.Deferred} should put the task into a state where the
        outstanding L{defer.Deferred} must be called back I{and} the task is
        C{resume}d before it will continue processing.
        """
        self.deferNext()
        self.scheduler.pump()
        self.assertEquals(len(self.work), 1)
        self.failUnless(isinstance(self.work[0], defer.Deferred))
        self.scheduler.pump()
        self.assertEquals(len(self.work), 1)
        self.task.pause()
        self.scheduler.pump()
        self.assertEquals(len(self.work), 1)
        self.task.resume()
        self.scheduler.pump()
        self.assertEquals(len(self.work), 1)
        self.work[0].callback("STUFF!")
        self.scheduler.pump()
        self.assertEquals(len(self.work), 2)
        self.assertEquals(self.work[1], 2)


    def test_whenDone(self):
        """
        L{CooperativeTask.whenDone} returns a Deferred which fires when the
        Cooperator's iterator is exhausted.  It returns a new Deferred each
        time it is called; callbacks added to other invocations will not modify
        the value that subsequent invocations will fire with.
        """

        deferred1 = self.task.whenDone()
        deferred2 = self.task.whenDone()
        results1 = []
        results2 = []
        final1 = []
        final2 = []

        def callbackOne(result):
            results1.append(result)
            return 1

        def callbackTwo(result):
            results2.append(result)
            return 2

        deferred1.addCallback(callbackOne)
        deferred2.addCallback(callbackTwo)

        deferred1.addCallback(final1.append)
        deferred2.addCallback(final2.append)

        # exhaust the task iterator
        # callbacks fire
        self.stopNext()
        self.scheduler.pump()

        self.assertEquals(len(results1), 1)
        self.assertEquals(len(results2), 1)

        self.assertIdentical(results1[0], self.task._iterator)
        self.assertIdentical(results2[0], self.task._iterator)

        self.assertEquals(final1, [1])
        self.assertEquals(final2, [2])


    def test_whenDoneError(self):
        """
        L{CooperativeTask.whenDone} returns a L{defer.Deferred} that will fail
        when the iterable's C{next} method raises an exception, with that
        exception.
        """
        deferred1 = self.task.whenDone()
        results = []
        deferred1.addErrback(results.append)
        self.dieNext()
        self.scheduler.pump()
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].check(UnhandledException), UnhandledException)


    def test_whenDoneStop(self):
        """
        L{CooperativeTask.whenDone} returns a L{defer.Deferred} that fails with
        L{TaskStopped} when the C{stop} method is called on that
        L{CooperativeTask}.
        """
        deferred1 = self.task.whenDone()
        errors = []
        deferred1.addErrback(errors.append)
        self.task.stop()
        self.assertEquals(len(errors), 1)
        self.assertEquals(errors[0].check(task.TaskStopped), task.TaskStopped)


    def test_whenDoneAlreadyDone(self):
        """
        L{CooperativeTask.whenDone} will return a L{defer.Deferred} that will
        succeed immediately if its iterator has already completed.
        """
        self.stopNext()
        self.scheduler.pump()
        results = []
        self.task.whenDone().addCallback(results.append)
        self.assertEquals(results, [self.task._iterator])


    def test_stopStops(self):
        """
        C{stop()}ping a task should cause it to be removed from the run just as
        C{pause()}ing, with the distinction that C{resume()} will raise a
        L{TaskStopped} exception.
        """
        self.task.stop()
        self.scheduler.pump()
        self.assertEquals(len(self.work), 0)
        self.assertRaises(task.TaskStopped, self.task.stop)
        self.assertRaises(task.TaskStopped, self.task.pause)
        # Sanity check - it's still not scheduled, is it?
        self.scheduler.pump()
        self.assertEquals(self.work, [])


    def test_pauseStopResume(self):
        """
        C{resume()}ing a paused, stopped task should be a no-op; it should not
        raise an exception, because it's paused, but neither should it actually
        do more work from the task.
        """
        self.task.pause()
        self.task.stop()
        self.task.resume()
        self.scheduler.pump()
        self.assertEquals(self.work, [])


    def test_stopDeferred(self):
        """
        As a corrolary of the interaction of C{pause()} and C{unpause()},
        C{stop()}ping a task which is waiting on a L{Deferred} should cause the
        task to gracefully shut down, meaning that it should not be unpaused
        when the deferred fires.
        """
        self.deferNext()
        self.scheduler.pump()
        d = self.work.pop()
        self.assertEquals(self.task._pauseCount, 1)
        results = []
        d.addBoth(results.append)
        self.scheduler.pump()
        self.task.stop()
        self.scheduler.pump()
        d.callback(7)
        self.scheduler.pump()
        # Let's make sure that Deferred doesn't come out fried with an
        # unhandled error that will be logged.  The value is None, rather than
        # our test value, 7, because this Deferred is returned to and consumed
        # by the cooperator code.  Its callback therefore has no contract.
        self.assertEquals(results, [None])
        # But more importantly, no further work should have happened.
        self.assertEquals(self.work, [])


    def test_stopExhausted(self):
        """
        C{stop()}ping a L{CooperativeTask} whose iterator has been exhausted
        should raise L{TaskDone}.
        """
        self.stopNext()
        self.scheduler.pump()
        self.assertRaises(task.TaskDone, self.task.stop)


    def test_stopErrored(self):
        """
        C{stop()}ping a L{CooperativeTask} whose iterator has encountered an
        error should raise L{TaskFailed}.
        """
        self.dieNext()
        self.scheduler.pump()
        self.assertRaises(task.TaskFailed, self.task.stop)


    def test_stopCooperatorReentrancy(self):
        """
        If a callback of a L{Deferred} from L{CooperativeTask.whenDone} calls
        C{Cooperator.stop} on its L{CooperativeTask._cooperator}, the
        L{Cooperator} will stop, but the L{CooperativeTask} whose callback is
        calling C{stop} should already be considered 'stopped' by the time the
        callback is running, and therefore removed from the
        L{CoooperativeTask}.
        """
        callbackPhases = []
        def stopit(result):
            callbackPhases.append(result)
            self.cooperator.stop()
            # "done" here is a sanity check to make sure that we get all the
            # way through the callback; i.e. stop() shouldn't be raising an
            # exception due to the stopped-ness of our main task.
            callbackPhases.append("done")
        self.task.whenDone().addCallback(stopit)
        self.stopNext()
        self.scheduler.pump()
        self.assertEquals(callbackPhases, [self.task._iterator, "done"])



