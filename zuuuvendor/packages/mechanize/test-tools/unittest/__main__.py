"""Main entry point"""

import sys
if sys.argv[0].endswith("__main__.py"):
    sys.argv[0] = "unittest"

from unittest.main import main
main(module=None)
