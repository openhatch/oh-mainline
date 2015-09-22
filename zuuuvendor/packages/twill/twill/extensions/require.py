"""
A simple set of extensions to manage post-load requirements for pages.

Commands:

   require       -- turn on post-load requirements; either 'success' or
                    'links_ok'.
                    
   no_require    -- turn off requirements.
   
   skip_require  -- for the next page visit, skip requirements processing.
   
   flush_visited -- flush the list of already visited pages
                    (for links checking)
"""

__all__ = ['require', 'skip_require', 'flush_visited', 'no_require']

DEBUG=False

###

_requirements = []                      # what requirements to satisfy

ignore_once = False                     # reset after each hook call
ignore_always = False                   # never reset
links_visited = {}                      # list of known good links, for
                                        #   link checking.

def _require_post_load_hook(action, *args, **kwargs):
    """
    post-load hook function to be called after each page is loaded.
    
    See TwillBrowser._journey() for more information.
    """
    if action == 'back':                # do nothing on a 'back'
        return
    
    from twill import commands
    OUT=commands.OUT

    global ignore_once
    global ignore_always
    
    if ignore_once or ignore_always:
        ignore_once = False
        return
    
    for what in _requirements:

        ####
        ####
        ####
        
        if what == 'success':
            if DEBUG:
                print>>OUT, 'REQUIRING success'
            commands.code(200)
            
        ####
        ####
        ####
            
        elif what == 'links_ok':
            from check_links import check_links
            
            ignore_always = True
            if DEBUG:
                print>>OUT, 'REQUIRING functioning links'
                print>>OUT, '(already visited:)'
                print "\n\t".join(links_visited.keys())
                
            try:
                check_links(visited=links_visited)
            finally:
                ignore_always = False

#######

#
# twill command-line functions.
#

def skip_require():
    """
    >> skip_require

    Skip the post-page-load requirements.
    """
    global ignore_once
    ignore_once = True

def require(what):
    """
    >> require <what>

    After each page is loaded, require that 'what' be satisfied.  'what'
    can be:
      * 'success' -- HTTP return code is 200
      * 'links_ok' -- all of the links on the page load OK (see 'check_links'
                      extension module)
    """
    global _requirements
    from twill import commands

    #
    # install the post-load hook function.
    #

    if _require_post_load_hook not in commands.browser._post_load_hooks:
        if DEBUG:
            print>>commands.OUT, 'INSTALLING POST-LOAD HOOK'
        commands.browser._post_load_hooks.append(_require_post_load_hook)

    #
    # add the requirement.
    #

    if what not in _requirements:
        if DEBUG:
            print>>commands.OUT, 'Adding requirement', what
        _requirements.append(what)

def no_require():
    """
    >> no_require

    Remove all post-load requirements.
    """
    from twill import commands
    
    l = commands.browser._post_load_hooks
    l = [ fn for fn in l if fn != _require_post_load_hook ]
    commands.browser._post_load_hooks = l

    global _requirements
    _requirements = []

def flush_visited():
    """
    >> flush_visited
    
    Flush the list of pages successfully visited already.
    """
    global links_visited
    links_visited.clear()
