# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for Twisted's deprecation framework, L{twisted.python.deprecate}.
"""

import sys, types
import warnings
from os.path import normcase

from twisted.trial.unittest import TestCase

from twisted.python import deprecate
from twisted.python.deprecate import _appendToDocstring
from twisted.python.deprecate import _getDeprecationDocstring
from twisted.python.deprecate import deprecated, getDeprecationWarningString
from twisted.python.deprecate import _getDeprecationWarningString
from twisted.python.deprecate import DEPRECATION_WARNING_FORMAT
from twisted.python.reflect import fullyQualifiedName
from twisted.python.versions import Version
from twisted.python.filepath import FilePath

from twisted.python.test import deprecatedattributes



def dummyCallable():
    """
    Do nothing.

    This is used to test the deprecation decorators.
    """


def dummyReplacementMethod():
    """
    Do nothing.

    This is used to test the replacement parameter to L{deprecated}.
    """



class TestDeprecationWarnings(TestCase):
    def test_getDeprecationWarningString(self):
        """
        L{getDeprecationWarningString} returns a string that tells us that a
        callable was deprecated at a certain released version of Twisted.
        """
        version = Version('Twisted', 8, 0, 0)
        self.assertEqual(
            getDeprecationWarningString(self.test_getDeprecationWarningString,
                                        version),
            "twisted.python.test.test_deprecate.TestDeprecationWarnings."
            "test_getDeprecationWarningString was deprecated in "
            "Twisted 8.0.0")


    def test_getDeprecationWarningStringWithFormat(self):
        """
        L{getDeprecationWarningString} returns a string that tells us that a
        callable was deprecated at a certain released version of Twisted, with
        a message containing additional information about the deprecation.
        """
        version = Version('Twisted', 8, 0, 0)
        format = deprecate.DEPRECATION_WARNING_FORMAT + ': This is a message'
        self.assertEquals(
            getDeprecationWarningString(self.test_getDeprecationWarningString,
                                        version, format),
            'twisted.python.test.test_deprecate.TestDeprecationWarnings.'
            'test_getDeprecationWarningString was deprecated in '
            'Twisted 8.0.0: This is a message')


    def test_deprecateEmitsWarning(self):
        """
        Decorating a callable with L{deprecated} emits a warning.
        """
        version = Version('Twisted', 8, 0, 0)
        dummy = deprecated(version)(dummyCallable)
        def addStackLevel():
            dummy()
        self.assertWarns(
            DeprecationWarning,
            getDeprecationWarningString(dummyCallable, version),
            __file__,
            addStackLevel)


    def test_deprecatedPreservesName(self):
        """
        The decorated function has the same name as the original.
        """
        version = Version('Twisted', 8, 0, 0)
        dummy = deprecated(version)(dummyCallable)
        self.assertEqual(dummyCallable.__name__, dummy.__name__)
        self.assertEqual(fullyQualifiedName(dummyCallable),
                         fullyQualifiedName(dummy))


    def test_getDeprecationDocstring(self):
        """
        L{_getDeprecationDocstring} returns a note about the deprecation to go
        into a docstring.
        """
        version = Version('Twisted', 8, 0, 0)
        self.assertEqual(
            "Deprecated in Twisted 8.0.0.",
            _getDeprecationDocstring(version, ''))


    def test_deprecatedUpdatesDocstring(self):
        """
        The docstring of the deprecated function is appended with information
        about the deprecation.
        """

        version = Version('Twisted', 8, 0, 0)
        dummy = deprecated(version)(dummyCallable)

        _appendToDocstring(
            dummyCallable,
            _getDeprecationDocstring(version, ''))

        self.assertEqual(dummyCallable.__doc__, dummy.__doc__)


    def test_versionMetadata(self):
        """
        Deprecating a function adds version information to the decorated
        version of that function.
        """
        version = Version('Twisted', 8, 0, 0)
        dummy = deprecated(version)(dummyCallable)
        self.assertEqual(version, dummy.deprecatedVersion)


    def test_getDeprecationWarningStringReplacement(self):
        """
        L{getDeprecationWarningString} takes an additional replacement parameter
        that can be used to add information to the deprecation.  If the
        replacement parameter is a string, it will be interpolated directly into
        the result.
        """
        version = Version('Twisted', 8, 0, 0)
        warningString = getDeprecationWarningString(
            self.test_getDeprecationWarningString, version,
            replacement="something.foobar")
        self.assertEqual(
            warningString,
            "%s was deprecated in Twisted 8.0.0; please use something.foobar "
            "instead" % (
                fullyQualifiedName(self.test_getDeprecationWarningString),))


    def test_getDeprecationWarningStringReplacementWithCallable(self):
        """
        L{getDeprecationWarningString} takes an additional replacement parameter
        that can be used to add information to the deprecation. If the
        replacement parameter is a callable, its fully qualified name will be
        interpolated into the result.
        """
        version = Version('Twisted', 8, 0, 0)
        warningString = getDeprecationWarningString(
            self.test_getDeprecationWarningString, version,
            replacement=dummyReplacementMethod)
        self.assertEqual(
            warningString,
            "%s was deprecated in Twisted 8.0.0; please use "
            "twisted.python.test.test_deprecate.dummyReplacementMethod "
            "instead" % (
                fullyQualifiedName(self.test_getDeprecationWarningString),))


    def test_deprecatedReplacement(self):
        """
        L{deprecated} takes an additional replacement parameter that can be used
        to indicate the new, non-deprecated method developers should use.  If
        the replacement parameter is a string, it will be interpolated directly
        into the warning message.
        """
        version = Version('Twisted', 8, 0, 0)
        dummy = deprecated(version, "something.foobar")(dummyCallable)
        self.assertEquals(dummy.__doc__,
            "\n"
            "    Do nothing.\n\n"
            "    This is used to test the deprecation decorators.\n\n"
            "    Deprecated in Twisted 8.0.0; please use "
            "something.foobar"
            " instead.\n"
            "    ")


    def test_deprecatedReplacementWithCallable(self):
        """
        L{deprecated} takes an additional replacement parameter that can be used
        to indicate the new, non-deprecated method developers should use.  If
        the replacement parameter is a callable, its fully qualified name will
        be interpolated into the warning message.
        """
        version = Version('Twisted', 8, 0, 0)
        decorator = deprecated(version, replacement=dummyReplacementMethod)
        dummy = decorator(dummyCallable)
        self.assertEquals(dummy.__doc__,
            "\n"
            "    Do nothing.\n\n"
            "    This is used to test the deprecation decorators.\n\n"
            "    Deprecated in Twisted 8.0.0; please use "
            "twisted.python.test.test_deprecate.dummyReplacementMethod"
            " instead.\n"
            "    ")



class TestAppendToDocstring(TestCase):
    """
    Test the _appendToDocstring function.

    _appendToDocstring is used to add text to a docstring.
    """

    def test_appendToEmptyDocstring(self):
        """
        Appending to an empty docstring simply replaces the docstring.
        """

        def noDocstring():
            pass

        _appendToDocstring(noDocstring, "Appended text.")
        self.assertEqual("Appended text.", noDocstring.__doc__)


    def test_appendToSingleLineDocstring(self):
        """
        Appending to a single line docstring places the message on a new line,
        with a blank line separating it from the rest of the docstring.

        The docstring ends with a newline, conforming to Twisted and PEP 8
        standards. Unfortunately, the indentation is incorrect, since the
        existing docstring doesn't have enough info to help us indent
        properly.
        """

        def singleLineDocstring():
            """This doesn't comply with standards, but is here for a test."""

        _appendToDocstring(singleLineDocstring, "Appended text.")
        self.assertEqual(
            ["This doesn't comply with standards, but is here for a test.",
             "",
             "Appended text."],
            singleLineDocstring.__doc__.splitlines())
        self.assertTrue(singleLineDocstring.__doc__.endswith('\n'))


    def test_appendToMultilineDocstring(self):
        """
        Appending to a multi-line docstring places the messade on a new line,
        with a blank line separating it from the rest of the docstring.

        Because we have multiple lines, we have enough information to do
        indentation.
        """

        def multiLineDocstring():
            """
            This is a multi-line docstring.
            """

        def expectedDocstring():
            """
            This is a multi-line docstring.

            Appended text.
            """

        _appendToDocstring(multiLineDocstring, "Appended text.")
        self.assertEqual(
            expectedDocstring.__doc__, multiLineDocstring.__doc__)



class _MockDeprecatedAttribute(object):
    """
    Mock of L{twisted.python.deprecate._DeprecatedAttribute}.

    @ivar value: The value of the attribute.
    """
    def __init__(self, value):
        self.value = value


    def get(self):
        """
        Get a known value.
        """
        return self.value



class ModuleProxyTests(TestCase):
    """
    Tests for L{twisted.python.deprecate._ModuleProxy}, which proxies
    access to module-level attributes, intercepting access to deprecated
    attributes and passing through access to normal attributes.
    """
    def _makeProxy(self, **attrs):
        """
        Create a temporary module proxy object.

        @param **kw: Attributes to initialise on the temporary module object

        @rtype: L{twistd.python.deprecate._ModuleProxy}
        """
        mod = types.ModuleType('foo')
        for key, value in attrs.iteritems():
            setattr(mod, key, value)
        return deprecate._ModuleProxy(mod)


    def test_getattrPassthrough(self):
        """
        Getting a normal attribute on a L{twisted.python.deprecate._ModuleProxy}
        retrieves the underlying attribute's value, and raises C{AttributeError}
        if a non-existant attribute is accessed.
        """
        proxy = self._makeProxy(SOME_ATTRIBUTE='hello')
        self.assertIdentical(proxy.SOME_ATTRIBUTE, 'hello')
        self.assertRaises(AttributeError, getattr, proxy, 'DOES_NOT_EXIST')


    def test_getattrIntercept(self):
        """
        Getting an attribute marked as being deprecated on
        L{twisted.python.deprecate._ModuleProxy} results in calling the
        deprecated wrapper's C{get} method.
        """
        proxy = self._makeProxy()
        _deprecatedAttributes = object.__getattribute__(
            proxy, '_deprecatedAttributes')
        _deprecatedAttributes['foo'] = _MockDeprecatedAttribute(42)
        self.assertEquals(proxy.foo, 42)


    def test_privateAttributes(self):
        """
        Private attributes of L{twisted.python.deprecate._ModuleProxy} are
        inaccessible when regular attribute access is used.
        """
        proxy = self._makeProxy()
        self.assertRaises(AttributeError, getattr, proxy, '_module')
        self.assertRaises(
            AttributeError, getattr, proxy, '_deprecatedAttributes')


    def test_setattr(self):
        """
        Setting attributes on L{twisted.python.deprecate._ModuleProxy} proxies
        them through to the wrapped module.
        """
        proxy = self._makeProxy()
        proxy._module = 1
        self.assertNotEquals(object.__getattribute__(proxy, '_module'), 1)
        self.assertEquals(proxy._module, 1)


    def test_repr(self):
        """
        L{twisted.python.deprecated._ModuleProxy.__repr__} produces a string
        containing the proxy type and a representation of the wrapped module
        object.
        """
        proxy = self._makeProxy()
        realModule = object.__getattribute__(proxy, '_module')
        self.assertEquals(
            repr(proxy), '<%s module=%r>' % (type(proxy).__name__, realModule))



class DeprecatedAttributeTests(TestCase):
    """
    Tests for L{twisted.python.deprecate._DeprecatedAttribute} and
    L{twisted.python.deprecate.deprecatedModuleAttribute}, which issue
    warnings for deprecated module-level attributes.
    """
    def setUp(self):
        self.version = deprecatedattributes.version
        self.message = deprecatedattributes.message
        self._testModuleName = __name__ + '.foo'


    def _getWarningString(self, attr):
        """
        Create the warning string used by deprecated attributes.
        """
        return _getDeprecationWarningString(
            deprecatedattributes.__name__ + '.' + attr,
            deprecatedattributes.version,
            DEPRECATION_WARNING_FORMAT + ': ' + deprecatedattributes.message)


    def test_deprecatedAttributeHelper(self):
        """
        L{twisted.python.deprecate._DeprecatedAttribute} correctly sets its
        __name__ to match that of the deprecated attribute and emits a warning
        when the original attribute value is accessed.
        """
        name = 'ANOTHER_DEPRECATED_ATTRIBUTE'
        setattr(deprecatedattributes, name, 42)
        attr = deprecate._DeprecatedAttribute(
            deprecatedattributes, name, self.version, self.message)

        self.assertEquals(attr.__name__, name)

        # Since we're accessing the value getter directly, as opposed to via
        # the module proxy, we need to match the warning's stack level.
        def addStackLevel():
            attr.get()

        # Access the deprecated attribute.
        addStackLevel()
        warningsShown = self.flushWarnings([
            self.test_deprecatedAttributeHelper])
        self.assertIdentical(warningsShown[0]['category'], DeprecationWarning)
        self.assertEquals(
            warningsShown[0]['message'],
            self._getWarningString(name))
        self.assertEquals(len(warningsShown), 1)


    def test_deprecatedAttribute(self):
        """
        L{twisted.python.deprecate.deprecatedModuleAttribute} wraps a
        module-level attribute in an object that emits a deprecation warning
        when it is accessed the first time only, while leaving other unrelated
        attributes alone.
        """
        # Accessing non-deprecated attributes does not issue a warning.
        deprecatedattributes.ANOTHER_ATTRIBUTE
        warningsShown = self.flushWarnings([self.test_deprecatedAttribute])
        self.assertEquals(len(warningsShown), 0)

        name = 'DEPRECATED_ATTRIBUTE'

        # Access the deprecated attribute. This uses getattr to avoid repeating
        # the attribute name.
        getattr(deprecatedattributes, name)

        warningsShown = self.flushWarnings([self.test_deprecatedAttribute])
        self.assertEquals(len(warningsShown), 1)
        self.assertIdentical(warningsShown[0]['category'], DeprecationWarning)
        self.assertEquals(
            warningsShown[0]['message'],
            self._getWarningString(name))


    def test_wrappedModule(self):
        """
        Deprecating an attribute in a module replaces and wraps that module
        instance, in C{sys.modules}, with a
        L{twisted.python.deprecate._ModuleProxy} instance but only if it hasn't
        already been wrapped.
        """
        sys.modules[self._testModuleName] = mod = types.ModuleType('foo')
        self.addCleanup(sys.modules.pop, self._testModuleName)

        setattr(mod, 'first', 1)
        setattr(mod, 'second', 2)

        deprecate.deprecatedModuleAttribute(
            Version('Twisted', 8, 0, 0),
            'message',
            self._testModuleName,
            'first')

        proxy = sys.modules[self._testModuleName]
        self.assertNotEqual(proxy, mod)

        deprecate.deprecatedModuleAttribute(
            Version('Twisted', 8, 0, 0),
            'message',
            self._testModuleName,
            'second')

        self.assertIdentical(proxy, sys.modules[self._testModuleName])

    _packageInit = """\
from twisted.python.deprecate import deprecatedModuleAttribute
from twisted.python.versions import Version

deprecatedModuleAttribute(
    Version('Package', 1, 2, 3), 'message', __name__, 'module')
"""

    def test_deprecatedModule(self):
        """
        If L{deprecatedModuleAttribute} is used to deprecate a module attribute
        of a package, only one deprecation warning is emitted when the
        deprecated module is imported.
        """
        base = FilePath(self.mktemp())
        base.makedirs()
        package = base.child('package')
        package.makedirs()
        package.child('__init__.py').setContent(self._packageInit)
        module = package.child('module.py').setContent('')

        sys.path.insert(0, base.path)
        self.addCleanup(sys.path.remove, base.path)

        # import package.module
        from package import module
        # make sure it's the right module.
        self.assertEquals(module.__file__.rsplit(".", 1)[0],
                          package.child('module.py').path.rsplit(".", 1)[0])
        warningsShown = self.flushWarnings([self.test_deprecatedModule])
        self.assertEquals(len(warningsShown), 1)



class WarnAboutFunctionTests(TestCase):
    """
    Tests for L{twisted.python.deprecate.warnAboutFunction} which allows the
    callers of a function to issue a C{DeprecationWarning} about that function.
    """
    def setUp(self):
        """
        Create a file that will have known line numbers when emitting warnings.
        """
        self.package = FilePath(self.mktemp()).child('twisted_private_helper')
        self.package.makedirs()
        self.package.child('__init__.py').setContent('')
        self.package.child('module.py').setContent('''
"A module string"

from twisted.python import deprecate

def testFunction():
    "A doc string"
    a = 1 + 2
    return a

def callTestFunction():
    b = testFunction()
    if b == 3:
        deprecate.warnAboutFunction(testFunction, "A Warning String")
''')
        sys.path.insert(0, self.package.parent().path)
        self.addCleanup(sys.path.remove, self.package.parent().path)

        modules = sys.modules.copy()
        self.addCleanup(
            lambda: (sys.modules.clear(), sys.modules.update(modules)))


    def test_warning(self):
        """
        L{deprecate.warnAboutFunction} emits a warning the file and line number
        of which point to the beginning of the implementation of the function
        passed to it.
        """
        def aFunc():
            pass
        deprecate.warnAboutFunction(aFunc, 'A Warning Message')
        warningsShown = self.flushWarnings()
        filename = __file__
        if filename.lower().endswith('.pyc'):
            filename = filename[:-1]
        self.assertSamePath(
            FilePath(warningsShown[0]["filename"]), FilePath(filename))
        self.assertEquals(warningsShown[0]["message"], "A Warning Message")


    def test_warningLineNumber(self):
        """
        L{deprecate.warnAboutFunction} emits a C{DeprecationWarning} with the
        number of a line within the implementation of the function passed to it.
        """
        from twisted_private_helper import module
        module.callTestFunction()
        warningsShown = self.flushWarnings()
        self.assertSamePath(
            FilePath(warningsShown[0]["filename"]),
            self.package.sibling('twisted_private_helper').child('module.py'))
        # Line number 9 is the last line in the testFunction in the helper
        # module.
        self.assertEquals(warningsShown[0]["lineno"], 9)
        self.assertEquals(warningsShown[0]["message"], "A Warning String")
        self.assertEquals(len(warningsShown), 1)


    def assertSamePath(self, first, second):
        """
        Assert that the two paths are the same, considering case normalization
        appropriate for the current platform.

        @type first: L{FilePath}
        @type second: L{FilePath}

        @raise C{self.failureType}: If the paths are not the same.
        """
        self.assertTrue(
            normcase(first.path) == normcase(second.path),
            "%r != %r" % (first, second))


    def test_renamedFile(self):
        """
        Even if the implementation of a deprecated function is moved around on
        the filesystem, the line number in the warning emitted by
        L{deprecate.warnAboutFunction} points to a line in the implementation of
        the deprecated function.
        """
        from twisted_private_helper import module
        # Clean up the state resulting from that import; we're not going to use
        # this module, so it should go away.
        del sys.modules['twisted_private_helper']
        del sys.modules[module.__name__]

        # Rename the source directory
        self.package.moveTo(self.package.sibling('twisted_renamed_helper'))

        # Import the newly renamed version
        from twisted_renamed_helper import module
        self.addCleanup(sys.modules.pop, 'twisted_renamed_helper')
        self.addCleanup(sys.modules.pop, module.__name__)

        module.callTestFunction()
        warningsShown = self.flushWarnings()
        warnedPath = FilePath(warningsShown[0]["filename"])
        expectedPath = self.package.sibling(
            'twisted_renamed_helper').child('module.py')
        self.assertSamePath(warnedPath, expectedPath)
        self.assertEquals(warningsShown[0]["lineno"], 9)
        self.assertEquals(warningsShown[0]["message"], "A Warning String")
        self.assertEquals(len(warningsShown), 1)


    def test_filteredWarning(self):
        """
        L{deprecate.warnAboutFunction} emits a warning that will be filtered if
        L{warnings.filterwarning} is called with the module name of the
        deprecated function.
        """
        # Clean up anything *else* that might spuriously filter out the warning,
        # such as the "always" simplefilter set up by unittest._collectWarnings.
        # We'll also rely on trial to restore the original filters afterwards.
        del warnings.filters[:]

        warnings.filterwarnings(
            action="ignore", module="twisted_private_helper")

        from twisted_private_helper import module
        module.callTestFunction()

        warningsShown = self.flushWarnings()
        self.assertEquals(len(warningsShown), 0)


    def test_filteredOnceWarning(self):
        """
        L{deprecate.warnAboutFunction} emits a warning that will be filtered
        once if L{warnings.filterwarning} is called with the module name of the
        deprecated function and an action of once.
        """
        # Clean up anything *else* that might spuriously filter out the warning,
        # such as the "always" simplefilter set up by unittest._collectWarnings.
        # We'll also rely on trial to restore the original filters afterwards.
        del warnings.filters[:]

        warnings.filterwarnings(
            action="module", module="twisted_private_helper")

        from twisted_private_helper import module
        module.callTestFunction()
        module.callTestFunction()

        warningsShown = self.flushWarnings()
        self.assertEquals(len(warningsShown), 1)
        message = warningsShown[0]['message']
        category = warningsShown[0]['category']
        filename = warningsShown[0]['filename']
        lineno = warningsShown[0]['lineno']
        msg = warnings.formatwarning(message, category, filename, lineno)
        self.assertTrue(
            msg.endswith("module.py:9: DeprecationWarning: A Warning String\n"
                         "  return a\n"),
            "Unexpected warning string: %r" % (msg,))
