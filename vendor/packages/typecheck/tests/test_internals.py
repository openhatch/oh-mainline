import support
from support import TODO, TestCase, test_hash, test_equality

if __name__ == '__main__':
    support.adjust_path()
### /Bookkeeping ###

import typecheck

def check_type(typ, obj):
    typecheck.check_type(typ, None, obj)

class SingleTests(TestCase):
    def test_success_builtin_types(self):
        from typecheck import Single
        
        check_type(Single(int), 7)
        check_type(Single(float), 7.0)

    def test_success_userdef_classes_oldstyle(self):
        from typecheck import Single
            
        class A: pass
        class B(A): pass
        
        check_type(Single(A), A())
        check_type(Single(A), B())
        check_type(Single(B) ,B())
        
    def test_success_userdef_classes_newstyle(self):
        from typecheck import Single
            
        class A(object): pass
        class B(A): pass
        
        check_type(Single(A), A())
        check_type(Single(A), B())
        check_type(Single(B), B())
        
    def test_failure(self):
        from typecheck import Single, _TC_TypeError
        
        try:
            check_type(Single(int), 7.0)
        except _TC_TypeError, e:
            assert e.right == int
            assert e.wrong == float
        else:
            raise AssertionError("Failed to raise the proper exception")
            
    def test_equality(self):
        from typecheck import Single
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Single(int), Single(int)),
            (Single(A), Single(A)),
            (Single(B), Single(B)) ]
            
        ne_tests = [
            (Single(int), Single(float)),
            (Single(A), Single(B)) ]
        
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import Single
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Single(int), Single(int)),
            (Single(A), Single(A)),
            (Single(B), Single(B)) ]
            
        ne_tests = [
            (Single(int), Single(float)),
            (Single(A), Single(B)) ]
        
        test_hash(eq_tests, ne_tests)

class DictTests(TestCase):
    def setUp(self):
        from typecheck import Dict
    
        def dic(obj):
            check_type(Dict(key=str, val=int), obj)
    
        self.dict = dic

    def test_success(self):
        self.dict({})
        self.dict({ 'a': 1, 'b': 2 })

    def test_key_failure(self):
        from typecheck import _TC_KeyError, _TC_TypeError
    
        try:
            self.dict({1.0: 1, 'b': 2})
        except _TC_KeyError, e:
            assert e.key == 1.0
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.wrong == float
            assert e.inner.right == str
        else:
            self.fail("Passed incorrectly")
        
    def test_val_failure(self):
        from typecheck import _TC_KeyValError, _TC_TypeError
    
        try:
            # 1.0 is not an integer
            self.dict({'a': 1.0, 'b': 2})
        except _TC_KeyValError, e:
            assert e.key == 'a'
            assert e.val == 1.0
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.wrong == float
            assert e.inner.right == int
        else:
            self.fail("Passed incorrectly")
            
    def test_type_failure(self):
        from typecheck import _TC_TypeError
    
        try:
            self.dict( 5.0 )
        except _TC_TypeError, e:
            assert e.wrong is float
            assert e.right == { str: int }
        else:
            self.fail("Passed incorrectly")
            
    def test_equality(self):
        from typecheck import Dict
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Dict(str, int), Dict(str, int)),
            (Dict(str, A), Dict(str, A)),
            (Dict(str, Dict(str, int)), Dict(str, Dict(str, int))) ]
            
        ne_tests = [
            (Dict(str, int), Dict(int, str)),
            (Dict(str, int), {'a': 5}),
            (Dict(str, Dict(str, int)), Dict(str, Dict(int, str))) ]
        
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import Dict
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Dict(str, int), Dict(str, int)),
            (Dict(str, A), Dict(str, A)),
            (Dict(str, Dict(str, int)), Dict(str, Dict(str, int))) ]
            
        ne_tests = [
            (Dict(str, int), Dict(int, str)),
            (Dict(str, Dict(str, int)), Dict(str, Dict(int, str))) ]
        
        test_hash(eq_tests, ne_tests)
            
class TupleTests(TestCase):
    def setUp(self):
        from typecheck import Tuple
    
        def tup(obj):
            check_type(Tuple(int, float, int), obj)
    
        self.tuple = tup

    def test_success(self):
        self.tuple( (4, 5.0, 4) )

    def test_type_failure(self):
        from typecheck import _TC_TypeError
    
        try:
            self.tuple( [4, 5, 6] )
        except _TC_TypeError, e:
            assert e.right == (int, float, int)
            assert e.wrong == [int]
        else:
            self.fail("Passed incorrectly")
            
    def test_index_failure(self):
        from typecheck import _TC_IndexError, _TC_TypeError
        
        try:
            self.tuple( (5, 'a', 4) )
        except _TC_IndexError, e:
            assert e.index == 1
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.wrong == str
            assert e.inner.right == float
        else:
            self.fail("Passed incorrectly")
            
    def test_length_error(self):
        from typecheck import _TC_TypeError
        
        try:
            self.tuple( (3, 4) )
        except _TC_TypeError, e:
            assert e.wrong == (int, int)
            assert e.right == (int, float, int)
        else:
            self.fail("Passed incorrectly")
            
    def test_equality(self):
        from typecheck import Tuple
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Tuple(str, int), Tuple(str, int)),
            (Tuple(str, A), Tuple(str, A)),
            (Tuple(), Tuple()),
            (Tuple(str, Tuple(str, int)), Tuple(str, Tuple(str, int))) ]
            
        ne_tests = [
            (Tuple(str, int), Tuple(int, str)),
            (Tuple(str, int), (str, int)),
            (Tuple(A, A), Tuple(A, B)),
            (Tuple(str, int, float), Tuple()),
            (Tuple(str, Tuple(str, int)), Tuple(str, Tuple(int, str))) ]
        
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import Tuple
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Tuple(str, int), Tuple(str, int)),
            (Tuple(str, A), Tuple(str, A)),
            (Tuple(), Tuple()),
            (Tuple(str, Tuple(str, int)), Tuple(str, Tuple(str, int))) ]
            
        ne_tests = [
            (Tuple(str, int), Tuple(int, str)),
            (Tuple(A, A), Tuple(A, B)),
            (Tuple(str, int, float), Tuple()),
            (Tuple(str, Tuple(str, int)), Tuple(str, Tuple(int, str))) ]
        
        test_hash(eq_tests, ne_tests)
        
    def test_empty_tuple_success(self):
        from typecheck import Tuple
    
        check_type(Tuple(), tuple())
    
    def test_empty_tuple_failure(self):
        from typecheck import Tuple, _TC_TypeError
        
        try:
            check_type(Tuple(), (5, 6))
        except _TC_TypeError, e:
            assert e.wrong == (int, int)
            assert e.right == ()
        else:
            self.fail("Passed incorrectly")
    
class SingleType_ListTests(TestCase):
    def setUp(self):
        from typecheck import List
    
        def lis(obj):
            check_type(List(int), obj)
    
        self.list = lis

    def test_success(self):
        self.list([])
        self.list([ 4, 5, 6, 7 ])

    def test_index_failure(self):
        from typecheck import _TC_IndexError, _TC_TypeError
    
        try:
            self.list( [4,5,6,7.0] )
        except _TC_IndexError, e:
            assert e.index == 3
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == int
            assert e.inner.wrong == float
        else:
            self.fail("Passed incorrectly")
            
    def test_type_failure(self):
        from typecheck import _TC_TypeError
        
        try:
            self.list( { 'f': 4 } )
        except _TC_TypeError, e:
            assert e.right == [int]
            assert e.wrong == {str: int}
        else:
            self.fail("Passed incorrectly")
            
    def test_equality(self):
        from typecheck import List
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (List(str), List(str)),
            (List(A), List(A)),
            (List(), List()),
            (List(List(int)), List(List(int))) ]
            
        ne_tests = [
            (List(str), List(int)),
            (List(A), List(B)),
            (List(), List(int)),
            (List(List(int)), List(List(List(int)))),
            (List(int), List(int, int)),
            (List(int), [int]) ]
        
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import List
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (List(str), List(str)),
            (List(A), List(A)),
            (List(), List()),
            (List(List(int)), List(List(int))) ]
            
        ne_tests = [
            (List(str), List(int)),
            (List(A), List(B)),
            (List(), List(int)),
            (List(List(int)), List(List(List(int)))),
            (List(int), List(int, int)) ]
        
        test_hash(eq_tests, ne_tests)
            
class Pattern_ListTests(TestCase):
    def setUp(self):
        from typecheck import List
    
        def lis(obj):
            check_type(List(int, float), obj)

        self.list = lis

    def test_success(self):
        self.list([])
        self.list([ 4, 5.0 ])
        self.list([ 4, 5.0, 8, 9.0 ])
        self.list([ 4, 5.0, 9, 8.0, 4, 5.0 ])

    def test_index_failure(self):
        from typecheck import _TC_IndexError, _TC_TypeError
    
        try:
            # 5 is not a float
            self.list( [4,5,6,7.0] )
        except _TC_IndexError, e:
            assert e.index == 1
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.wrong == int
            assert e.inner.right == float
        else:
            self.fail("Passed incorrectly")
            
    def test_type_failure(self):
        from typecheck import _TC_TypeError
        
        try:
            self.list( { 'f': 4 } )
        except _TC_TypeError, e:
            assert e.right == [int, float]
            assert e.wrong == {str: int}
        else:
            self.fail("Passed incorrectly")
            
    def test_length_failure(self):
        from typecheck import _TC_LengthError
    
        try:
            self.list( [4,5.0,6,7.0, 6] )
        except _TC_LengthError, e:
            assert e.wrong == 5
        else:
            self.fail("Passed incorrectly")
            
    def test_equality(self):
        from typecheck import List
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (List(str, str), List(str, str)),
            (List(A, B), List(A, B)),
            (List(List(int, int), int), List(List(int, int), int)) ]
            
        ne_tests = [
            (List(str, int), List(int, str)),
            (List(A, B), List(B, B)),
            (List(A, B), List(A, A)),
            (List(), List(int, int)),
            (List(List(int, int)), List(List(List(int, int)))),
            (List(int, int), List(int, int, int)),
            (List(int, int), [int, int]) ]
        
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        from typecheck import List
        
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (List(str, str), List(str, str)),
            (List(A, B), List(A, B)),
            (List(List(int, int), int), List(List(int, int), int)) ]
            
        ne_tests = [
            (List(str, int), List(int, str)),
            (List(A, B), List(B, B)),
            (List(A, B), List(A, A)),
            (List(), List(int, int)),
            (List(List(int, int)), List(List(List(int, int)))),
            (List(int, int), List(int, int, int)) ]
        
        test_hash(eq_tests, ne_tests)
            
class NestedTests(TestCase):
    def test_patterned_lists_in_lists(self):
        from typecheck import _TC_IndexError, List, _TC_TypeError
    
        def list1(obj):
            check_type(List( [int, str] ), obj)
        
        # This should pass (list of lists)
        list1( [[4,"foo"], [6,"foo",7,"bar"]] )
        
        try:
            # 6 is not list of alternating integers and strings
            list1( [[4,"foo"], 6] )
        except _TC_IndexError, e:
            assert e.index == 1
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == [int, str]
            assert e.inner.wrong == int
        else:
            self.fail("Passed incorrectly")

    def test_patterned_lists_of_patterned_lists(self):
        from typecheck import _TC_IndexError, List, Or, _TC_TypeError
        
        # [[[i, s]]] (list of lists of lists of alternating ints and strs)
        def list2(obj):
            check_type(List( [[int, str]] ), obj)
        
        list2( [ [[4,"foo"], [5,"bar"]], [[4,"baz",7,"foo"]] ] )
        
        try:
            # The error is in [4,[6]]; the [6] isn't a string
            list2( [[[6,"a"], [7,"r",8,"q"], [4,[6]], [6,"aaa"]]] )
        except _TC_IndexError, e:
            assert e.index == 0
            assert isinstance(e.inner, _TC_IndexError)
            assert e.inner.index == 2
            assert isinstance(e.inner.inner, _TC_IndexError)
            assert e.inner.inner.index == 1
            assert isinstance(e.inner.inner.inner, _TC_TypeError)
            assert e.inner.inner.inner.right == str
            assert e.inner.inner.inner.wrong == [int]
        else:
            self.fail("Passed incorrectly")

    def test_nested_monotype_lists(self):
        from typecheck import _TC_IndexError, List, _TC_TypeError
    
        def list1(obj):
            check_type(List( [int] ), obj)
        
        # This should pass (list of lists)
        list1( [[4,5], [6,7,8]] )
        try:
            # This should raise an exception
            list1( [[4,5], 6] )
        except _TC_IndexError, e:
            assert e.index == 1
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.wrong == int
            assert e.inner.right == [int]
        else:
            self.fail("Passed incorrectly")
            
    def test_doubly_nested_monotype_lists(self):
        from typecheck import _TC_IndexError, List, Or
        from typecheck import _TC_TypeError
        
        # [[[i]]] (list of lists of lists of integers)
        def list2(obj):
            check_type(List( [[int]] ), obj)
        
        list2( [[[4,5], [5,6]], [[4]]] )
        try:
            # The error is in [4,[6]]; the [6] isn't an integer
            list2( [[[6], [7], [4,[6]], [6]]] )
        except _TC_IndexError, e:
            assert e.index == 0
            assert isinstance(e.inner, _TC_IndexError)
            assert e.inner.index == 2
            assert isinstance(e.inner.inner, _TC_IndexError)
            assert e.inner.inner.index == 1
            assert isinstance(e.inner.inner.inner, _TC_TypeError)
            assert e.inner.inner.inner.right == int
            assert e.inner.inner.inner.wrong == [int]
        else:
            self.fail("Passed incorrectly")
            
    def test_lists_of_tuples(self):
        from typecheck import _TC_IndexError, List, _TC_TypeError
        
        # lists of 2-tuples of integer x float
        def list3(obj):
            check_type(List( (int, float) ), obj)
        
        list3( [(1, 2.0), (2, 3.0), (3, 4.0)] )
        try:
            # The types are flipped
            list3( [(2.0, 1), (3.0, 4)] )
        except _TC_IndexError, e:
            assert e.index == 0
            assert isinstance(e.inner, _TC_IndexError)
            assert e.index == 0
            assert isinstance(e.inner.inner, _TC_TypeError)
            assert e.inner.inner.right == int
            assert e.inner.inner.wrong == float
        else:
            self.fail("Passed incorrectly")
            
    def test_singly_nested_tuples(self):
        from typecheck import _TC_IndexError, Tuple, _TC_TypeError
    
        def tup1(obj):
            check_type(Tuple( (int, int), int ), obj)
        
        # This should pass
        tup1( ((4,5), 6) )
        
        try:
            # This should raise an exception
            tup1( ([4,5], 6) )
        except _TC_IndexError, e:
            assert e.index == 0
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == (int, int)
            assert e.inner.wrong == [int]
        else:
            self.fail("Passed incorrectly")
            
    def test_doubly_nested_tuples(self):
        from typecheck import _TC_IndexError, Tuple, _TC_TypeError
        
        # (((i, i), i), i)
        # Triply-nested 2-tuples of integers
        tup1 = Tuple( (int, int), int )
        def tup2(obj):
            check_type(Tuple(tup1, int), obj)
        
        tup2( (((4, 5), 6), 7) )
        
        try:
            # [4,5] is not a 2-tuple of int x int
            tup2( (([4,5], 6), 7) )
        except _TC_IndexError, e:
            assert e.index == 0
            assert isinstance(e.inner, _TC_IndexError)
            assert e.inner.index == 0
            assert isinstance(e.inner.inner, _TC_TypeError)
            assert e.inner.inner.right == (int, int)
            assert e.inner.inner.wrong == [int]
        else:
            self.fail("Passed incorrectly")
            
    def test_tuples_of_lists(self):
        from typecheck import _TC_IndexError, Tuple, _TC_TypeError
        
        # 2-tuples of list of integers x list of strs
        def tup3(obj):
            check_type(Tuple( [int], [str] ), obj)
        
        # Should pass
        tup3( ([4,5,6], ["a","b","c"]) )
        
        try:
            tup3( (["a","b","c"], [4,5,6]) )
        except _TC_IndexError, e:
            assert e.index == 0
            assert isinstance(e.inner, _TC_IndexError)
            assert e.index == 0
            assert isinstance(e.inner.inner, _TC_TypeError)
            assert e.inner.inner.right == int
            assert e.inner.inner.wrong == str
        else:
            self.fail("Passed incorrectly")
            
    def test_nested_dict_as_val(self):
        from typecheck import _TC_KeyError, _TC_KeyValError, Dict, _TC_TypeError
    
        # int -> {int -> float}
        def dict1(obj):
            check_type(Dict( int, {int: float}), obj)
        
        # Should pass
        dict1( {6: {6: 7.0, 8: 9.0}} )
        
        try:
            # Should fail (7.0 is not an integer)
            dict1( {6: {7.0: 8.0}} )
        except _TC_KeyValError, e:
            assert e.key == 6
            assert e.val == {7.0: 8.0}
            assert isinstance(e.inner, _TC_KeyError)
            assert e.inner.key == 7.0
            assert isinstance(e.inner.inner, _TC_TypeError)
            assert e.inner.inner.right == int
            assert e.inner.inner.wrong == float
        else:
            self.fail("Passed incorrectly")

    def test_nested_tuple_as_key(self):
        from typecheck import _TC_KeyError, _TC_IndexError, Dict
        from typecheck import _TC_TypeError
        
        # (int, int) -> float
        def dict2(obj):
            check_type(Dict( (int, int), float ), obj)
        
        dict2( {(4,5): 5.0, (9,9): 9.0} )
        
        try:
            # Should fail; 5.0 in (5.0, 5) is not an integer
            dict2( {(5.0, 5): 5.0} )
        except _TC_KeyError, e:
            assert e.key == (5.0, 5)
            assert isinstance(e.inner, _TC_IndexError)
            assert e.inner.index == 0
            assert isinstance(e.inner.inner, _TC_TypeError)
            assert e.inner.inner.right == int
            assert e.inner.inner.wrong == float
        else:
            self.fail("Passed incorrectly")
            
class ExtensibleSigTests(TestCase):
    def setUp(self):
        from typecheck import register_type, _TC_TypeError, unregister_type
        import types

        class ExactValue(object):
            def __init__(self, value):
                self.type = value
        
            def __typecheck__(self, func, to_check):
                if to_check != self.type:
                    raise _TC_TypeError(to_check, self.type)
                
            @classmethod
            def __typesig__(cls, obj):
                # Note that you can either include this test
                # or your classes (like ExactValue) can inherit
                # from CheckType; either works, but you have
                # to do one or the other.
                if isinstance(obj, cls):
                    return obj
                if isinstance(obj, int):
                    return cls(obj)
        
        self.ExactValue = ExactValue
        register_type(ExactValue)
        
    def tearDown(self):
        from typecheck import unregister_type, is_registered_type
    
        if is_registered_type(self.ExactValue):
            unregister_type(self.ExactValue)

    def test_register(self):
        from typecheck import typecheck_args, TypeCheckError, _TC_IndexError, _TC_TypeError

        @typecheck_args(5, 6)
        def foo(a, b):
            return a, b

        assert foo(5, 6) == (5, 6)

        try:
            foo('a', 5)
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_TypeError)
            assert e.internal.wrong == str
            assert e.internal.right == 5
        else:
            raise AssertionError("Succeeded incorrectly")
    
    def test_double_register(self):
        from typecheck import register_type
        
        register_type(self.ExactValue)
        
    def test_unregister_def(self):
        from typecheck import register_type, typecheck_args
        from typecheck import unregister_type

        @typecheck_args(5, 6)
        def foo(a, b):
            return a, b

        assert foo(5, 6) == (5, 6)

        unregister_type(self.ExactValue)

        try:
            @typecheck_args(5, 6)
            def foo(a, b):
                return a, b
        except AssertionError:
            pass
        else:
            raise AssertionError("Succeeded incorrectly")
            
    def test_unregister_call_again(self):
        from typecheck import typecheck_args, unregister_type, TypeCheckError, _TC_IndexError
        from typecheck import _TC_TypeError
        
        @typecheck_args(5, 6)
        def foo(a, b):
            return a, b
            
        assert foo(5, 6) == (5, 6)
        
        unregister_type(self.ExactValue)
        
        try:
            foo('a', 5)
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_TypeError)
            assert e.internal.wrong == str
            assert e.internal.right == 5
        else:
            raise AssertionError("Succeeded incorrectly")

class Test_Function(TestCase):
    def test_works_with_Type_function(self):
        from typecheck import Type, Function
        
        def foo(*vargs):
            return vargs
        
        assert isinstance(Type(foo), Function)
    
    def test_works_with_Type_call_method_newstyle(self):
        from typecheck import Type, Function
        
        class Foo(object):
            def __call__(self, *vargs):
                return vargs
        
        assert isinstance(Type(Foo()), Function)
    
    def test_works_with_Type_call_method_classic(self):
        from typecheck import Type, Function
        
        class Foo:
            def __call__(self, *vargs):
                return vargs
        
        assert isinstance(Type(Foo()), Function)
        
    def test_works_with_Type_classmethod_newstyle(self):
        from typecheck import Type, Function
        
        class Foo(object):
            @classmethod
            def foo(*vargs):
                return vargs
        
        assert isinstance(Type(Foo.foo), Function)
        
    def test_works_with_Type_classmethod_classic(self):
        from typecheck import Type, Function
        
        class Foo:
            @classmethod
            def foo(*vargs):
                return vargs
        
        assert isinstance(Type(Foo.foo), Function)
        
    def test_works_with_Type_instancemethod_newstyle(self):
        from typecheck import Type, Function
        
        class Foo(object):
            def foo(*vargs):
                return vargs
        
        assert isinstance(Type(Foo().foo), Function)
        
    def test_works_with_Type_instancemethod_classic(self):
        from typecheck import Type, Function
        
        class Foo:
            def foo(*vargs):
                return vargs
        
        assert isinstance(Type(Foo().foo), Function)
        
    def test_works_with_Type_staticmethod_newstyle(self):
        from typecheck import Type, Function
        
        class Foo(object):
            @staticmethod
            def foo(*vargs):
                return vargs
        
        assert isinstance(Type(Foo.foo), Function)
        
    def test_works_with_Type_staticmethod_classic(self):
        from typecheck import Type, Function
        
        class Foo:
            @staticmethod
            def foo(*vargs):
                return vargs
        
        assert isinstance(Type(Foo.foo), Function)
        
    def test_str(self):
        from typecheck import Function
        
        def foo(*vargs):
            return vargs
        
        assert str(Function(foo)) == "Function(%s)" % foo
        
    def test_repr(self):
        from typecheck import Function
        
        def foo(*vargs):
            return vargs
        
        assert repr(Function(foo)) == "Function(%s)" % foo
        
    def test_check_type_errors_pass_through(self):
        from typecheck import Function, check_type
        
        class MyCustomException(Exception):
            pass
            
        def checker_function(*vargs):
            raise MyCustomException(*vargs)
            
        try:
            check_type(Function(checker_function), None, 66)
        except MyCustomException, e:
            assert e.args == (66,)
        else:
            raise AssertionError("Failed to raise MyCustomException")
            
    def test_check_type_None_means_success(self):
        from typecheck import Function, check_type
        
        def checker_function(*vargs):
            return None
            
        check_type(Function(checker_function), None, 66)
        
    def test_check_type_true_values_mean_success(self):
        from typecheck import Function, check_type
        
        def checker_function(*vargs):
            return True
        check_type(Function(checker_function), None, 66)
        

        def checker_function(*vargs):
            return 5
        check_type(Function(checker_function), None, 66)
        
        
        def checker_function(*vargs):
            return "abc"
        check_type(Function(checker_function), None, 66)
        
    def test_check_type_false_values_mean_success(self):
        from typecheck import Function, check_type
        
        def checker_function(*vargs):
            return []
        check_type(Function(checker_function), None, 66)
        
        
        def checker_function(*vargs):
            return {}
        check_type(Function(checker_function), None, 66)
        
    def test_check_type_False_means_failure(self):
        from typecheck import Function, check_type, _TC_FunctionError
        
        def checker_function(*vargs):
            return False
        try:
            check_type(Function(checker_function), None, 66)
        except _TC_FunctionError, e:
            assert e.checking_func is checker_function
            assert e.rejected_obj == 66
        else:
            raise AssertionError("Failed to raise _TC_FunctionError")
        
        
        # (0 == False) == True
        def checker_function(*vargs):
            return 0
        try:
            check_type(Function(checker_function), None, 66)
        except _TC_FunctionError, e:
            assert e.checking_func is checker_function
            assert e.rejected_obj == 66
        else:
            raise AssertionError("Failed to raise _TC_FunctionError")

def convert_mapping(mapping):
    if mapping is None:
        return None
    # k[0] is necessary because k looks like ("string", string_type)
    return dict([(k[0], v.type) for k, v in mapping.items()])

def active_mapping():
    from typecheck import TypeVariables as TV
    return convert_mapping(TV._TypeVariables__active_mapping)
        
class Test_TypeVariables(TestCase):
    def tearDown(self):
        from typecheck import TypeVariables
        
        # Give ourselves a clean slate
        TypeVariables._TypeVariables__gen_mappings = {}
        TypeVariables._TypeVariables__mapping_stack = []
        TypeVariables._TypeVariables__active_mapping = None

    def test_equality(self):
        from typecheck import TypeVariables
        
        assert TypeVariables('a') != TypeVariables('b')
        assert TypeVariables('a') == TypeVariables('a')
        assert TypeVariables('a') != TypeVariables(u'a')
        
    def test_hash(self):
        from typecheck import TypeVariables
        
        assert hash(TypeVariables('a')) != hash(TypeVariables('b'))
        assert hash(TypeVariables('a')) == hash(TypeVariables('a'))
        assert hash(TypeVariables('a')) != hash(TypeVariables(u'a'))

    def test_args_and_return_pass(self):
        from typecheck import accepts, returns
        from typecheck import TypeVariables

        def run_test(dec):
            @dec('a', int, 'a')
            def foo(a, b, c):
                return a, b, c

            class A: pass
            a = A()
            for args in ((5, 5, 5), (5.0, 5, 7.0), ([4, 5], 5, [8, 9, 10]), (a, 5, a)):
                assert foo(*args) == args
                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping is None
                assert len(TypeVariables._TypeVariables__gen_mappings) == 0

        run_test(accepts)
        run_test(returns)

    def test_args_fail(self):
        from typecheck import accepts, calculate_type
        from typecheck import TypeCheckError, _TC_TypeError
        from typecheck import TypeVariables

        class Bad: pass
        bad = Bad()

        @accepts('a', int, 'a')
        def foo(a, b, c):
            return a, b, c

        class A: pass
        a = A()

        for args in ((5, 5, bad), (5.0, 5, bad), ([4, 5], 5, bad), (a, 5, bad)):
            try:
                foo(*args)
            except TypeCheckError, e:
                assert isinstance(e.internal, _TC_TypeError)
                assert e.internal.right == calculate_type(args[0])
                assert e.internal.wrong == Bad

                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping is None
                assert len(TypeVariables._TypeVariables__gen_mappings) == 0
            else:
                raise AssertionError("Failed to raise TypeCheckError at the proper place")

    def test_return_fail(self):
        from typecheck import returns, calculate_type
        from typecheck import TypeCheckError, _TC_IndexError, _TC_TypeError
        from typecheck import TypeVariables

        class Bad: pass
        bad = Bad()

        @returns('a', int, 'a')
        def foo(a, b, c):
            return a, b, c

        class A: pass
        a = A()

        for args in ((5, 5, bad), (5.0, 5, bad), ([4, 5], 5, bad), (a, 5, bad)):
            try:
                foo(*args)
            except TypeCheckError, e:
                assert isinstance(e.internal, _TC_IndexError)
                assert e.internal.index == 2
                assert isinstance(e.internal.inner, _TC_TypeError)
                assert e.internal.inner.right == calculate_type(args[0])
                assert e.internal.inner.wrong == Bad

                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping is None
                assert len(TypeVariables._TypeVariables__gen_mappings) == 0
            else:
                raise AssertionError("Failed to raise TypeCheckError at the proper place")

    def test_yield_pass(self):
        from typecheck import yields
        from typecheck import TypeVariables

        @yields('a', int, 'a')
        def foo(a, b, c):
            yield a, b, c

        class A: pass
        a = A()
        for args in ((5, 5, 5), (5.0, 5, 7.0), ([4, 5], 5, [8, 9, 10]), (a, 5, a)):
            g = foo(*args)
            assert g.next() == args
            try:
                g.next()
            except StopIteration:
                pass
            else:
                raise AssertionError("Failed to raise StopIteration at the right place")

        assert TypeVariables._TypeVariables__mapping_stack == []
        assert TypeVariables._TypeVariables__active_mapping is None
        assert len(TypeVariables._TypeVariables__gen_mappings) == 0

    def test_yield_fail(self):
        from typecheck import yields
        from typecheck import TypeCheckError, _TC_IndexError, _TC_TypeError
        from typecheck import calculate_type, _TC_GeneratorError
        from typecheck import TypeVariables

        gen_mappings = TypeVariables._TypeVariables__gen_mappings

        class Bad: pass
        bad = Bad()

        @yields('a', int, 'a')
        def foo(a, b, c):
            yield a, b, bad

        class A: pass
        a = A()
        for args in ((5, 5, 5), (5.0, 5, 7.0), ([4, 5], 5, [8, 9, 10]), (a, 5, a)):
            g = foo(*args)

            try:
                assert g.next() == args
            except TypeCheckError, e:
                assert isinstance(e.internal, _TC_GeneratorError)
                assert e.internal.yield_no == 1
                assert isinstance(e.internal.inner, _TC_IndexError)
                assert e.internal.inner.index == 2
                assert isinstance(e.internal.inner.inner, _TC_TypeError)
                assert e.internal.inner.inner.right == calculate_type(args[0])
                assert e.internal.inner.inner.wrong == Bad

                assert len(gen_mappings) == 1
                assert convert_mapping(gen_mappings.values()[0]) == {'a': calculate_type(args[0])}
            else:
                raise AssertionError("Failed to raise TypeCheckError at the right place")

            try:
                g.next()
            except StopIteration:
                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping is None
                assert len(gen_mappings) == 0
            else:
                raise AssertionError("Failed to raise StopIteration at the right place")

        assert TypeVariables._TypeVariables__mapping_stack == []
        assert TypeVariables._TypeVariables__active_mapping is None
        assert len(gen_mappings) == 0

    def test_args_return_pass(self):
        from typecheck import returns, accepts
        from typecheck import TypeVariables

        def run_test(dec_1, dec_2):
            @dec_1('a', 'b', int, 'a', 'b')
            @dec_2('a', 'b', int, 'a', 'b')
            def foo(a, b, c, d, e):
                return a, b, c, d, e

            class A: pass
            class B: pass
            a = A()
            b = B()
            for args in ((5, 5.0, 6, 7, 7.0), ('a', 4, 6, 'b', 6), (a, b, 5, a, b)):
                assert foo(*args) == args
                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping is None
                assert len(TypeVariables._TypeVariables__gen_mappings) == 0

        run_test(returns, accepts)
        run_test(accepts, returns)

    def test_args_return_fail(self):
        from typecheck import accepts, returns, calculate_type
        from typecheck import TypeCheckError, _TC_IndexError, _TC_TypeError
        from typecheck import TypeVariables

        class Bad: pass
        bad = Bad()

        def run_test(dec_1, dec_2):
            @dec_1
            @dec_2
            def foo(a, b, c, d, e):
                return a, b, c, bad, e

            class A: pass
            class B: pass
            a = A()
            b = B()
            for args in ((5, 5.0, 6, 7, 7.0), ('a', 4, 6, 'b', 6), (a, b, 5, a, b)):
                try:
                    foo(*args)
                except TypeCheckError, e:
                    assert isinstance(e.internal, _TC_IndexError)
                    assert e.internal.index == 3
                    assert isinstance(e.internal.inner, _TC_TypeError)
                    assert e.internal.inner.right == calculate_type(args[0])
                    assert e.internal.inner.wrong == Bad

                    assert TypeVariables._TypeVariables__mapping_stack == []
                    assert TypeVariables._TypeVariables__active_mapping is None
                    assert len(TypeVariables._TypeVariables__gen_mappings) == 0
                else:
                    raise AssertionError("Failed to raise TypeCheckError at the proper place")

        t_r = returns('a', 'b', int, 'a', 'b')
        t_a = accepts('a', 'b', int, 'a', 'b')

        run_test(t_r, t_a)
        run_test(t_a, t_r)

    def test_args_yield_pass(self):
        from typecheck import yields, accepts
        from typecheck import TypeVariables

        gen_mappings = TypeVariables._TypeVariables__gen_mappings

        def run_test(dec_1, dec_2):
            @dec_1('a', 'b', int, 'a', 'b')
            @dec_2('a', 'b', int, 'a', 'b')
            def foo(a, b, c, d, e):
                yield a, b, c, d, e

            class A: pass
            class B: pass
            a = A()
            b = B()

            problem_set = [0]*3
            problem_set[0] = ((5, 5.0, 6, 7, 7.0), {'a': int, 'b': float})
            problem_set[1] = (('a', 4, 6, 'b', 6), {'a': str, 'b': int})
            problem_set[2] = ((a, b, 5, a, b), {'a': A, 'b': B})

            for args, mapping in problem_set:
                gen = foo(*args)
                assert gen.next() == args
                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping == None
                assert len(gen_mappings) == 1
                assert convert_mapping(gen_mappings.values()[0]) == mapping
                try:
                    gen.next()
                except StopIteration:
                    pass
                else:
                    raise AssertionError("Failed to raise StopIteration at the right time")
                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping is None
                assert len(gen_mappings) == 0

        run_test(yields, accepts)
        run_test(accepts, yields)

        assert TypeVariables._TypeVariables__mapping_stack == []
        assert TypeVariables._TypeVariables__active_mapping is None
        assert len(TypeVariables._TypeVariables__gen_mappings) == 0

    def test_args_yield_fail(self):
        from typecheck import yields, accepts
        from typecheck import TypeCheckError, _TC_IndexError, _TC_TypeError
        from typecheck import calculate_type, _TC_GeneratorError
        from typecheck import TypeVariables

        gen_mappings = TypeVariables._TypeVariables__gen_mappings

        class Bad: pass
        bad = Bad()

        def run_test(dec_1, dec_2):
            @dec_1('a', 'b', int, 'a', 'b')
            @dec_2('a', 'b', int, 'a', 'b')
            def foo(a, b, c, d, e):
                yield bad, b, c, bad, e

            class A: pass
            class B: pass
            a = A()
            b = B()

            problem_set = [0]*3
            problem_set[0] = ((5, 5.0, 6, 7, 7.0), {'a': int, 'b': float})
            problem_set[1] = (('a', 4, 6, 'b', 6), {'a': str, 'b': int})
            problem_set[2] = ((a, b, 5, a, b), {'a': A, 'b': B})

            for args, mapping in problem_set:
                gen = foo(*args)

                try:
                    assert gen.next() == args
                except TypeCheckError, e:
                    assert isinstance(e.internal, _TC_GeneratorError)
                    assert e.internal.yield_no == 1
                    assert isinstance(e.internal.inner, _TC_IndexError)
                    assert e.internal.inner.index == 0
                    assert isinstance(e.internal.inner.inner, _TC_TypeError)
                    assert e.internal.inner.inner.wrong == Bad
                    assert e.internal.inner.inner.right == calculate_type(args[0])

                    assert TypeVariables._TypeVariables__mapping_stack == []
                    assert TypeVariables._TypeVariables__active_mapping == None
                    assert len(gen_mappings) == 1
                    assert convert_mapping(gen_mappings.values()[0]) == mapping
                try:
                    gen.next()
                except StopIteration:
                    assert TypeVariables._TypeVariables__mapping_stack == []
                    assert TypeVariables._TypeVariables__active_mapping is None
                    assert len(gen_mappings) == 0
                else:
                    raise AssertionError("Failed to raise StopIteration at the right time")


        run_test(yields, accepts)
        run_test(accepts, yields)

        assert TypeVariables._TypeVariables__mapping_stack == []
        assert TypeVariables._TypeVariables__active_mapping is None
        assert len(TypeVariables._TypeVariables__gen_mappings) == 0

    def test_recursive_functions(self):
        from typecheck import returns, accepts
        from typecheck import TypeVariables

        mapping_stack = TypeVariables._TypeVariables__mapping_stack

        mappings = [None, {'a': str}, {'a': (int, int)}, {'a': float}, None]
        stack = list(mappings)
        stack.reverse()
        stack.pop()

        def check(n):
            assert active_mapping() == mappings[n]
            assert [convert_mapping(m) for m in mapping_stack] == stack[:-n]

        def run_test(dec_1, dec_2):
            @dec_1
            @dec_2
            def foo(obj_1, obj_2, n):
                if n == 1:
                    check(n)
                    return [obj_1, obj_2]
                elif n == 2:
                    check(n)
                    foo('jabber', 'wocky', n-1)
                    check(n)

                    return [(4, 5), (6, 7)]
                elif n == 3:
                    check(n)
                    foo((5, 6), (7, 8), n-1)
                    check(n)

                    return [obj_1, obj_2]

            assert foo(6.0, 7.0, 3) == [6.0, 7.0]
            assert mapping_stack == []
            assert TypeVariables._TypeVariables__active_mapping == None
            assert len(TypeVariables._TypeVariables__gen_mappings) == 0

        t_r = returns(['a'])
        t_a = accepts('a', 'a', int)
        run_test(t_r, t_a)
        run_test(t_a, t_r)

    def test_incorrect_generator_usage(self):
        from typecheck import yields, accepts
        from typecheck import TypeVariables

        gen_mappings = TypeVariables._TypeVariables__gen_mappings

        @accepts('a')
        @yields('a')
        def gen(obj):
            yield obj

        assert gen.type_yield == 'a'
        assert gen.type_args == {'obj': 'a'}

        for i in range(1, 4):
            g = gen(5)

            assert gen.type_yield == g.type_yield

            assert g.next() == 5
            del g

            assert TypeVariables._TypeVariables__mapping_stack == []
            assert TypeVariables._TypeVariables__active_mapping == None
            assert len(gen_mappings) == 0

    def test_args_yield_on_method_fail(self):
        from typecheck import yields, TypeCheckError
        from typecheck import _TC_IndexError, _TC_TypeError
        from typecheck import _TC_GeneratorError, accepts
        from typecheck import TypeVariables

        class Test(object):
            @accepts('a', int, int)
            @yields('a', int, 'a')
            def foo(self, a, b):
                yield b, a, b

        assert Test.foo.type_yield == ('a', int, 'a')
        assert Test.foo.type_args == {'self': 'a', 'a': int, 'b': int}

        def run_test():
            try:
                assert Test().foo(4, 6).next() == (6, 4, 6)
            except TypeCheckError, e:
                assert isinstance(e.internal, _TC_GeneratorError)
                assert e.internal.yield_no == 1
                assert isinstance(e.internal.inner, _TC_IndexError)
                assert e.internal.inner.index == 0
                assert isinstance(e.internal.inner.inner, _TC_TypeError)
                assert e.internal.inner.inner.wrong == int
                assert e.internal.inner.inner.right == Test
            else:
                raise AssertionError("Failed to raise TypeCheckError")

        run_test()
        assert TypeVariables._TypeVariables__mapping_stack == []
        assert TypeVariables._TypeVariables__active_mapping == None
        assert len(TypeVariables._TypeVariables__gen_mappings) == 0

    def test_unicode_tvars(self):
        from typecheck import accepts, calculate_type
        from typecheck import TypeCheckError, _TC_TypeError
        from typecheck import TypeVariables

        class Bad: pass
        bad = Bad()

        @accepts(u'a', int, u'a')
        def foo(a, b, c):
            return a, b, c

        class A: pass
        a = A()

        for args in ((5, 5, bad), (5.0, 5, bad), ([4, 5], 5, bad), (a, 5, bad)):
            try:
                foo(*args)
            except TypeCheckError, e:
                assert isinstance(e.internal, _TC_TypeError)
                assert e.internal.right == calculate_type(args[0])
                assert e.internal.wrong == Bad

                assert TypeVariables._TypeVariables__mapping_stack == []
                assert TypeVariables._TypeVariables__active_mapping is None
                assert len(TypeVariables._TypeVariables__gen_mappings) == 0
            else:
                raise AssertionError("Failed to raise TypeCheckError at the proper place")

    def test_unicode_and_ascii_tvars_1(self):
        from typecheck import accepts, returns
        
        @accepts(u'a', 'a')
        @returns('a', u'a')
        def flip(a, b):
            return b, a
            
        flip(5, 7.0)
    
    def test_unicode_and_ascii_tvars_2(self):
        from typecheck import accepts, returns, TypeCheckError
        from typecheck import _TC_IndexError, _TC_TypeError, TypeVariables
    
        # The signature is wrong (for the function, not the test)
        @accepts(u'a', 'a')
        @returns('a', u'a')
        def foo(a, b):
            return a, b
            
        try:
            foo(4, 5.0)
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_IndexError)
            assert e.internal.index == 0
            
            assert isinstance(e.internal.inner, _TC_TypeError)
            assert e.internal.inner.right is float
            assert e.internal.inner.wrong is int
            
            assert TypeVariables._TypeVariables__mapping_stack == []
            assert TypeVariables._TypeVariables__active_mapping is None
            assert len(TypeVariables._TypeVariables__gen_mappings) == 0
        else:
            raise AssertionError('Failed to raise TypeCheckError')

    def test_same_tvar_nested_calls(self):
        from typecheck import accepts, returns
        from typecheck import TypeVariables

        Foo = TypeVariables("this is the foo tvar")

        @accepts(Foo)
        @returns(Foo)
        def bar(a):
            return int(baz(float(a)))

        @accepts(Foo)
        @returns(Foo)
        def baz(a):
            return a

        assert bar(4) == float(4)
            
### Bookkeeping ###
if __name__ == '__main__':
    import __main__
    support.run_all_tests(__main__)
