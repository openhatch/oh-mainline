##
# - Originally submitted by Knut Hartmann (2005/09/28)
# - Hacked up by Iain to allow integration with the _unittest module
# - Further hacked up by Collin Winter (2005.11.16) to work with his own testsuite

from typecheck import typecheck

@typecheck(str)
def checker(aString):
    """    
    >>> print [x for x in globals().copy() if not x.startswith('__')]
    ['checker2', 'typecheck', '_[1]', 'checker', 'Rational', 'testMyClass', 'MyTestClass']
    >>> print [x for x in locals().copy() if not x.startswith('__')]
    ['checker2', 'typecheck', '_[1]', 'checker', 'Rational', 'testMyClass', 'x', 'MyTestClass']
    >>> checker('Nonsense')
    2
    """
    if aString == "":
        return 1
    else:
        return 2

def checker2(aString):
    """
    >>> print [x for x in globals().copy() if not x.startswith('__')]
    ['checker2', 'typecheck', '_[1]', 'checker', 'Rational', 'testMyClass', 'MyTestClass']
    >>> print [x for x in locals().copy() if not x.startswith('__')]
    ['checker2', 'typecheck', '_[1]', 'checker', 'Rational', 'testMyClass', 'x', 'MyTestClass']
    >>> checker2('Nonsense')
    2
    """
    if aString == "":
        return 1
    else:
        return 2

class Rational(object):
    @typecheck(object, int, int)
    def __init__(self, numerator, denumerator):
        self.p = numerator
        self.q = denumerator

class MyTestClass:
    @typecheck(object, int, Rational)
    def __init__(self, a, b):
        pass

def testMyClass():
    """
    >>> print MyTestClass(1, Rational(1, 2)) # doctest:+ELLIPSIS
    <...doctests.MyTestClass instance at 0x...>
    """
    pass
