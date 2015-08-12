import types
import unittest
import sys
import os.path
import time

from unittest import _strclass
    
def run_all_tests(test_mod=None, tests=None):
    if tests is None:
        tests = unittest.TestLoader().loadTestsFromModule(test_mod)
    TodoTextRunner(verbosity=2).run(tests)

def adjust_path():
    parent_dir = os.path.split(sys.path[0])[0]
    sys.path = [parent_dir] + sys.path

class _Todo_Exception(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)   
        self.message = message

class Todo_Failed(_Todo_Exception):
    pass
        
class Todo_Passed(_Todo_Exception):
    pass
    
def TODO(message="TODO"):
    def decorator(func):
        def __todo_func(*args, **kwargs):
            try:
                ret_val = func(*args, **kwargs)
            except Exception, e:
                raise Todo_Failed(message)
            raise Todo_Passed(message)
        __todo_func.__name__ = func.__name__
        __todo_func.__doc__ = func.__doc__
        __todo_func.__module__ = func.__module__
        return __todo_func
    return decorator

class TodoResult(unittest.TestResult):
    def __init__(self):
        unittest.TestResult.__init__(self)
        
        self.todo_failed = []
        self.todo_passed = []

    def addTodoFailed(self, test, err):
        self.todo_failed.append((test, self._exc_info_to_string(err, test)))
        
    def addTodoPassed(self, test, err):
        self.todo_passed.append((test, self._exc_info_to_string(err, test)))    

    def wasSuccessful(self):
        p_success = unittest.TestResult.wasSuccessful(self)
        
        return p_success and not self.stillTodo()
        
    def stillTodo(self):
        return self.todo_failed or self.todo_passed

class TodoTextResult(unittest._TextTestResult, TodoResult):
    def __init__(self, *vargs, **kwargs):
        TodoResult.__init__(self)
        unittest._TextTestResult.__init__(self, *vargs, **kwargs)
        
    def addTodoFailed(self, test, err):
        TodoResult.addTodoFailed(self, test, err)
        if self.showAll:
            self.stream.writeln("TODO FAIL")
        elif self.dots:
            self.stream.write('TF')
            
    def addTodoPassed(self, test, err):
        TodoResult.addTodoPassed(self, test, err)
        if self.showAll:
            self.stream.writeln("TODO PASS")
        elif self.dots:
            self.stream.write('TP')
            
    def printErrors(self):
        self.printErrorList('TODO(PASS)', self.todo_passed)
        self.printErrorList('TODO(FAIL)', self.todo_failed)

        unittest._TextTestResult.printErrors(self)      

class TodoCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        """ Create an instance of the class that will use the named test
            method when executed. Raises a ValueError if the instance does
            not have a method with the specified name.
        """
        unittest.TestCase.__init__(self, methodName)
        
        try:
            self.__testMethodName = methodName
            testMethod = getattr(self, methodName)
            self.__testMethodDoc = testMethod.__doc__
        except AttributeError:
            raise ValueError, "no such test method in %s: %s" % \
                (self.__class__, methodName)
                  
    def shortDescription(self):
        """Returns a one-line description of the test, or None if no
        description has been provided.

        The default implementation of this method returns the first line of
        the specified test method's docstring.
        """
        doc = self.__testMethodDoc
        return doc and doc.split("\n")[0].strip() or None
        
    def __str__(self):
        return "%s (%s)" % (self.__testMethodName, _strclass(self.__class__))

    def __repr__(self):
        return "<%s testMethod=%s>" % \
            (_strclass(self.__class__), self.__testMethodName)
            
    def __exc_info(self):
        """Return a version of sys.exc_info() with the traceback frame
        minimised; usually the top level of the traceback frame is not
        needed.
        """
        exctype, excvalue, tb = sys.exc_info()
        if sys.platform[:4] == 'java': ## tracebacks look different in Jython
            return (exctype, excvalue, tb)
        return (exctype, excvalue, tb)

    def run(self, result):
        result.startTest(self)
        testMethod = getattr(self, self.__testMethodName)
        try:
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self.__exc_info())
                return

            ok = False
            try:
                testMethod()
                ok = True
            except Todo_Failed:
                result.addTodoFailed(self, self.__exc_info())
            except Todo_Passed:
                result.addTodoPassed(self, self.__exc_info())
            except self.failureException:
                result.addFailure(self, self.__exc_info())
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self.__exc_info())

            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self.__exc_info())
                ok = False
            if ok: result.addSuccess(self)
        finally:
            result.stopTest(self)
    
class TodoTextRunner(unittest.TextTestRunner):
    def run(self, test):
        "Run the given test case or test suite."
        result = TodoTextResult(self.stream, self.descriptions, self.verbosity)
        startTime = time.time()
        test.run(result)
        stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()
        if not result.wasSuccessful():
            if result.stillTodo():
                self.stream.write("TODO (")
            else:
                self.stream.write("FAILED (")

            status = ("failures", "errors", "todo_passed", "todo_failed")
            self.stream.write(", ".join("%s=%d" % (s, len(getattr(result, s))) for s in status)) 

            self.stream.writeln(")")
        else:
            self.stream.writeln("OK")
        return result

TestCase = TodoCase #unittest.TestCase

### The following are some convenience functions used throughout the test
### suite

def test_equality(eq_tests, ne_tests, repeats=10):
    eq_error = "Problem with __eq__ with %s and %s"
    ne_error = "Problem with __ne__ with %s and %s"

    # We run this multiple times to try and shake out any errors
    # related to differences in set/dict/etc ordering
    for _ in xrange(0, repeats):                
        for (left, right) in eq_tests:
            try:
                assert left == right
            except AssertionError:
                raise AssertionError(eq_error % (left, right))

            try:
                assert not left != right
            except AssertionError:
                raise AssertionError(ne_error % (left, right))

        for (left, right) in ne_tests:
            try:
                assert left != right
            except AssertionError:
                raise AssertionError(ne_error % (left, right))

            try:
                assert not left == right
            except AssertionError:
                raise AssertionError(eq_error % (left, right))
                
def test_hash(eq_tests, ne_tests, repeats=10):
    hash_error = "Problem with hash() with %s and %s"

    # We run this multiple times to try and shake out any errors
    # related to differences in set/dict/etc ordering
    for _ in xrange(0, repeats):                
        for (left, right) in eq_tests:
            try:
                assert hash(left) == hash(right)
            except AssertionError:
                raise AssertionError(hash_error % (left, right))

        for (left, right) in ne_tests:
            try:
                assert hash(left) != hash(right)
            except AssertionError:
                raise AssertionError(hash_error % (left, right))
