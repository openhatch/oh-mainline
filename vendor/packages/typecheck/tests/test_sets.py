import support
from support import TODO, TestCase, test_equality, test_hash

if __name__ == '__main__':
    support.adjust_path()
### /Bookkeeping ###

import typecheck

import typecheck.sets
from typecheck.sets import Set

def check_type(typ, obj):
    typecheck.check_type(typ, None, obj)

class SetTests(TestCase):
    def test_empty_list(self):
        Set([])
    
    def test_success_basic(self):
        check_type(Set([int]), set([4, 5, 6, 4, 5, 6]))

    def test_success_mutlitypes(self):
        check_type(Set([int, float]), set([4, 5.0, 6, 4, 5, 6.0]))
        
    def test_success_nested(self):
        from typecheck import Or
        
        check_type(Set([(int, int)]), set([(4, 5), (6, 7)]))
        
        check_type(Set([Or(int, float)]), set([4, 4.0, 5, 5.0]))
        
    def test_success_empty(self):
        check_type(Set([]), set())
        
    def test_failure_empty(self):
        from typecheck import _TC_LengthError
        
        try:
            check_type(Set([]), set([4, 5, 6]))
        except _TC_LengthError, e:
            assert e.right == 0
            assert e.wrong == 3
        else:
            raise AssertionError("Failed to raise _TC_LengthError")
        
    def test_failure(self):
        from typecheck import _TC_KeyError, _TC_TypeError
        
        try:
            check_type(Set([int]), set([4, 5, 6.0]))
        except _TC_KeyError, e:
            assert e.key == 6.0
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == int
            assert e.inner.wrong == float
        else:
            raise AssertionError("Did not raise the proper exception")

    def test_failure_multitypes(self):
        from typecheck import Or, _TC_KeyError, _TC_TypeError
        
        try:
            check_type(Set([int, float]), set([4, 5, 6.0, 's']))
        except _TC_KeyError, e:
            assert e.key == 's'
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == Or(int, float)
            assert e.inner.wrong == str
        else:
            raise AssertionError("Did not raise the proper exception")
            
    def test_failure_nested(self):
        from typecheck import _TC_KeyError, _TC_IndexError, _TC_TypeError

        try:
            check_type(Set([(int, int)]), set([(4, 5), (4, 6.0)]))
        except _TC_KeyError, e:
            assert e.key == (4, 6.0)
            assert isinstance(e.inner, _TC_TypeError)
            assert e.inner.right == (int, int)
            assert e.inner.wrong == (int, float)
        else:
            raise AssertionError("Did not raise the proper exception")
        
    def test_equality(self):
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Set([str]), Set([str])),
            (Set([A, B]), Set([A, B])),
            (Set([]), Set([])),
            (Set([int, int, str]), Set([int, str])),
            (Set([int, str]), Set([str, int])),
            (Set([Set([int, float]), int]), Set([Set([float, int]), int])),
            (Set([Set([int, str]), Set([int, str])]), Set([Set([int, str])])) ]
            
        ne_tests = [
            (Set([A, B]), Set([B, B])),
            (Set([A, B]), Set([A, A])),
            (Set([]), Set([int, int])),
            (Set([Set([int, str])]), Set([Set([Set([int, str])])])),
            (Set([int, int]), set([int, int])) ]
        
        test_equality(eq_tests, ne_tests)
        
    def test_hash(self):
        class A(object): pass
        class B(A): pass
        
        eq_tests = [
            (Set([str]), Set([str])),
            (Set([A, B]), Set([A, B])),
            (Set([]), Set([])),
            (Set([int, int, str]), Set([int, str])),
            (Set([int, str]), Set([str, int])),
            (Set([Set([int, float]), int]), Set([Set([float, int]), int])),
            (Set([Set([int, str]), Set([int, str])]), Set([Set([int, str])])) ]
            
        ne_tests = [
            (Set([A, B]), Set([B, B])),
            (Set([A, B]), Set([A, A])),
            (Set([]), Set([int, int])),
            (Set([Set([int, str])]), Set([Set([Set([int, str])])])) ]
        
        test_hash(eq_tests, ne_tests)
        
    def test_Type_uses_it(self):
        from typecheck import Type
        
        t = Type(set([int, float]))
        assert isinstance(t, Set)

### Bookkeeping ###
if __name__ == '__main__':
    import __main__
    support.run_all_tests(__main__)
