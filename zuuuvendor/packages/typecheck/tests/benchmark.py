"""
A benchmark script to profile changes to typecheck's deep internals
"""

import time

### Bookkeeping ###
import support
if __name__ == '__main__':
    support.adjust_path()
### /Bookkeeping ###

import typecheck
from typecheck import accepts

print "Using typecheck from", typecheck.__file__

def test_add_accepts_to_naked_function_1():
    """Adding accepts to a naked function: single positional param"""

    def foo(int_1):
        pass

    t = time.time()
    for i in range(0, 10000):
        accepts(int)(foo)
    return time.time() - t

def test_add_accepts_to_naked_function_2():
    """Adding accepts to a naked function: multi positional params"""

    def foo(int_1, int_2, int_3):
        pass

    t = time.time()
    for i in range(0, 10000):
        accepts(int, int, int)(foo)
    return time.time() - t


def test_add_accepts_to_naked_function_3():
    """Adding accepts to a naked function: pos params, kw types"""

    def foo(int_1, int_2, int_3):
        pass

    t = time.time()
    for i in range(0, 10000):
        accepts(int_2=int, int_1=int, int_3=int)(foo)
    return time.time() - t


def test_add_accepts_to_naked_function_4():
    """Adding accepts to a naked function: kw params, kw types"""
    
    def foo(kw_1=5, kw_2=6, kw_3=7):
        pass

    t = time.time()
    for i in range(0, 10000):
        accepts(kw_1=int, kw_2=int, kw_3=int)(foo)
    return time.time() - t


def test_call_accepts_func_single_pos_passes():
    """Calling an accepts-checked function: single pos, passes"""

    @accepts(int)
    def foo(int_1):
        pass

    t = time.time()
    for i in range(0, 10000):
        foo(5)
    return time.time() - t

def test_call_accepts_func_multi_pos_passes():
    """Calling an accepts-checked function: multi positional params"""

    @accepts(int, int, int)
    def foo(int_1, int_2, int_3):
        pass

    t = time.time()
    for i in range(0, 10000):
       foo(5, 6, 7)
    return time.time() - t


def test_call_accepts_func_pos_params_kw_types():
    """Calling an accepts-checked function: pos params, pos args"""

    @accepts(int_2=int, int_1=int, int_3=int)
    def foo(int_1, int_2, int_3):
        pass

    t = time.time()
    for i in range(0, 10000):
        foo(5, 6, 7)
    return time.time() - t


def test_call_accepts_func_kw_params_kw_types():
    """Calling an accepts-checked function: kw params, pos args"""
    
    @accepts(kw_1=int, kw_2=int, kw_3=int)
    def foo(kw_1=5, kw_2=6, kw_3=7):
        pass

    t = time.time()
    for i in range(0, 10000):
        foo(5, 6, 7)
    return time.time() - t












if __name__ == '__main__':
    local_items = locals().items()
    tests = [test for name, test in local_items if name.startswith('test_')]
    max_len = max([len(test.__doc__) for test in tests])

    for test in sorted(tests, key=lambda o: o.__doc__):
        print test.__doc__.ljust(max_len), ':', test()

