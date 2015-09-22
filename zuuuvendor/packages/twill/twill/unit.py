"""
Support functionality for using twill in unit tests.
"""

import sys, os, time
from cStringIO import StringIO

# package import
from parse import execute_file

class TestInfo:
    """
    Object containing info for a test: script to run, server function to
    run, and port to run it on.  Note that information about server port
    *must* be decided by the end of the __init__ function.

    The optional sleep argument specifies how many seconds to wait for the
    server to set itself up.  Default is 0.
    """
    
    def __init__(self, script, server_fn, port, sleep=0):
        self.script = script
        self.server_fn = server_fn
        self.port = port
        self.stdout = None
        self.stderr = None
        self.sleep = sleep

    def start_server(self):
        # save old stdout/stderr
        old_out, old_err = sys.stdout, sys.stderr

        # create new stdout/stderr
        self.stdout = sys.stdout = StringIO()
        self.stderr = sys.stderr = StringIO()
        
        try:
            self.server_fn()
        finally:
            # restore stdout/stderr
            sys.stdout, sys.stderr = old_out, old_err

    def run_script(self):
        """
        Run the given twill script on the given server.
        """
        time.sleep(self.sleep)
        url = self.get_url()
        execute_file(self.script, initial_url=url)

    def get_url(self):
        "Calculate the test server URL."
        return "http://localhost:%d/" % (self.port,)

#
# run_test
#

def run_test(test_info):
    """
    Run a test on a Web site where the Web site is running in a child
    process.
    """
    pid = os.fork()

    if pid is 0:
        run_child_process(test_info)
        # never returns...

    #
    # run twill test script.
    #
    
    child_pid = pid
    try:
        test_info.run_script()
    finally:
        os.kill(child_pid, 9)

#
# run_child_process
#
        
def run_child_process(test_info):
    """
    Run a Web server in a child process.
    """
    test_info.start_server()
    sys.exit(0)
