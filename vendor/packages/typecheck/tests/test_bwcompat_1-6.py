import support
from support import TODO, TestCase

if __name__ == '__main__':
    support.adjust_path()
### /Bookkeeping ###

import types

import typecheck.doctest_support
from typecheck import typecheck, TypeCheckException, Any

class _TestSuite(TestCase):
    def testCreateTypeCheckedMethod(self):
        @typecheck(int)
        def f(a):
            return 1
            
        self.assertEquals(1, f(5))
        
        try:
            f('a')
            self.fail()
        except TypeCheckException:
            pass
            
    def testCreateTypeCheckedMethodPositional(self):
        @typecheck(int, int, str)
        def f(a, b, c):
            return 1
            
        self.assertEquals(1, f(5, 6, '7'))
        
        for a, b, c in [(5, 6, 7), ('5', 6, '7'), (8, '9', 10), (8, '9', '10')]:
            try:
                f(a, b, c)
                self.fail('Failed with values (%s, %s, %s)' % (a, b, c))
            except TypeCheckException:
                pass
                
    def testCreateTypeCheckedMethodKeyword(self):
        # The original did not supply a type for b
        @typecheck(a=int, b=Any(), c=str)
        def f(a=None, b=None, c=None):
            return 1

        self.assertEquals(1, f(5, 6, '7'))
        self.assertEquals(1, f(5, [], '7'))

        for a, b, c in [(5, 6, 7), ('11', 12, '13'), (8, '9', 10)]:
            try:
                self.assertEquals(1, f(a=a, b=b, c=c))
                self.fail('Failed with values (%s, %s, %s)' % (a, b, c))
            except TypeCheckException:
                pass
                
    def testCreateTypeCheckedMethodCombined(self):
        @typecheck(int, b=int, c=str)
        def f(a, b=None, c=None):
            return 1

        self.assertEquals(1, f(5, 6, '7'))
        self.assertEquals(1, f(5, 13, 'hello'))

        for a, b, c in [(5, 6, 7), ('11', 12, '13'), (8, '9', 10)]:
            try:
                self.assertEquals(1, f(a, b=b, c=c))
                self.fail('Failed with values (%s, %s, %s)' % (a, b, c))
            except TypeCheckException:
                pass
                
    def testTypeCheckedMethodRetainsName(self):
        @typecheck(int)
        def f(a):
            pass
            
        self.assertEquals('f', f.__name__)
        
    def testTypeCheckedMethodRetainsDocstring(self):
        @typecheck(int)
        def f(a):
            'docstring'
            pass
        
        self.assertEquals('docstring', f.__doc__)   
    
    def testTypeCheckedDocstringGetsFoundByDoctest(self):
        import doctest
        import doctests
        
        finder = doctest.DocTestFinder(verbose=True)
        tests = finder.find(doctests)

        self.assertEquals(3, len(tests))
        
        runner = doctest.DocTestRunner(doctest.OutputChecker())
        
        for test in tests:
            runner.run(test)
        
        self.assertEquals(7, runner.summarize()[1])
        self.assertEquals(0, runner.summarize()[0])
        
    def testOldStyleClassesAcceptedAsPatterns(self):
        class T:
            pass
            
        @typecheck(T)
        def f(t_instance):
            pass            
    
    ##########################################################################
    
    def a_testTypeCheckMatchesKwToPnIfNoCorrespondingKw(self):
        @typecheck(b=str)
        def my_func(a, b):
            pass
    
    def a_testTypeCheckMatchesKeywordsToPositionalNames(self):
        @typecheck(a=str)
        def my_func(a):
            pass
            
        try:
            my_func(4, 7)
            self.fail('Should have raised a TypeCheckException')
        except TypeCheckException:
            pass
        except:
            self.fail('Should have raised a TypeCheckException')
            
        @typecheck(a=str, b=int)
        def my_func(a, b, c):
            pass
        
        try:
            my_func(4, 7, 7)
            self.fail('Should have raised a TypeCheckException')
        except TypeCheckException:
            pass
        except:
            self.fail('Should have raised a TypeCheckException')
            
        try:
            my_func('4', 7, 7)
            self.fail('Should have raised a TypeCheckException')
        except TypeCheckException:
            pass
        except:
            self.fail('Should have raised a TypeCheckException')    
        
        try:
            my_func(4, '7', 7)
            self.fail('Should have raised a TypeCheckException')
        except TypeCheckException:
            pass
        except:
            self.fail('Should have raised a TypeCheckException')

### Bookkeeping ###
if __name__ == '__main__':
    import __main__
    support.run_all_tests(__main__)
