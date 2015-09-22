import support
from support import TODO, TestCase, test_hash, test_equality

if __name__ == '__main__':
    support.adjust_path()
### /Bookkeeping ###

import types

import typecheck

def check_type(typ, obj):
    typecheck.check_type(typ, None, obj)
    
class Test_Or(TestCase):
    def setUp(self):
        from typecheck import Or
    
        def or_type(obj):
            check_type(Or(int, float), obj)
    
        self.or_type = or_type
        
    def test_IsOneOf_alias(self):
        from typecheck import Or, IsOneOf
        
        assert Or is IsOneOf
        
    def test_constructor(self):
        from typecheck import Or
        
        try:
            Or()
        except TypeError, e:
            assert str(e) == "__init__() takes at least 3 arguments (1 given)"
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_distinct_parameters(self):
        from typecheck import Or
        
        try:
            Or(int, int)
        except TypeError, e:
            self.assertEqual(str(e), "there must be at least 2 distinct parameters to __init__()")
        else:
            raise AssertionError("Failed to raise TypeError")
        
    def test_success(self):
        from typecheck import Or, And
    
        # Built-in types
        self.or_type(5)
        self.or_type(7.0)
        
        class A(object): pass # New-style classes
        class B: pass # Old-style classes
        class C(A, B): pass
        
        check_type(Or(A, B), C())
        check_type(Or(A, B), A())
        check_type(Or(A, B), B())
        
        # Nested extension classes
        check_type(Or(A, And(A, B)), C())
        
        # Complex-er types
        check_type(Or((int, int), [int, float]), (5, 6))
        
    def test_failure(self):
        from typecheck import _TC_TypeError, Or
    
        try:
            self.or_type("foo")
        except _TC_TypeError, e:
            assert e.right == Or(int, float)
            assert e.wrong == str
        else:
            self.fail("Passed incorrectly")
            
    def test_equality(self):
        from typecheck import Or, And
        
        eq_tests = [
            (Or(int, float), Or(int, float)),
            (Or(int, float), Or(int, int, int, float)),
            (Or(int, int, int, float), Or(int, float)),
            (Or(int, float), Or(float, int)),
            (Or(Or(int, str), float), Or(float, Or(str, int))),
            (Or(Or(int, str), float), Or(int, str, float)) ]
            
        ne_tests = [
            (Or(float, str), Or(int, float)),
            (Or(int, float, str), Or(int, float)),
            (Or(int, float), Or(int, float, str)),
            (Or(int, float), And(int, float)) ]
            
        test_equality(eq_tests, ne_tests)

    def test_hash(self):
        from typecheck import Or, And
        
        eq_tests = [
            (Or(int, float), Or(int, float)),
            (Or(int, float), Or(int, int, int, float)),
            (Or(int, int, int, float), Or(int, float)),
            (Or(int, float), Or(float, int)),
            (Or(Or(int, str), float), Or(float, Or(str, int))),
            (Or(Or(int, str), float), Or(int, str, float)) ]
            
        ne_tests = [
            (Or(float, str), Or(int, float)),
            (Or(int, float, str), Or(int, float)),
            (Or(int, float), Or(int, float, str)),
            (Or(int, float), And(int, float)) ]
            
        test_hash(eq_tests, ne_tests)
            
class Test_And(TestCase):
    def test_IsAllOf_alias(self):
        from typecheck import And, IsAllOf
        
        assert And is IsAllOf

    def test_success(self):
        from typecheck import And
    
        class A: pass
        class B: pass
        class C(A, B): pass
            
        check_type(And(A, B), C())
        
    def test_distinct_parameters(self):
        from typecheck import And
        
        try:
            And(int, int)
        except TypeError, e:
            self.assertEqual(str(e), "there must be at least 2 distinct parameters to __init__()")
        else:
            raise AssertionError("Failed to raise TypeError")
        
    def test_failure(self):
        from typecheck import _TC_TypeError, And
    
        try:
            check_type(And(int, float), "foo")
        except _TC_TypeError, e:
            assert e.right == And(int, float)
            assert e.wrong == str
        else:
            self.fail("Passed incorrectly")
            
    def test_equality(self):
        from typecheck import And, Or
        
        eq_tests = [
            (And(int, float), And(int, float)),
            (And(int, float), And(int, int, int, float)),
            (And(int, int, int, float), And(int, float)),
            (And(int, float), And(float, int)),
            (And(And(int, str), float), And(float, And(str, int))),
            (And(And(int, str), float), And(int, str, float)),
            (And(And(int, float), And(str, int)), And(int, float, str)) ]
            
        ne_tests = [
            (And(float, str), And(int, float)),
            (And(int, float, str), And(int, float)),
            (And(int, float), And(int, float, str)),
            (And(int, float), Or(int, float)) ]
            
        test_equality(eq_tests, ne_tests)
                    
    def test_hash(self):
        from typecheck import And, Or
        
        eq_tests = [
            (And(int, float), And(int, float)),
            (And(int, float), And(int, int, int, float)),
            (And(int, int, int, float), And(int, float)),
            (And(int, float), And(float, int)),
            (And(And(int, str), float), And(float, And(str, int))),
            (And(And(int, str), float), And(int, str, float)),
            (And(And(int, float), And(str, int)), And(int, float, str)) ]
            
        ne_tests = [
            (And(float, str), And(int, float)),
            (And(int, float, str), And(int, float)),
            (And(int, float), And(int, float, str)),
            (And(int, float), Or(int, float)) ]
            
        test_hash(eq_tests, ne_tests)

class Test_Not(TestCase):
    def test_IsNoneOf_alias(self):
        from typecheck import Not, IsNoneOf
        
        assert Not is IsNoneOf

    def test_constructor(self):
        from typecheck import Not
        
        try:
            Not()
        except TypeError, e:
            assert str(e) == "__init__() takes at least 2 arguments (1 given)"
        else:
            raise AssertionError("Failed to raise TypeError")

    def test_success(self):
        from typecheck import Not
    
        check_type(Not(int), 4.0)
        check_type(Not(int, float), 'four')
        
        class A: pass
        class B: pass
        class C: pass
            
        check_type(Not(A, B, int), C())
        
    def test_failure_1(self):
        from typecheck import _TC_TypeError, Not
    
        try:
            check_type(Not(int), 4)
        except _TC_TypeError, e:
            assert e.right == Not(int)
            assert e.wrong == int
        else:
            self.fail("Passed incorrectly")
            
    def test_failure_2(self):
        from typecheck import _TC_TypeError, Not
    
        try:
            check_type(Not(int, float), 4.0)
        except _TC_TypeError, e:
            assert e.right == Not(int, float)
            assert e.wrong == float
        else:
            self.fail("Passed incorrectly")
            
    def test_failure_3(self):
        from typecheck import _TC_TypeError, Not
    
        class A: pass
        class B: pass
        class C(A, B): pass
            
        try:
            check_type(Not(A, B, int), C()) 
        except _TC_TypeError, e:
            assert e.right == Not(A, B, int)
            assert e.wrong == C
        else:
            self.fail("Passed incorrectly")
            
    def test_equality(self):
        from typecheck import Not, Or
        
        eq_tests = [
            (Not(int, float), Not(int, float)),
            (Not(int, float), Not(int, int, int, float)),
            (Not(int, int, int, float), Not(int, float)),
            (Not(int, float), Not(float, int)),
            (Not(Not(int, str), float), Not(float, Not(str, int))) ]
            
        ne_tests = [
            (Not(float, str), Not(int, float)),
            (Not(int, float, str), Not(int, float)),
            (Not(int, float), Not(int, float, str)),
            (Not(int, float), Or(int, float)),
            (Not(Not(int, str), float), Not(int, str, float)),
            (Not(Not(int, float), Not(str, int)), Not(int, float, str)) ]
            
        test_equality(eq_tests, ne_tests)
                    
    def test_hash(self):
        from typecheck import Not, Or
        
        eq_tests = [
            (Not(int, float), Not(int, float)),
            (Not(int, float), Not(int, int, int, float)),
            (Not(int, int, int, float), Not(int, float)),
            (Not(int, float), Not(float, int)),
            (Not(Not(int, str), float), Not(float, Not(str, int))) ]
            
        ne_tests = [
            (Not(float, str), Not(int, float)),
            (Not(int, float, str), Not(int, float)),
            (Not(int, float), Not(int, float, str)),
            (Not(int, float), Or(int, float)),
            (Not(Not(int, str), float), Not(int, str, float)),
            (Not(Not(int, float), Not(str, int)), Not(int, float, str)) ]
            
        test_hash(eq_tests, ne_tests)
        
class Test_Any(TestCase):
    def test_args_and_return_pass(self):
        from typecheck import typecheck_args, typecheck_return, Any
        
        def run_test(dec):
            @dec(Any())
            def foo(a):
                return a

            assert foo(foo) == foo
            assert foo(5) == 5
            assert foo(([], [], 5)) == ([], [], 5)
            
        run_test(typecheck_args)
        run_test(typecheck_return)
        
    def test_yield_pass(self):
        from typecheck import typecheck_yield, Any
        
        @typecheck_yield(Any())
        def foo(a):
            yield a
            
        assert foo(5).next() == 5
        assert foo({}).next() == {}
        assert foo(foo).next() == foo
        
    def test_equality(self):
        from typecheck import Any
        
        assert Any() == Any()
        assert not Any() != Any()
        
    def test_hash(self):
        from typecheck import Any
        
        assert hash(Any()) == hash(Any())
        assert not hash(Any()) != hash(Any())
        
class Test_Empty(TestCase):
    def test_bad_constructor_1(self):
        from typecheck import Empty
        
        try:
            Empty()
        except TypeError, e:
            self.assertEqual(str(e), "__init__() takes exactly 2 arguments (1 given)")
        else:
            raise AssertionError("Failed to raise TypeError")
        
    def test_bad_constructor_2(self):
        from typecheck import Empty
        
        try:
            Empty(dict, list)
        except TypeError, e:
            self.assertEqual(str(e), "__init__() takes exactly 2 arguments (3 given)")
        else:
            raise AssertionError("Failed to raise TypeError")

    def test_bad_empty_type(self):
        from typecheck import Empty
        
        for t in (int, float):
            try:
                Empty(t)
            except TypeError:
                pass
            else:
                raise AssertionError("Failed to raise TypeError for %s" % t)

    def test_list_success(self):
        from typecheck import Empty
    
        check_type(Empty(list), [])
    
    def test_list_failure(self):
        from typecheck import Empty, _TC_LengthError
        
        try:
            check_type(Empty(list), [5, 6])
        except _TC_LengthError, e:
            assert e.wrong == 2
            assert e.right == 0
        else:
            self.fail("Passed incorrectly")
            
    def test_dict_success(self):
        from typecheck import Empty
    
        check_type(Empty(dict), {})
    
    def test_dict_failure(self):
        from typecheck import Empty, _TC_LengthError, _TC_DictError
        
        try:
            check_type(Empty(dict), {'f': 5})
        except _TC_DictError, e:
            assert isinstance(e.inner, _TC_LengthError)
            assert e.inner.wrong == 1
            assert e.inner.right == 0
        else:
            self.fail("Passed incorrectly")
            
    def test_set_success(self):
        from typecheck import Empty
        
        check_type(Empty(set), set())
        
    def test_set_failure(self):
        from typecheck import Empty, _TC_LengthError
        
        try:
            check_type(Empty(set), set([5, 6]))
        except _TC_LengthError, e:
            assert e.wrong == 2
            assert e.right == 0
        else:
            self.fail("Passed incorrectly")
            
    def test_userdef_success(self):
        from typecheck import Empty
        
        class A(object):
            def __len__(self):
                return 0
                
        check_type(Empty(A), A())
        
    def test_userdef_failure(self):
        from typecheck import Empty, _TC_LengthError
        
        class A(object):
            def __len__(self):
                return 2
        
        try:
            check_type(Empty(A), A())
        except _TC_LengthError, e:
            assert e.wrong == 2
            assert e.right == 0
        else:
            self.fail("Passed incorrectly")
            
    def test_inappropriate_type(self):
        from typecheck import Empty, _TC_TypeError
        
        for t in (dict, list, set):
            try:
                check_type(Empty(t), 5)
            except _TC_TypeError, e:
                assert e.right == t
                assert e.wrong == int
            else:
                raise AssertionError("Failed to raise _TC_TypeError")
            
    def test_equality(self):
        from typecheck import Empty
        
        eq_tests = [
            (Empty(list), Empty(list)),
            (Empty(dict), Empty(dict)),
            (Empty(set), Empty(set)) ]
            
        ne_tests = [
            (Empty(list), Empty(dict)),
            (Empty(list), Empty(set)),
            (Empty(dict), Empty(list)),
            (Empty(dict), Empty(set)),
            (Empty(set), Empty(list)),
            (Empty(set), Empty(dict)), ]
            
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import Empty
        
        eq_tests = [
            (Empty(list), Empty(list)),
            (Empty(dict), Empty(dict)),
            (Empty(set), Empty(set)) ]
            
        ne_tests = [
            (Empty(list), Empty(dict)),
            (Empty(list), Empty(set)),
            (Empty(dict), Empty(set)) ]
            
        test_hash(eq_tests, ne_tests)

class Test_IsCallable(TestCase):
    def test_accepts_no_args(self):
        from typecheck import IsCallable
        
        try:
            IsCallable(5, 6, 7)
        except TypeError, e:
            assert str(e) == "__init__() takes exactly 1 argument (4 given)"
        else:
            raise AssertionError("Failed to raise TypeError")

    def test_builtins(self):
        from typecheck import IsCallable
        
        check_type(IsCallable(), pow)
        
    def test_newstyle_classes(self):
        from typecheck import IsCallable
        
        class A(object):
            pass
        
        check_type(IsCallable(), A)
        
    def test_oldstyle_classes(self):
        from typecheck import IsCallable
        
        class A:
            pass
        
        check_type(IsCallable(), A)
        
    def test_userdefined_functions(self):
        from typecheck import IsCallable
        
        def foo(a):
            return a
            
        check_type(IsCallable(), foo)
        
    def test_callable_instances_newstyle(self):
        from typecheck import IsCallable
        
        class A(object):
            def __call__(self):
                pass
            
        check_type(IsCallable(), A())
        
    def test_callable_instances_oldstyle(self):
        from typecheck import IsCallable
        
        class A:
            def __call__(self):
                pass
            
        check_type(IsCallable(), A())
        
    def test_args_fail(self):
        from typecheck import typecheck_args, IsCallable
        from typecheck import TypeCheckError, _TC_IndexError, _TC_TypeError
        
        @typecheck_args(IsCallable())
        def foo(a):
            return a

        try:
            foo(5)
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_TypeError)
            assert e.internal.right == 'a callable'
            assert e.internal.wrong == int
            
            self.assertEquals(str(e), "Argument a: for 5, expected a callable, got <type 'int'>")
        else:
            raise AssertionError("Failed to raise TypeCheckError")
            
    def test_equality(self):
        from typecheck import IsCallable
        
        assert IsCallable() == IsCallable()
        assert not IsCallable() != IsCallable()
        
    def test_hash(self):
        from typecheck import IsCallable
        
        assert hash(IsCallable()) == hash(IsCallable())
            
class Test_HasAttr(TestCase):
    def test_empty(self):
        from typecheck import HasAttr
        
        try:
            HasAttr()
        except TypeError, e:
            self.assertEqual(str(e), "__init__() takes at least 2 arguments (1 given)")
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_success_named_only(self):
        from typecheck import HasAttr
        
        class A(object):
            def __init__(self):
                self.foo = 5
                self.bar = 6
                
        check_type(HasAttr(['foo', 'bar']), A())
        
    def test_success_typed_only(self):
        from typecheck import HasAttr
        
        class A(object):
            def __init__(self):
                self.foo = 5
                self.bar = 6
                
        check_type(HasAttr({'foo':int, 'bar':int}), A())
        
    def test_success_named_and_typed(self):
        from typecheck import HasAttr
        
        class A(object):
            def __init__(self):
                self.foo = 5
                self.bar = 6
                
        check_type(HasAttr(['foo'], {'bar': int}), A())
        check_type(HasAttr({'bar': int}, ['foo']), A())
        
    def test_failure_missing_attr(self):
        from typecheck import HasAttr, _TC_MissingAttrError
        
        class A(object):
            def __init__(self):
                self.foo = 5
                
            def __str__(self):
                return "A()"
                
        try:
            check_type(HasAttr(['foo', 'bar']), A())
        except _TC_MissingAttrError, e:
            assert e.attr == 'bar'
            self.assertEqual(e.error_message(), "missing attribute bar")
        else:
            raise AssertionError("Did not raise _TC_MissingAttrError")
            
    def test_failure_badly_typed_attr(self):
        from typecheck import HasAttr, _TC_AttrError, _TC_TypeError
        
        class A(object):
            def __init__(self):
                self.foo = 5
                self.bar = 7.0
                
            def __str__(self):
                return "A()"
                
        for args in ((['foo'], {'bar': int}), ({'bar': int}, ['foo'])):     
            try:
                check_type(HasAttr(*args), A())
            except _TC_AttrError, e:
                assert e.attr == 'bar'
                assert isinstance(e.inner, _TC_TypeError)
                assert e.inner.right == int
                assert e.inner.wrong == float
                self.assertEqual(e.error_message(), "as for attribute bar, expected <type 'int'>, got <type 'float'>")
            else:
                raise AssertionError("Did not raise _TC_AttrError")
                
    def test_equality(self):
        from typecheck import HasAttr, Any
        
        eq_tests = [
            (HasAttr(['a']), HasAttr(['a'])),
            (HasAttr(['a', 'b']), HasAttr(['b', 'a'])),
            (HasAttr({'a': int}), HasAttr({'a': int})),
            (HasAttr({'a': int, 'b': int}), HasAttr({'b': int, 'a': int})),
            (HasAttr({'a': HasAttr(['a'])}), HasAttr({'a': HasAttr(['a'])})),
            (HasAttr(['a'], {'b': int, 'c': int}), HasAttr(['a'], {'b': int, 'c': int})),
            (HasAttr(['a']), HasAttr({'a': Any()})),
            (HasAttr({'a': int, 'b': float, 'c': str}), HasAttr({'a': int, 'b': float, 'c': str})) ]
            
        ne_tests = [
            (HasAttr(['a', 'b']), HasAttr(['b'])),
            (HasAttr(['a', 'b']), HasAttr(['a'], {'b': int})),
            (HasAttr({'a': HasAttr(['a'])}), HasAttr({'a': HasAttr(['b'])})), ]
            
        test_equality(eq_tests, ne_tests, 100)
        
    def test_hash(self):
        from typecheck import HasAttr, Any
        
        eq_tests = [
            (HasAttr(['a']), HasAttr(['a'])),
            (HasAttr(['a', 'b']), HasAttr(['b', 'a'])),
            (HasAttr({'a': int}), HasAttr({'a': int})),
            (HasAttr({'a': int, 'b': int}), HasAttr({'b': int, 'a': int})),
            (HasAttr({'a': HasAttr(['a'])}), HasAttr({'a': HasAttr(['a'])})),
            (HasAttr(['a'], {'b': int, 'c': int}), HasAttr(['a'], {'b': int, 'c': int})),
            (HasAttr(['a']), HasAttr({'a': Any()})),
            (HasAttr({'a': int, 'b': float, 'c': str}), HasAttr({'a': int, 'b': float, 'c': str})) ]
            
        ne_tests = [
            (HasAttr(['a', 'b']), HasAttr(['b'])),
            (HasAttr(['a', 'b']), HasAttr(['a'], {'b': int})),
            (HasAttr({'a': HasAttr(['a'])}), HasAttr({'a': HasAttr(['b'])})), ]
            
        test_hash(eq_tests, ne_tests, 100)

class Test_IsIterable(TestCase):
    def test_accepts_no_args(self):
        from typecheck import IsIterable
        
        try:
            IsIterable(5, 6, 7)
        except TypeError, e:
            assert str(e) == "__init__() takes exactly 1 argument (4 given)"
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_equality(self):
        from typecheck import IsIterable
        
        assert IsIterable() == IsIterable()
        assert not IsIterable() != IsIterable()

    def test_success_builtins(self):
        from typecheck import IsIterable
        
        for t in (list, tuple, set, dict):
            check_type(IsIterable(), t())
            
    def test_success_generator(self):
        from typecheck import IsIterable
        
        def foo():
            yield 5
            yield 6
            
        check_type(IsIterable(), foo())
            
    def test_success_user_newstyle(self):
        from typecheck import IsIterable
        
        class A(object):
            def __iter__(self):
                yield 5
                yield 6
                
        class B(object):
            def __iter__(self):
                return self
                
            def next(self):
                return 5
                
        for c in (A, B):
            check_type(IsIterable(), c())
            
    def test_success_user_oldstyle(self):
        from typecheck import IsIterable
        
        class A:
            def __iter__(self):
                yield 5
                yield 6
                
        class B:
            def __iter__(self):
                return self
                
            def next(self):
                return 5
                
        for c in (A, B):
            check_type(IsIterable(), c())
            
    def test_failure(self):
        from typecheck import IsIterable, _TC_TypeError
        
        class A(object):
            def __str__(self):
                return "A()"
            
        try:
            check_type(IsIterable(), A())
        except _TC_TypeError, e:
            assert e.right == "an iterable"
            assert e.wrong == A
        else:
            raise AssertionError("Failed to raise _TC_TypeError")
            
    def test_hash(self):
        from typecheck import IsIterable
        
        assert hash(IsIterable()) == hash(IsIterable())
            
class Test_YieldSeq(TestCase):
    def test_bad_seq(self):
        from typecheck import YieldSeq
        
        try:
            YieldSeq()
        except TypeError, e:
            self.assertEqual(str(e), "__init__() takes at least 3 arguments (1 given)")
        else:
            raise AssertionError("Did not raise TypeError")
            
        try:
            YieldSeq(int)
        except TypeError, e:
            self.assertEqual(str(e), "__init__() takes at least 3 arguments (2 given)")
        else:
            raise AssertionError("Did not raise TypeError")
            
    def test_success(self):
        from typecheck import YieldSeq, typecheck_yield
        
        @typecheck_yield(int, YieldSeq(int, int, float))
        def foo(const, seq):
            for o in seq:
                yield (const, o)
        
        const = 5
        seq = [5, 6, 7.0]
        g = foo(const, seq)
        
        for obj in seq:
            assert g.next() == (const, obj)
            
    def test_nested_success(self):
        from typecheck import YieldSeq, typecheck_yield
        
        @typecheck_yield(YieldSeq(float, str, str))
        def bar(seq):
            for o in seq:
                yield o
        
        @typecheck_yield(YieldSeq(float, str, str), YieldSeq(int, int, float))
        def foo(seq_1, seq_2):
            g = bar(seq_1)
        
            for o in seq_2:
                yield (g.next(), o)
        
        seq_1 = [7.0, "i", "i"]
        seq_2 = [5, 6, 7.0]
        g = foo(seq_1, seq_2)
        
        for tup in zip(seq_1, seq_2):
            assert g.next() == tup
            
    def test_parallel_success(self):
        from typecheck import YieldSeq, typecheck_yield
        
        @typecheck_yield(int, YieldSeq(int, int, float))
        def foo(const, seq):
            for o in seq:
                yield (const, o)
        
        const = 5
        seq = [5, 6, 7.0]
        g = foo(const, seq)
        h = foo(const, seq)
        
        for obj in seq:
            assert g.next() == h.next()
        
    def test_failure_1(self):
        from typecheck import YieldSeq, typecheck_yield
        from typecheck import TypeCheckError, _TC_GeneratorError
        from typecheck import _TC_TypeError
        
        @typecheck_yield(YieldSeq(int, int, float))
        def foo():
            yield 5
            yield 7.0
            
        g = foo()
        assert g.next() == 5
        
        try:
            g.next()
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_GeneratorError)
            assert e.internal.yield_no == 2
            assert isinstance(e.internal.inner, _TC_TypeError)
            assert e.internal.inner.right == int
            assert e.internal.inner.wrong == float
            self.assertEqual(str(e), "At yield #2: for 7.0, expected <type 'int'>, got <type 'float'>")
        else:
            raise AssertionError("Did not raise TypeCheckError")
            
    def test_failure_2(self):
        from typecheck import YieldSeq, typecheck_yield
        from typecheck import TypeCheckError, _TC_GeneratorError
        from typecheck import _TC_YieldCountError
        
        @typecheck_yield(YieldSeq(int, float))
        def foo():
            yield 5
            yield 7.0
            yield 8.0
            
        g = foo()
        assert g.next() == 5
        assert g.next() == 7.0
        
        try:
            g.next()
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_GeneratorError)
            assert e.internal.yield_no == 3
            assert isinstance(e.internal.inner, _TC_YieldCountError)
            assert e.internal.inner.expected == 2
            self.assertEqual(str(e), "At yield #3: only expected the generator to yield 2 times")
        else:
            raise AssertionError("Did not raise TypeCheckError")
            
    def test_equality(self):
        from typecheck import YieldSeq, And
        
        eq_tests = [
            (YieldSeq(int, float), YieldSeq(int, float)),
            (YieldSeq(And(int, str), float), YieldSeq(And(int, str), float)) ]
            
        ne_tests = [
            (YieldSeq(float, str), YieldSeq(int, float)),
            (YieldSeq(int, float), YieldSeq(int, int, int, float)),
            (YieldSeq(int, float, str), YieldSeq(int, float)),
            (YieldSeq(int, float), YieldSeq(int, float, str)),
            (YieldSeq(int, float), And(int, float)),
            (YieldSeq(int, int, int, float), YieldSeq(int, float)) ]
            
        test_equality(eq_tests, ne_tests)

    def test_hash(self):
        from typecheck import YieldSeq, And
        
        eq_tests = [
            (YieldSeq(int, float), YieldSeq(int, float)),
            (YieldSeq(And(int, str), float), YieldSeq(And(int, str), float)) ]
            
        ne_tests = [
            (YieldSeq(float, str), YieldSeq(int, float)),
            (YieldSeq(int, float), YieldSeq(int, int, int, float)),
            (YieldSeq(int, float, str), YieldSeq(int, float)),
            (YieldSeq(int, float), YieldSeq(int, float, str)),
            (YieldSeq(int, float), And(int, float)),
            (YieldSeq(int, int, int, float), YieldSeq(int, float)) ]
            
        test_hash(eq_tests, ne_tests)
            
class Test_Xor(TestCase):
    def test_IsOnlyOneOf_alias(self):
        from typecheck import Xor, IsOnlyOneOf
        
        assert Xor is IsOnlyOneOf

    def test_no_parameters(self):
        from typecheck import Xor
        
        try:
            Xor()
        except TypeError, e:
            self.assertEqual(str(e), "__init__() takes at least 3 arguments (1 given)")
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_distinct_parameters(self):
        from typecheck import Xor
        
        try:
            Xor(int, int)
        except TypeError, e:
            self.assertEqual(str(e), "there must be at least 2 distinct parameters to __init__()")
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_success(self):
        from typecheck import Xor, IsCallable
        
        check_type(Xor(dict, IsCallable()), pow)
        check_type(Xor(dict, IsCallable()), {'a': 5})
        
    def test_failure_matched_no_conditions(self):
        from typecheck import Xor, IsIterable
        from typecheck import _TC_XorError, _TC_TypeError
        
        try:
            check_type(Xor(dict, IsIterable()), 5)
        except _TC_XorError, e:
            assert e.matched_conds == 0
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == Xor(dict, IsIterable())
            assert e.inner.wrong == int
            self.assertEqual(e.error_message(), ", expected Xor(<type 'dict'>, IsIterable()), got <type 'int'> (matched neither assertion)")
        else:
            raise AssertionError("Failed to raise _TC_TypeError")
            
    def test_failure_matched_both_conditions(self):
        from typecheck import Xor, IsIterable
        from typecheck import _TC_XorError, _TC_TypeError
        
        try:
            check_type(Xor(dict, IsIterable()), {'a': 5})
        except _TC_XorError, e:
            assert e.matched_conds == 2
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == Xor(dict, IsIterable())
            assert e.inner.wrong == {str: int}
            self.assertEqual(e.error_message(), ", expected Xor(<type 'dict'>, IsIterable()), got {<type 'str'>: <type 'int'>} (matched both assertions)")
        else:
            raise AssertionError("Failed to raise _TC_TypeError")
            
    def test_equality(self):
        from typecheck import Xor, Or
        
        eq_tests = [
            (Xor(int, float), Xor(int, float)),
            (Xor(int, float), Xor(int, int, int, float)),
            (Xor(int, int, int, float), Xor(int, float)),
            (Xor(int, float), Xor(float, int)),
            (Xor(Xor(int, str), float), Xor(float, Xor(str, int))),
            (Xor(Xor(int, str), float), Xor(int, str, float)),
            (Xor(Xor(int, float), Xor(str, int)), Xor(int, float, str)) ]
            
        ne_tests = [
            (Xor(float, str), Xor(int, float)),
            (Xor(int, float, str), Xor(int, float)),
            (Xor(int, float), Xor(int, float, str)),
            (Xor(int, float), Or(int, float)) ]
            
        test_equality(eq_tests, ne_tests)
                    
    def test_hash(self):
        from typecheck import Xor, Or
        
        eq_tests = [
            (Xor(int, float), Xor(int, float)),
            (Xor(int, float), Xor(int, int, int, float)),
            (Xor(int, int, int, float), Xor(int, float)),
            (Xor(int, float), Xor(float, int)),
            (Xor(Xor(int, str), float), Xor(float, Xor(str, int))),
            (Xor(Xor(int, str), float), Xor(int, str, float)),
            (Xor(Xor(int, float), Xor(str, int)), Xor(int, float, str)) ]
            
        ne_tests = [
            (Xor(float, str), Xor(int, float)),
            (Xor(int, float, str), Xor(int, float)),
            (Xor(int, float), Xor(int, float, str)),
            (Xor(int, float), Or(int, float)) ]
            
        test_hash(eq_tests, ne_tests)
        
class Test_Exact(TestCase):
    def test_constructor(self):
        from typecheck import Exact
        
        try:
            Exact()
        except TypeError, e:
            assert str(e) == "__init__() takes exactly 2 arguments (1 given)"
        else:
            raise AssertionError("Failed to raise TypeError")
            
        try:
            Exact(4, 5)
        except TypeError, e:
            assert str(e) == "__init__() takes exactly 2 arguments (3 given)"
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_equality(self):
        from typecheck import Exact
        
        eq_tests = [
                    (Exact(4), Exact(4)),
                    (Exact([4, 5]), Exact([4, 5])),
                    (Exact(Exact), Exact(Exact)) ]
                    
        ne_tests = [
                    (Exact(4), Exact(5)),
                    (Exact([5, 4]), Exact([4, 5])),
                    (Exact(Exact), Exact(object)),
                    (Exact(object), Exact(dict)) ]
                    
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import Exact
        
        eq_tests = [
                    (Exact(4), Exact(4)),
                    (Exact([4, 5]), Exact([4, 5])),
                    (Exact(Exact), Exact(Exact)) ]
                    
        ne_tests = [
                    (Exact(4), Exact(5)),
                    (Exact([5, 4]), Exact([4, 5])),
                    (Exact(Exact), Exact(object)),
                    (Exact(object), Exact(dict)),
                    (Exact([5, 4]), Exact(set([]))) ]
                    
        test_hash(eq_tests, ne_tests)
        
    def test_pass(self):
        from typecheck import Exact, Or
        
        for obj in (5, [5, 6], Exact, Or(int, float)):
            check_type(Exact(obj), obj)
            
    def test_fail_1(self):
        from typecheck import Exact, _TC_ExactError
        
        try:
            check_type(Exact(5), 6)
        except _TC_ExactError, e:
            assert e.wrong == 6
            assert e.right == 5
        else:
            raise AssertionError("Failed to raise _TC_ExactError")
            
    def test_fail_2(self):
        from typecheck import Exact, _TC_ExactError
        
        try:
            check_type(Exact(Exact), Exact(5))
        except _TC_ExactError, e:
            assert e.right == Exact
            assert e.wrong == Exact(5)
        else:
            raise AssertionError("Failed to raise _TC_ExactError")

    def test_fail_3(self):
        from typecheck import Exact, CheckType, _TC_ExactError
        
        try:
            check_type(Exact(CheckType), Exact)
        except _TC_ExactError, e:
            assert e.right == CheckType
            assert e.wrong == Exact
        else:
            raise AssertionError("Failed to raise _TC_ExactError")
            
    def test_combined(self):
        from typecheck import Exact, Or
        
        or_type = Or(Exact(5), Exact(6), Exact(7))
        
        for num in (5, 6, 7):
            check_type(or_type, num)
            
class Test_Length(TestCase):
    def test_constructor(self):
        from typecheck import Length
        
        try:
            Length()
        except TypeError, e:
            assert str(e) == "__init__() takes exactly 2 arguments (1 given)"
        else:
            raise AssertionError("Failed to raise TypeError")
            
        try:
            Length(4, 5)
        except TypeError, e:
            assert str(e) == "__init__() takes exactly 2 arguments (3 given)"
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_bad_argument(self):
        from typecheck import Length
        
        try:
            Length('abc')
        except:
            pass
        else:
            raise AssertionError("Failed to raise an exception")
            
    def test_equality(self):
        from typecheck import Length
        
        eq_tests = [(Length(4), Length(4)), (Length(4.0), Length(4))]
        ne_tests = [(Length(5), Length(4))]
                    
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import Length
        
        eq_tests = [(Length(4), Length(4)), (Length(4.0), Length(4))]
        ne_tests = [(Length(5), Length(4))]
                    
        test_hash(eq_tests, ne_tests)
        
    def test_pass_builtins(self):
        from typecheck import Length
        
        for obj in ([4, 5], (6, 7), {5: 6, 7: 8}):
            check_type(Length(2), obj)
            
    def test_pass_userdef(self):
        from typecheck import Length
        
        class A(object):
            def __len__(self):
                return 5
                
        check_type(Length(5), A())
            
    def test_fail_1(self):
        from typecheck import Length, _TC_LengthError
        
        try:
            check_type(Length(5), [6])
        except _TC_LengthError, e:
            assert e.wrong == 1
            assert e.right == 5
        else:
            raise AssertionError("Failed to raise _TC_LengthError")
            
    def test_fail_2(self):
        from typecheck import Length, _TC_TypeError
        
        try:
            check_type(Length(5), 5)
        except _TC_TypeError, e:
            assert e.right == "something with a __len__ method"
            assert e.wrong == int
        else:
            raise AssertionError("Failed to raise _TC_TypeError")

    def test_combined(self):
        from typecheck import Length, And
        
        and_type = And(Length(3), tuple)
        check_type(and_type, (5, 6, 7))
        
class Test_Class(TestCase):
    def test_equality(self):
        from typecheck import Class
        
        assert Class("ClassB") == Class("ClassB")
        assert not Class("ClassB") != Class("ClassB")
        
        assert Class("ClassA") != Class("ClassB")
        assert not Class("ClassA") == Class("ClassB")
        
        classb_1 = Class("ClassB")
        
        class ClassB(object):
            pass
            
        classb_2 = Class("ClassB")
        
        assert classb_1 == classb_2
        assert not classb_1 != classb_2
        
        check_type(classb_2, ClassB())
        
        assert classb_1 == classb_2
        assert not classb_1 != classb_2
        
    def test_hash(self):
        from typecheck import Class
        
        assert hash(Class("ClassB")) == hash(Class("ClassB"))
        assert hash(Class("ClassA")) != hash(Class("ClassB"))
        assert hash(Class("ClassA")) != hash("ClassA")
        
        classb_1 = Class("ClassB")
        
        class ClassB(object):
            pass
            
        classb_2 = Class("ClassB")
        
        assert hash(classb_1) == hash(classb_2)
        
        check_type(classb_2, ClassB())
        
        assert hash(classb_1) == hash(classb_2)

    def test_no_class(self):
        from typecheck import Class, typecheck_args
        
        ClassB = Class("ClassB")
        
        @typecheck_args(ClassB)
        def foo(a):
            return a
            
        try:
            foo(5)
        except NameError, e:
            self.assertEqual(str(e), "name 'ClassB' is not defined")
        else:
            raise AssertionError("Failed to raise NameError")
            
    def test_success(self):
        from typecheck import Class, typecheck_args, Self
        
        ClassB = Class("ClassB")
        
        class ClassA(object):
            @typecheck_args(Self(), ClassB)
            def foo(self, a):
                return a
                
        class ClassB(object):
            @typecheck_args(Self(), ClassA)
            def foo(self, a):   
                return a
                
        ClassA().foo(ClassB())
        ClassB().foo(ClassA())
        
    def test_failure(self):
        from typecheck import Class, typecheck_args, Self
        from typecheck import TypeCheckError, _TC_TypeError
        
        ClassB = Class("ClassB")
        
        class ClassA(object):
            @typecheck_args(Self(), ClassB)
            def foo(self, a):
                return a
                
        class ClassB(object):
            @typecheck_args(Self(), ClassA)
            def foo(self, a):
                return a
                
        try:
            ClassA().foo(ClassA())
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_TypeError)
            assert e.internal.right == ClassB
            assert e.internal.wrong == ClassA
        else:
            raise AssertionError("Failed to raise TypeCheckError")
            
class Test_Typeclass(TestCase):
    def test_no_args(self):
        from typecheck import Typeclass
        
        try:
            Typeclass()
        except TypeError:
            pass
        else:
            raise AssertionError("Failed to raise TypeError")
            
    def test_instances_1(self):
        from typecheck import Typeclass
        
        tc = Typeclass(list, tuple, set)
        instances = tc.instances()

        assert isinstance(instances, list)
        assert len(instances) == 3
        assert list in instances
        assert tuple in instances
        assert set in instances
        
    def test_instances_2(self):
        from typecheck import Typeclass
        
        tc = Typeclass(list, tuple, Typeclass(str, unicode))
        instances = tc.instances()

        assert isinstance(instances, list)
        assert len(instances) == 4
        assert list in instances
        assert tuple in instances
        assert str in instances
        assert unicode in instances
        
    def test_has_instance(self):
        from typecheck import Typeclass
        
        tc = Typeclass(list, tuple)
        
        assert tc.has_instance(list)
        assert tc.has_instance(tuple)
        assert not tc.has_instance(set)
        
        tc.add_instance(set)
        
        assert tc.has_instance(set)
        
    def test_interface(self):
        from typecheck import Typeclass
        
        tc = Typeclass(list, tuple, set)
        interface = tc.interface()
        
        for method in interface:
            for t in (list, tuple, set):
                assert callable(getattr(t, method))
        
        for method in ('__class__', '__init__', '__new__', '__doc__'):
            assert method not in interface

    def test_pass(self):
        from typecheck import Typeclass
        
        tc = Typeclass(list, set)
        
        # These are a no-brainer
        check_type(tc, list)
        check_type(tc, set)
        
        check_type(tc, tuple)
        
        # XXX Does tuple get added to the instances list?
        # assert tuple in tc.instances()
        
    def test_fail_1(self):
        from typecheck import Typeclass, _TC_AttrError, _TC_TypeError
        from typecheck import IsCallable
        
        class A(object):
            def foo(self):
                pass
                
        class B(object):
            def foo(self):
                pass
        
            def bar(self):
                pass
                
        class C(object):
            def __init__(self):
                self.foo = 5
        
        tc = Typeclass(A, B)
        
        try:
            check_type(tc, C())
        except _TC_AttrError, e:
            assert e.attr == 'foo'
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == IsCallable()
            assert e.inner.wrong == int
        else:
            raise AssertionError("Failed to raise _TC_AttrError")
            
    def test_fail_2(self):
        from typecheck import Typeclass, _TC_MissingAttrError
        
        class A(object):
            def foo(self):
                pass
                
        class B(object):
            def foo(self):
                pass
        
            def bar(self):
                pass
                
        class C(object):
            pass
        
        tc = Typeclass(A, B)
        
        try:
            check_type(tc, C())
        except _TC_MissingAttrError, e:
            assert e.attr == 'foo'
        else:
            raise AssertionError("Failed to raise _TC_MissingAttrError")
        
    def test_add_instance(self):
        from typecheck import Typeclass
        
        tc = Typeclass(list, set, tuple)
        interface_before = tc.interface()
        
        tc.add_instance(dict)
        
        # Adding an instance shouldn't chance the interface...
        assert interface_before == tc.interface()
        
        # but it should change the instances list
        assert dict in tc.instances()
        
    def test_intersect_1(self):
        """
        Make sure .intersect works on other Typeclass instances
        """
        from typecheck import Typeclass
        
        tc_int = Typeclass(int)
        tc_flt = Typeclass(float)
        
        interface_int = set(tc_int.interface())
        interface_flt = set(tc_flt.interface())
        merged_intfc = interface_int.intersection(interface_flt)
        
        tc_int.intersect(tc_flt)
        
        for t in (int, float):
            assert tc_int.has_instance(t)
            
        for method in merged_intfc:
            assert method in tc_int.interface()
            
    def test_intersect_1(self):
        """
        Make sure .intersect works on all iterables
        """
        from typecheck import Typeclass
        
        tc_int = Typeclass(int)
        tc_flt = Typeclass(float)
        
        interface_int = set(tc_int.interface())
        interface_flt = set(tc_flt.interface())
        merged_intfc = interface_int.intersection(interface_flt)
        
        def run_test(itr_type):
            tc_int.intersect(itr_type([float]))

            for t in (int, float):
                assert tc_int.has_instance(t)

            for method in merged_intfc:
                assert method in tc_int.interface()
        
        def gen(seq):
            for o in seq:
                yield o
                
        for itr_type in (tuple, list, set, gen):
            run_test(itr_type)
            
    def test_equality(self):
        from typecheck import Typeclass
        
        eq_tests = [ (Typeclass(int), Typeclass(int)),
                     (Typeclass(int, float), Typeclass(float, int)),
                     (Typeclass(int, int), Typeclass(int)),
                     (Typeclass(int), Typeclass(Typeclass(int))) ]
                     
        ne_tests = [ (Typeclass(int), Typeclass(float)) ]
        
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import Typeclass
        
        eq_tests = [ (Typeclass(int), Typeclass(int)),
                     (Typeclass(int, float), Typeclass(float, int)),
                     (Typeclass(int, int), Typeclass(int)),
                     (Typeclass(int), Typeclass(Typeclass(int))) ]
                     
        ne_tests = [ (Typeclass(int), Typeclass(float)) ]
        
        test_hash(eq_tests, ne_tests)
        
    def test_cope_with_class_changes(self):
        from typecheck import Typeclass, _TC_AttrError, _TC_TypeError
        from typecheck import IsCallable
        
        class A(object):
            def foo(self): pass
            
        class B(object):
            def foo(self): pass
            
        tc = Typeclass(A)
        b = B()
        
        # Should pass
        check_type(tc, b)
        
        B.foo = 5
        
        # B is still cached as known-good
        check_type(tc, b)
            
        tc.recalculate_interface()
        
        try:
            check_type(tc, b)
        except _TC_AttrError, e:
            assert e.attr == 'foo'
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == IsCallable()
            assert e.inner.wrong == int
        else:
            raise AssertionError("Failed to raise _TC_AttrError")

### Bookkeeping ###
if __name__ == '__main__':
    import __main__
    support.run_all_tests(__main__)
