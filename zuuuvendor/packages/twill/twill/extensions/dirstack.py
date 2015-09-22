"""
Extension functions for manipulating the current working directory (cwd).

Commands:

   chdir -- push the cwd onto the directory stack & change to the new location.
   popd  -- change to the last directory on the directory stack.
"""
import os

_dirstack = []

def chdir(where):
    """
    >> chdir <where>

    Change to the new location, after saving the current directory onto
    the directory stack.  The global variable __dir__ is set to the cwd.
    """
    from twill import commands
    
    cwd = os.getcwd()
    _dirstack.append(cwd)
    print cwd

    os.chdir(where)
    print>>commands.OUT, 'changed directory to "%s"' % (where,)

    commands.setglobal('__dir__', where)

def popd():
    """
    >> popd

    Change back to the last directory on the directory stack.  The global
    variable __dir__ is set to the cwd.
    """
    from twill import commands
    
    where = _dirstack.pop()
    os.chdir(where)
    print>>commands.OUT, 'popped back to directory "%s"' % (where,)

    commands.setglobal('__dir__', where)
