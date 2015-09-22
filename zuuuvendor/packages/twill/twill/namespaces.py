"""
Global and local dictionaries, + initialization/utility functions.
"""

global_dict = {}

def init_global_dict():
    """
    Initialize global dictionary with twill commands.

    This must be done after all the other modules are loaded, so that all
    of the commands are already defined.
    """
    exec "from twill.commands import *" in global_dict
    import twill.commands
    command_list = twill.commands.__all__
    
    import twill.parse
    twill.parse.command_list.extend(command_list)

# local dictionaries.
_local_dict_stack = []

###

# local dictionary management functions.

def new_local_dict():
    """
    Initialize a new local dictionary & push it onto the stack.
    """
    d = {}
    _local_dict_stack.append(d)

    return d

def pop_local_dict():
    """
    Get rid of the current local dictionary.
    """
    _local_dict_stack.pop()

###

def get_twill_glocals():
    """
    Return global dict & current local dictionary.
    """
    global global_dict, _local_dict_stack
    assert global_dict is not None, "must initialize global namespace first!"

    if len(_local_dict_stack) == 0:
        new_local_dict()

    return global_dict, _local_dict_stack[-1]

###
