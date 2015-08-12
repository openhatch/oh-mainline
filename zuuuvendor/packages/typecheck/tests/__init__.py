import os
import os.path
import unittest
import types

import support

all_tests = unittest.TestSuite()

tests_dir = os.path.join(os.getcwd(), 'tests')
tests = [t[0:-3] for t in os.listdir(tests_dir)
            if t.startswith('test_') and t.endswith('.py')]

loader = unittest.TestLoader()
for t in tests:
    __import__('tests.' + t)
    mod = globals()[t]
    
    all_tests.addTests( loader.loadTestsFromModule(mod) )
