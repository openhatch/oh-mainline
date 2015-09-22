import support
from support import TODO, TestCase

if __name__ == '__main__':
    support.adjust_path()
### /Bookkeeping ###

import typecheck
from typecheck import check_type

class TypeCheckedTree(TestCase):
    def setUp(self):
        from typecheck import typecheck_args, register_type
        from typecheck import check_type, _TC_Exception, Type
        from typecheck import _TC_NestedError, _TC_TypeError
        
        class _TC_TreeChildTypeError(_TC_NestedError):
            def __init__(self, child, inner_exception):
                _TC_NestedError.__init__(self, inner_exception)
        
                self.child = child
                
            def error_message(self):
                return ("in the %s child" % self.child) + _TC_NestedError.error_message(self)
        
        class TreeType(object):
            def __init__(self, val):
                self._type = Type(val)
                self.type = self

            def __typecheck__(self, func, to_check):
                if not isinstance(to_check, Tree):
                    raise _TC_TypeError(to_check, self._type)
            
                try:
                    check_type(self._type, func, to_check.val)
                except _TC_Exception, e:
                    raise _TC_TypeError(to_check.val, self._type.type)

                for side in ('right', 'left'):
                    child = getattr(to_check, side)
                    if child is not None:
                        try:
                            check_type(self, func, child)
                        except _TC_Exception, e:
                            raise _TC_TreeChildTypeError(side, e)

            @classmethod    
            def __typesig__(cls, obj):
                if isinstance(obj, cls):
                    return obj
                    
            def __str__(self):
                return "Tree(%s)" % str(self._type)
                
            __repr__ = __str__

        class Tree(object):
            def __init__(self, val, left=None, right=None):
                self.val = val
                self.left = left
                self.right = right
                
            def __str__(self):
                if self.left is None and self.right is None:
                    return "Tree(%s)" % str(self.val)
                return "Tree(%s, %s, %s)" % (str(self.val), str(self.left), str(self.right))
            
            __repr__ = __str__
            
            @classmethod
            def __typesig__(cls, obj):
                if isinstance(obj, cls):
                    if obj.left is None and obj.right is None:
                        return TreeType(obj.val)
            
        register_type(Tree)
        register_type(TreeType)

        @typecheck_args(Tree(int))
        def preorder(tree):
            l = [tree.val]
            if tree.left is not None:
                l.extend(preorder(tree.left))
            if tree.right is not None:
                l.extend(preorder(tree.right))

            return l
                        
        self.Tree = Tree
        self.preorder = preorder
        self._TC_TreeChildTypeError = _TC_TreeChildTypeError

    def test_success(self):
        Tree = self.Tree
        preorder = self.preorder
                        
        preorder(Tree(5, Tree(6), Tree(7)))
    
    def test_failure(self):
        from typecheck import TypeCheckError, _TC_IndexError, _TC_TypeError
    
        Tree = self.Tree
        preorder = self.preorder
        _TC_TreeChildTypeError = self._TC_TreeChildTypeError
        
        try:            
            preorder(Tree(5, Tree(6), Tree(7.0)))
        except TypeCheckError, e:
            assert isinstance(e.internal, _TC_TreeChildTypeError)
            assert e.internal.child == 'right'
            assert isinstance(e.internal.inner, _TC_TypeError)
            assert e.internal.inner.right == int
            assert e.internal.inner.wrong == float
            self.assertEqual(str(e), "Argument tree: for Tree(5, Tree(6), Tree(7.0)), in the right child, expected <type 'int'>, got <type 'float'>")
        else:
            raise AssertionError("Succeeded incorrectly")

# An example of Xor being implemented in terms of the included And, Not
# and Or utility classes            
class Xor(TestCase):
    def setUp(self):
        from typecheck import Or, And, Not
        
        def Xor(cond_1, cond_2):
            return Or(And(cond_1, Not(cond_2)), And(cond_2, Not(cond_1)))
            
        def check_type(typ, to_check):
            typecheck.check_type(typ, None, to_check)
            
        self.Xor = Xor
        self.check_type = check_type
        
    def test_success(self):
        from typecheck import IsCallable
    
        Xor = self.Xor
        check_type = self.check_type
        
        check_type(Xor(dict, IsCallable()), pow)
        check_type(Xor(dict, IsCallable()), {'a': 5})
        
    def test_failure(self):
        from typecheck import IsIterable, _TC_TypeError
    
        Xor = self.Xor
        check_type = self.check_type
        
        for obj in (pow, {'a': 5}):
            try:
                check_type(Xor(dict, IsIterable()), pow)
            except _TC_TypeError:
                pass
            else:
                raise AssertionError("Failed to raise _TC_TypeError")
                
# An example of IsIterable being implemented in terms of HasAttr() and
# IsCallable()
class IsIterable(TestCase):
    def setUp(self):
        from typecheck import HasAttr, IsCallable
        
        def IsIterable():
            return HasAttr({'__iter__': IsCallable()})
            
        def check_type(typ, to_check):
            typecheck.check_type(typ, None, to_check)
        
        self.IsIterable = IsIterable
        self.check_type = check_type
        
    def test_success_builtins(self):
        IsIterable = self.IsIterable
        
        for t in (list, tuple, set, dict):
            self.check_type(IsIterable(), t())
            
    def test_success_generator(self):
        IsIterable = self.IsIterable
        
        def foo():
            yield 5
            yield 6
            
        self.check_type(IsIterable(), foo())
            
    def test_success_user_newstyle(self):
        IsIterable = self.IsIterable
        
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
            self.check_type(IsIterable(), c())
            
    def test_success_user_oldstyle(self):
        IsIterable = self.IsIterable
        
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
            self.check_type(IsIterable(), c())
            
    def test_failure(self):
        from typecheck import _TC_MissingAttrError
        
        IsIterable = self.IsIterable
        
        class A(object):
            def __str__(self):
                return "A()"
            
        try:
            self.check_type(IsIterable(), A())
        except _TC_MissingAttrError, e:
            pass
        else:
            raise AssertionError("Failed to raise _TC_MissingAttrError")


### Bookkeeping ###
if __name__ == '__main__':
    import __main__
    support.run_all_tests(__main__)
