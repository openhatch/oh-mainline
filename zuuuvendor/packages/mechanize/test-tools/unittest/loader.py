"""Loading unittests."""

import doctest
import os
import re
import sys
import traceback
import types

from fnmatch import fnmatch

from unittest import case, suite

# Python 2.4 compatibility
if os.name == "posix":
    from os.path import join, abspath, commonprefix, pardir, curdir, sep
    def relpath(path, start=curdir):
        """Return a relative version of a path"""

        if not path:
            raise ValueError("no path specified")

        start_list = abspath(start).split(sep)
        path_list = abspath(path).split(sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)
elif os.name == "nt":
    from os.path import join, abspath, pardir, curdir, sep, splitunc
    def relpath(path, start=curdir):
        """Return a relative version of a path"""

        if not path:
            raise ValueError("no path specified")
        start_list = abspath(start).split(sep)
        path_list = abspath(path).split(sep)
        if start_list[0].lower() != path_list[0].lower():
            unc_path, rest = splitunc(path)
            unc_start, rest = splitunc(start)
            if bool(unc_path) ^ bool(unc_start):
                raise ValueError("Cannot mix UNC and non-UNC paths (%s and %s)"
                                                                    % (path, start))
            else:
                raise ValueError("path is on drive %s, start on drive %s"
                                                    % (path_list[0], start_list[0]))
        # Work out how much of the filepath is shared by start and path.
        for i in range(min(len(start_list), len(path_list))):
            if start_list[i].lower() != path_list[i].lower():
                break
        else:
            i += 1

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)
else:
    # seems test discovery code from Python 2.7 trunk doesn't support the mac
    # yet
    raise NotImplementedError("fixme")


def _CmpToKey(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) == -1
    return K


# what about .pyc or .pyo (etc)
# we would need to avoid loading the same tests multiple times
# from '.py', '.pyc' *and* '.pyo'
VALID_MODULE_NAME = re.compile(r'[_a-z]\w*\.py$', re.IGNORECASE)


def _make_failed_import_test(name, suiteClass):
    message = 'Failed to import test module: %s' % name
    if hasattr(traceback, 'format_exc'):
        # Python 2.3 compatibility
        # format_exc returns two frames of discover.py as well
        message += '\n%s' % traceback.format_exc()

    def testImportFailure(self):
        raise ImportError(message)
    attrs = {name: testImportFailure}
    ModuleImportFailure = type('ModuleImportFailure', (case.TestCase,), attrs)
    return suiteClass((ModuleImportFailure(name),))


def maybe_load_doctest(path):
    if path.endswith(".doctest"):
        return doctest.DocFileTest(path, module_relative=False)
    elif path.endswith("test_password_manager.special_doctest"):
        # TODO: get rid of this
        import mechanize
        tests = []
        common_globs = {"mechanize": mechanize}
        for globs in [
            {"mgr_class": mechanize.HTTPPasswordMgr},
            {"mgr_class": mechanize.HTTPProxyPasswordMgr},
            ]:
            globs.update(common_globs)
            tests.append(doctest.DocFileTest(path, module_relative=False,
                                             globs=globs))
        return suite.TestSuite(tests)
    return None


def flatten_test(test):
    try:
        tests = iter(test)
    except TypeError:
        yield test
    else:
        for test in tests:
            for flattened in flatten_test(test):
                yield flattened


def is_not_skipped(test, skip_tags, allowed_tags, skip_doctests):
    skipped = False
    for tag in getattr(test, "tags", "").split():
        if tag not in allowed_tags:
            raise Exception("unknown tag: %r" % tag)
        if tag in skip_tags:
            skipped = True
    if skip_doctests and isinstance(test, doctest.DocTestCase):
        skipped = True
    return not skipped


class TestLoader(object):

    # problems
    #  * Can't load doctests from name
    #  * I'm maintaining this :-(

    # TODO: fix doctest support in nose, and use nose instead

    """
    This class is responsible for loading tests according to various criteria
    and returning them wrapped in a TestSuite
    """
    testMethodPrefix = 'test'
    sortTestMethodsUsing = cmp
    suiteClass = suite.TestSuite
    _top_level_dir = None

    def loadTestsFromTestCase(self, testCaseClass):
        """Return a suite of all tests cases contained in testCaseClass"""
        if issubclass(testCaseClass, suite.TestSuite):
            raise TypeError("Test cases should not be derived from TestSuite." \
                                " Maybe you meant to derive from TestCase?")
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']
        loaded_suite = self.suiteClass(map(testCaseClass, testCaseNames))
        return loaded_suite

    def loadTestsFromModule(self, module, use_load_tests=True):
        """Return a suite of all tests cases contained in the given module"""
        tests = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, case.TestCase):
                tests.append(self.loadTestsFromTestCase(obj))

        try:
            if isinstance(module, types.ModuleType):
                tests.append(doctest.DocTestSuite(module))
        except ValueError:
            # no docstring doctests
            pass

        load_tests = getattr(module, 'load_tests', None)
        if use_load_tests and load_tests is not None:
            return load_tests(self, tests, None)
        return self.suiteClass(tests)

    def loadTestsFromName(self, name, module=None):
        """Return a suite of all tests cases given a string specifier.

        The name may resolve either to a module, a test case class, a
        test method within a test case class, or a callable object which
        returns a TestCase or TestSuite instance.

        The method optionally resolves the names relative to a given module.
        """
        parts = name.split('.')
        if module is None:
            parts_copy = parts[:]
            while parts_copy:
                try:
                    module = __import__('.'.join(parts_copy))
                    break
                except ImportError:
                    del parts_copy[-1]
                    if not parts_copy:
                        doctest_test = maybe_load_doctest(name)
                        if doctest_test is not None:
                            obj = doctest_test
                        else:
                            raise
            parts = parts[1:]
        obj = module
        for part in parts:
            parent, obj = obj, getattr(obj, part)

        if isinstance(obj, types.ModuleType):
            return self.loadTestsFromModule(obj)
        elif isinstance(obj, type) and issubclass(obj, case.TestCase):
            return self.loadTestsFromTestCase(obj)
        elif (isinstance(obj, types.UnboundMethodType) and
              isinstance(parent, type) and
              issubclass(parent, case.TestCase)):
            return self.suiteClass([parent(obj.__name__)])
        elif isinstance(obj, suite.TestSuite):
            return obj
        elif hasattr(obj, '__call__'):
            test = obj()
            if isinstance(test, suite.TestSuite):
                return test
            elif isinstance(test, case.TestCase):
                return self.suiteClass([test])
            else:
                raise TypeError("calling %s returned %s, not a test" %
                                (obj, test))
        else:
            raise TypeError("don't know how to make test from: %s" % obj)

    def loadTestsFromNames(self, names, module=None):
        """Return a suite of all tests cases found using the given sequence
        of string specifiers. See 'loadTestsFromName()'.
        """
        suites = [self.loadTestsFromName(name, module) for name in names]
        return self.suiteClass(suites)

    def getTestCaseNames(self, testCaseClass):
        """Return a sorted sequence of method names found within testCaseClass
        """
        def isTestMethod(attrname, testCaseClass=testCaseClass,
                         prefix=self.testMethodPrefix):
            return attrname.startswith(prefix) and \
                hasattr(getattr(testCaseClass, attrname), '__call__')
        testFnNames = filter(isTestMethod, dir(testCaseClass))
        if self.sortTestMethodsUsing:
            testFnNames.sort(key=_CmpToKey(self.sortTestMethodsUsing))
        return testFnNames

    def discover(self, start_dir, pattern='test*.py', top_level_dir=None,
                 skip_tags=frozenset(), allowed_tags=frozenset(),
                 skip_doctests=False):
        """Find and return all test modules from the specified start
        directory, recursing into subdirectories to find them. Only test files
        that match the pattern will be loaded. (Using shell style pattern
        matching.)

        All test modules must be importable from the top level of the project.
        If the start directory is not the top level directory then the top
        level directory must be specified separately.

        If a test package name (directory with '__init__.py') matches the
        pattern then the package will be checked for a 'load_tests' function. If
        this exists then it will be called with loader, tests, pattern.

        If load_tests exists then discovery does  *not* recurse into the package,
        load_tests is responsible for loading all tests in the package.

        The pattern is deliberately not stored as a loader attribute so that
        packages can continue discovery themselves. top_level_dir is stored so
        load_tests does not need to pass this argument in to loader.discover().
        """
        if top_level_dir is None and self._top_level_dir is not None:
            # make top_level_dir optional if called from load_tests in a package
            top_level_dir = self._top_level_dir
        elif top_level_dir is None:
            top_level_dir = start_dir

        top_level_dir = os.path.abspath(os.path.normpath(top_level_dir))
        start_dir = os.path.abspath(os.path.normpath(start_dir))

        if not top_level_dir in sys.path:
            # all test modules must be importable from the top level directory
            sys.path.append(top_level_dir)
        self._top_level_dir = top_level_dir

        if start_dir != top_level_dir and not os.path.isfile(os.path.join(start_dir, '__init__.py')):
            # what about __init__.pyc or pyo (etc)
            raise ImportError('Start directory is not importable: %r' % start_dir)

        tests = list(test for test in
                     flatten_test(self._find_tests(start_dir, pattern))
                     if is_not_skipped(test, skip_tags, allowed_tags,
                                       skip_doctests))
        return self.suiteClass(tests)

    def _get_name_from_path(self, path):
        path = os.path.splitext(os.path.normpath(path))[0]

        _relpath = relpath(path, self._top_level_dir)
        assert not os.path.isabs(_relpath), "Path must be within the project"
        assert not _relpath.startswith('..'), "Path must be within the project"

        name = _relpath.replace(os.path.sep, '.')
        return name

    def _get_module_from_name(self, name):
        __import__(name)
        return sys.modules[name]

    def _find_tests(self, start_dir, pattern):
        """Used by discovery. Yields test suites it loads."""
        paths = os.listdir(start_dir)

        for path in paths:
            full_path = os.path.join(start_dir, path)
            if os.path.isfile(full_path):
                doctest_test = maybe_load_doctest(full_path)
                if doctest_test is not None:
                    yield doctest_test
                    continue

                if not VALID_MODULE_NAME.match(path):
                    # valid Python identifiers only
                    continue

                if fnmatch(path, pattern):
                    # if the test file matches, load it
                    name = self._get_name_from_path(full_path)
                    try:
                        module = self._get_module_from_name(name)
                    except:
                        yield _make_failed_import_test(name, self.suiteClass)
                    else:
                        yield self.loadTestsFromModule(module)
            elif os.path.isdir(full_path):
                if not os.path.isfile(os.path.join(full_path, '__init__.py')):
                    continue

                load_tests = None
                tests = None
                if fnmatch(path, pattern):
                    # only check load_tests if the package directory itself matches the filter
                    name = self._get_name_from_path(full_path)
                    package = self._get_module_from_name(name)
                    load_tests = getattr(package, 'load_tests', None)
                    tests = self.loadTestsFromModule(package, use_load_tests=False)

                if load_tests is None:
                    if tests is not None:
                        # tests loaded from package file
                        yield tests
                    # recurse into the package
                    for test in self._find_tests(full_path, pattern):
                        yield test
                else:
                    yield load_tests(self, tests, pattern)

defaultTestLoader = TestLoader()


def _makeLoader(prefix, sortUsing, suiteClass=None):
    loader = TestLoader()
    loader.sortTestMethodsUsing = sortUsing
    loader.testMethodPrefix = prefix
    if suiteClass:
        loader.suiteClass = suiteClass
    return loader

def getTestCaseNames(testCaseClass, prefix, sortUsing=cmp):
    return _makeLoader(prefix, sortUsing).getTestCaseNames(testCaseClass)

def makeSuite(testCaseClass, prefix='test', sortUsing=cmp,
              suiteClass=suite.TestSuite):
    return _makeLoader(prefix, sortUsing, suiteClass).loadTestsFromTestCase(testCaseClass)

def findTestCases(module, prefix='test', sortUsing=cmp,
                  suiteClass=suite.TestSuite):
    return _makeLoader(prefix, sortUsing, suiteClass).loadTestsFromModule(module)
