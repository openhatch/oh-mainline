# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Test cases for Twisted component architecture.
"""

from zope.interface import Interface, implements, Attribute

from twisted.trial import unittest
from twisted.python import components
from twisted.python.components import proxyForInterface


class InterfacesTestCase(unittest.TestCase):
    """Test interfaces."""

class Compo(components.Componentized):
    num = 0
    def inc(self):
        self.num = self.num + 1
        return self.num

class IAdept(Interface):
    def adaptorFunc():
        raise NotImplementedError()

class IElapsed(Interface):
    def elapsedFunc():
        """
        1!
        """

class Adept(components.Adapter):
    implements(IAdept)
    def __init__(self, orig):
        self.original = orig
        self.num = 0
    def adaptorFunc(self):
        self.num = self.num + 1
        return self.num, self.original.inc()

class Elapsed(components.Adapter):
    implements(IElapsed)
    def elapsedFunc(self):
        return 1

components.registerAdapter(Adept, Compo, IAdept)
components.registerAdapter(Elapsed, Compo, IElapsed)

class AComp(components.Componentized):
    pass
class BComp(AComp):
    pass
class CComp(BComp):
    pass

class ITest(Interface):
    pass
class ITest2(Interface):
    pass
class ITest3(Interface):
    pass
class ITest4(Interface):
    pass
class Test(components.Adapter):
    implements(ITest, ITest3, ITest4)
    def __init__(self, orig):
        pass
class Test2:
    implements(ITest2)
    temporaryAdapter = 1
    def __init__(self, orig):
        pass

components.registerAdapter(Test, AComp, ITest)
components.registerAdapter(Test, AComp, ITest3)
components.registerAdapter(Test2, AComp, ITest2)




class ComponentizedTestCase(unittest.TestCase):
    """Simple test case for caching in Componentized.
    """
    def testComponentized(self):
        c = Compo()
        assert c.getComponent(IAdept).adaptorFunc() == (1, 1)
        assert c.getComponent(IAdept).adaptorFunc() == (2, 2)
        assert IElapsed(IAdept(c)).elapsedFunc() == 1

    def testInheritanceAdaptation(self):
        c = CComp()
        co1 = c.getComponent(ITest)
        co2 = c.getComponent(ITest)
        co3 = c.getComponent(ITest2)
        co4 = c.getComponent(ITest2)
        assert co1 is co2
        assert co3 is not co4
        c.removeComponent(co1)
        co5 = c.getComponent(ITest)
        co6 = c.getComponent(ITest)
        assert co5 is co6
        assert co1 is not co5

    def testMultiAdapter(self):
        c = CComp()
        co1 = c.getComponent(ITest)
        co2 = c.getComponent(ITest2)
        co3 = c.getComponent(ITest3)
        co4 = c.getComponent(ITest4)
        assert co4 == None
        assert co1 is co3


    def test_getComponentDefaults(self):
        """
        Test that a default value specified to Componentized.getComponent if
        there is no component for the requested interface.
        """
        componentized = components.Componentized()
        default = object()
        self.assertIdentical(
            componentized.getComponent(ITest, default),
            default)
        self.assertIdentical(
            componentized.getComponent(ITest, default=default),
            default)
        self.assertIdentical(
            componentized.getComponent(ITest),
            None)



class AdapterTestCase(unittest.TestCase):
    """Test adapters."""

    def testAdapterGetComponent(self):
        o = object()
        a = Adept(o)
        self.assertRaises(components.CannotAdapt, ITest, a)
        self.assertEquals(ITest(a, None), None)



class IMeta(Interface):
    pass

class MetaAdder(components.Adapter):
    implements(IMeta)
    def add(self, num):
        return self.original.num + num

class BackwardsAdder(components.Adapter):
    implements(IMeta)
    def add(self, num):
        return self.original.num - num

class MetaNumber:
    def __init__(self, num):
        self.num = num

class FakeAdder:
    def add(self, num):
        return num + 5

class FakeNumber:
    num = 3

class ComponentNumber(components.Componentized):
    def __init__(self):
        self.num = 0
        components.Componentized.__init__(self)

class ComponentMeta(components.Adapter):
    implements(IMeta)
    def __init__(self, original):
        components.Adapter.__init__(self, original)
        self.num = self.original.num

class ComponentAdder(ComponentMeta):
    def add(self, num):
        self.num += num
        return self.num

class ComponentDoubler(ComponentMeta):
    def add(self, num):
        self.num += (num * 2)
        return self.original.num

components.registerAdapter(MetaAdder, MetaNumber, IMeta)
components.registerAdapter(ComponentAdder, ComponentNumber, IMeta)

class IAttrX(Interface):
    def x():
        pass

class IAttrXX(Interface):
    def xx():
        pass

class Xcellent:
    implements(IAttrX)
    def x(self):
        return 'x!'

class DoubleXAdapter:
    num = 42
    def __init__(self, original):
        self.original = original
    def xx(self):
        return (self.original.x(), self.original.x())
    def __cmp__(self, other):
        return cmp(self.num, other.num)

components.registerAdapter(DoubleXAdapter, IAttrX, IAttrXX)

class TestMetaInterface(unittest.TestCase):

    def testBasic(self):
        n = MetaNumber(1)
        self.assertEquals(IMeta(n).add(1), 2)

    def testComponentizedInteraction(self):
        c = ComponentNumber()
        IMeta(c).add(1)
        IMeta(c).add(1)
        self.assertEquals(IMeta(c).add(1), 3)

    def testAdapterWithCmp(self):
        # Make sure that a __cmp__ on an adapter doesn't break anything
        xx = IAttrXX(Xcellent())
        self.assertEqual(('x!', 'x!'), xx.xx())


class RegistrationTestCase(unittest.TestCase):
    """
    Tests for adapter registration.
    """
    def _registerAdapterForClassOrInterface(self, original):
        adapter = lambda o: None
        class TheInterface(Interface):
            pass
        components.registerAdapter(adapter, original, TheInterface)
        self.assertIdentical(
            components.getAdapterFactory(original, TheInterface, None),
            adapter)


    def test_registerAdapterForClass(self):
        """
        Test that an adapter from a class can be registered and then looked
        up.
        """
        class TheOriginal(object):
            pass
        return self._registerAdapterForClassOrInterface(TheOriginal)


    def test_registerAdapterForInterface(self):
        """
        Test that an adapter from an interface can be registered and then
        looked up.
        """
        class TheOriginal(Interface):
            pass
        return self._registerAdapterForClassOrInterface(TheOriginal)


    def _duplicateAdapterForClassOrInterface(self, original):
        firstAdapter = lambda o: False
        secondAdapter = lambda o: True
        class TheInterface(Interface):
            pass
        components.registerAdapter(firstAdapter, original, TheInterface)
        self.assertRaises(
            ValueError,
            components.registerAdapter,
            secondAdapter, original, TheInterface)
        # Make sure that the original adapter is still around as well
        self.assertIdentical(
            components.getAdapterFactory(original, TheInterface, None),
            firstAdapter)


    def test_duplicateAdapterForClass(self):
        """
        Test that attempting to register a second adapter from a class
        raises the appropriate exception.
        """
        class TheOriginal(object):
            pass
        return self._duplicateAdapterForClassOrInterface(TheOriginal)


    def test_duplicateAdapterForInterface(self):
        """
        Test that attempting to register a second adapter from an interface
        raises the appropriate exception.
        """
        class TheOriginal(Interface):
            pass
        return self._duplicateAdapterForClassOrInterface(TheOriginal)


    def _duplicateAdapterForClassOrInterfaceAllowed(self, original):
        firstAdapter = lambda o: False
        secondAdapter = lambda o: True
        class TheInterface(Interface):
            pass
        components.registerAdapter(firstAdapter, original, TheInterface)
        components.ALLOW_DUPLICATES = True
        try:
            components.registerAdapter(secondAdapter, original, TheInterface)
            self.assertIdentical(
                components.getAdapterFactory(original, TheInterface, None),
                secondAdapter)
        finally:
            components.ALLOW_DUPLICATES = False

        # It should be rejected again at this point
        self.assertRaises(
            ValueError,
            components.registerAdapter,
            firstAdapter, original, TheInterface)

        self.assertIdentical(
            components.getAdapterFactory(original, TheInterface, None),
            secondAdapter)

    def test_duplicateAdapterForClassAllowed(self):
        """
        Test that when L{components.ALLOW_DUPLICATES} is set to a true
        value, duplicate registrations from classes are allowed to override
        the original registration.
        """
        class TheOriginal(object):
            pass
        return self._duplicateAdapterForClassOrInterfaceAllowed(TheOriginal)


    def test_duplicateAdapterForInterfaceAllowed(self):
        """
        Test that when L{components.ALLOW_DUPLICATES} is set to a true
        value, duplicate registrations from interfaces are allowed to
        override the original registration.
        """
        class TheOriginal(Interface):
            pass
        return self._duplicateAdapterForClassOrInterfaceAllowed(TheOriginal)


    def _multipleInterfacesForClassOrInterface(self, original):
        adapter = lambda o: None
        class FirstInterface(Interface):
            pass
        class SecondInterface(Interface):
            pass
        components.registerAdapter(adapter, original, FirstInterface, SecondInterface)
        self.assertIdentical(
            components.getAdapterFactory(original, FirstInterface, None),
            adapter)
        self.assertIdentical(
            components.getAdapterFactory(original, SecondInterface, None),
            adapter)


    def test_multipleInterfacesForClass(self):
        """
        Test the registration of an adapter from a class to several
        interfaces at once.
        """
        class TheOriginal(object):
            pass
        return self._multipleInterfacesForClassOrInterface(TheOriginal)


    def test_multipleInterfacesForInterface(self):
        """
        Test the registration of an adapter from an interface to several
        interfaces at once.
        """
        class TheOriginal(Interface):
            pass
        return self._multipleInterfacesForClassOrInterface(TheOriginal)


    def _subclassAdapterRegistrationForClassOrInterface(self, original):
        firstAdapter = lambda o: True
        secondAdapter = lambda o: False
        class TheSubclass(original):
            pass
        class TheInterface(Interface):
            pass
        components.registerAdapter(firstAdapter, original, TheInterface)
        components.registerAdapter(secondAdapter, TheSubclass, TheInterface)
        self.assertIdentical(
            components.getAdapterFactory(original, TheInterface, None),
            firstAdapter)
        self.assertIdentical(
            components.getAdapterFactory(TheSubclass, TheInterface, None),
            secondAdapter)


    def test_subclassAdapterRegistrationForClass(self):
        """
        Test that an adapter to a particular interface can be registered
        from both a class and its subclass.
        """
        class TheOriginal(object):
            pass
        return self._subclassAdapterRegistrationForClassOrInterface(TheOriginal)


    def test_subclassAdapterRegistrationForInterface(self):
        """
        Test that an adapter to a particular interface can be registered
        from both an interface and its subclass.
        """
        class TheOriginal(Interface):
            pass
        return self._subclassAdapterRegistrationForClassOrInterface(TheOriginal)



class IProxiedInterface(Interface):
    """
    An interface class for use by L{proxyForInterface}.
    """

    ifaceAttribute = Attribute("""
        An example declared attribute, which should be proxied.""")

    def yay(*a, **kw):
        """
        A sample method which should be proxied.
        """

class IProxiedSubInterface(IProxiedInterface):
    """
    An interface that derives from another for use with L{proxyForInterface}.
    """

    def boo(self):
        """
        A different sample method which should be proxied.
        """



class Yayable(object):
    """
    A provider of L{IProxiedInterface} which increments a counter for
    every call to C{yay}.

    @ivar yays: The number of times C{yay} has been called.
    """
    implements(IProxiedInterface)

    def __init__(self):
        self.yays = 0
        self.yayArgs = []

    def yay(self, *a, **kw):
        """
        Increment C{self.yays}.
        """
        self.yays += 1
        self.yayArgs.append((a, kw))
        return self.yays


class Booable(object):
    """
    An implementation of IProxiedSubInterface
    """
    implements(IProxiedSubInterface)
    yayed = False
    booed = False
    def yay(self):
        """
        Mark the fact that 'yay' has been called.
        """
        self.yayed = True


    def boo(self):
        """
        Mark the fact that 'boo' has been called.1
        """
        self.booed = True



class IMultipleMethods(Interface):
    """
    An interface with multiple methods.
    """

    def methodOne():
        """
        The first method. Should return 1.
        """

    def methodTwo():
        """
        The second method. Should return 2.
        """



class MultipleMethodImplementor(object):
    """
    A precise implementation of L{IMultipleMethods}.
    """

    def methodOne(self):
        """
        @return: 1
        """
        return 1


    def methodTwo(self):
        """
        @return: 2
        """
        return 2



class ProxyForInterfaceTests(unittest.TestCase):
    """
    Tests for L{proxyForInterface}.
    """

    def test_original(self):
        """
        Proxy objects should have an C{original} attribute which refers to the
        original object passed to the constructor.
        """
        original = object()
        proxy = proxyForInterface(IProxiedInterface)(original)
        self.assertIdentical(proxy.original, original)


    def test_proxyMethod(self):
        """
        The class created from L{proxyForInterface} passes methods on an
        interface to the object which is passed to its constructor.
        """
        klass = proxyForInterface(IProxiedInterface)
        yayable = Yayable()
        proxy = klass(yayable)
        proxy.yay()
        self.assertEquals(proxy.yay(), 2)
        self.assertEquals(yayable.yays, 2)


    def test_proxyAttribute(self):
        """
        Proxy objects should proxy declared attributes, but not other
        attributes.
        """
        yayable = Yayable()
        yayable.ifaceAttribute = object()
        proxy = proxyForInterface(IProxiedInterface)(yayable)
        self.assertIdentical(proxy.ifaceAttribute, yayable.ifaceAttribute)
        self.assertRaises(AttributeError, lambda: proxy.yays)


    def test_proxySetAttribute(self):
        """
        The attributes that proxy objects proxy should be assignable and affect
        the original object.
        """
        yayable = Yayable()
        proxy = proxyForInterface(IProxiedInterface)(yayable)
        thingy = object()
        proxy.ifaceAttribute = thingy
        self.assertIdentical(yayable.ifaceAttribute, thingy)


    def test_proxyDeleteAttribute(self):
        """
        The attributes that proxy objects proxy should be deletable and affect
        the original object.
        """
        yayable = Yayable()
        yayable.ifaceAttribute = None
        proxy = proxyForInterface(IProxiedInterface)(yayable)
        del proxy.ifaceAttribute
        self.assertFalse(hasattr(yayable, 'ifaceAttribute'))


    def test_multipleMethods(self):
        """
        [Regression test] The proxy should send its method calls to the correct
        method, not the incorrect one.
        """
        multi = MultipleMethodImplementor()
        proxy = proxyForInterface(IMultipleMethods)(multi)
        self.assertEquals(proxy.methodOne(), 1)
        self.assertEquals(proxy.methodTwo(), 2)


    def test_subclassing(self):
        """
        It is possible to subclass the result of L{proxyForInterface}.
        """

        class SpecializedProxy(proxyForInterface(IProxiedInterface)):
            """
            A specialized proxy which can decrement the number of yays.
            """
            def boo(self):
                """
                Decrement the number of yays.
                """
                self.original.yays -= 1

        yayable = Yayable()
        special = SpecializedProxy(yayable)
        self.assertEquals(yayable.yays, 0)
        special.boo()
        self.assertEquals(yayable.yays, -1)


    def test_proxyName(self):
        """
        The name of a proxy class indicates which interface it proxies.
        """
        proxy = proxyForInterface(IProxiedInterface)
        self.assertEquals(
            proxy.__name__,
            "(Proxy for "
            "twisted.python.test.test_components.IProxiedInterface)")


    def test_implements(self):
        """
        The resulting proxy implements the interface that it proxies.
        """
        proxy = proxyForInterface(IProxiedInterface)
        self.assertTrue(IProxiedInterface.implementedBy(proxy))


    def test_proxyDescriptorGet(self):
        """
        _ProxyDescriptor's __get__ method should return the appropriate
        attribute of its argument's 'original' attribute if it is invoked with
        an object.  If it is invoked with None, it should return a false
        class-method emulator instead.

        For some reason, Python's documentation recommends to define
        descriptors' __get__ methods with the 'type' parameter as optional,
        despite the fact that Python itself never actually calls the descriptor
        that way.  This is probably do to support 'foo.__get__(bar)' as an
        idiom.  Let's make sure that the behavior is correct.  Since we don't
        actually use the 'type' argument at all, this test calls it the
        idiomatic way to ensure that signature works; test_proxyInheritance
        verifies the how-Python-actually-calls-it signature.
        """
        class Sample:
            called = False
            def hello(self):
                self.called = True
        fakeProxy = Sample()
        testObject = Sample()
        fakeProxy.original = testObject
        pd = components._ProxyDescriptor("hello", "original")
        self.assertEquals(pd.__get__(fakeProxy), testObject.hello)
        fakeClassMethod = pd.__get__(None)
        fakeClassMethod(fakeProxy)
        self.failUnless(testObject.called)


    def test_proxyInheritance(self):
        """
        Subclasses of the class returned from L{proxyForInterface} should be
        able to upcall methods by reference to their superclass, as any normal
        Python class can.
        """
        class YayableWrapper(proxyForInterface(IProxiedInterface)):
            """
            This class does not override any functionality.
            """

        class EnhancedWrapper(YayableWrapper):
            """
            This class overrides the 'yay' method.
            """
            wrappedYays = 1
            def yay(self, *a, **k):
                self.wrappedYays += 1
                return YayableWrapper.yay(self, *a, **k) + 7

        yayable = Yayable()
        wrapper = EnhancedWrapper(yayable)
        self.assertEquals(wrapper.yay(3, 4, x=5, y=6), 8)
        self.assertEquals(yayable.yayArgs,
                          [((3, 4), dict(x=5, y=6))])


    def test_interfaceInheritance(self):
        """
        Proxies of subinterfaces generated with proxyForInterface should allow
        access to attributes of both the child and the base interfaces.
        """
        proxyClass = proxyForInterface(IProxiedSubInterface)
        booable = Booable()
        proxy = proxyClass(booable)
        proxy.yay()
        proxy.boo()
        self.failUnless(booable.yayed)
        self.failUnless(booable.booed)


    def test_attributeCustomization(self):
        """
        The original attribute name can be customized via the
        C{originalAttribute} argument of L{proxyForInterface}: the attribute
        should change, but the methods of the original object should still be
        callable, and the attributes still accessible.
        """
        yayable = Yayable()
        yayable.ifaceAttribute = object()
        proxy = proxyForInterface(
            IProxiedInterface, originalAttribute='foo')(yayable)
        self.assertIdentical(proxy.foo, yayable)

        # Check the behavior
        self.assertEquals(proxy.yay(), 1)
        self.assertIdentical(proxy.ifaceAttribute, yayable.ifaceAttribute)
        thingy = object()
        proxy.ifaceAttribute = thingy
        self.assertIdentical(yayable.ifaceAttribute, thingy)
        del proxy.ifaceAttribute
        self.assertFalse(hasattr(yayable, 'ifaceAttribute'))

