### The point of this module is that,
### when you import it, you get the "vendor" directory
### on your python's sys.path.

import sys
import os.path
import site

already_vendorified = False
def vendorify():
    global already_vendorified
    if already_vendorified:
        return

    ROOT = os.path.dirname(os.path.abspath(__file__))
    path = lambda *a: os.path.join(ROOT, *a)

    prev_sys_path = list(sys.path)
    site.addsitedir(path('.'))

    # Move the new items to the front of sys.path.
    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path

    # Remark that we have already vendorified
    already_vendorified = True
