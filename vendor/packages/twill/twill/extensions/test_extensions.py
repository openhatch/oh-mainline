"""
Used in test-shell, to test default command execution & extensions.
"""

flag = False

__all__ = ['flag_true', 'assert_flag']

def flag_true():
    global flag
    flag = True

def assert_flag():
    global flag
    assert flag
