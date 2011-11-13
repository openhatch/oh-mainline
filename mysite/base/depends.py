import os

try:
    import lxml
    import lxml.etree
    import lxml.html
except:
    class nothing(object):
        pass
    lxml = nothing()
    lxml.etree = None
    lxml.html = None

import logging

if lxml.html is None:
    logging.warning("Some parts of the OpenHatch site may fail because the lxml"
                    " library is not installed. Look in README.mkd for"
                    " information about lxml.")

def svnadmin_available():
    # FIXME: This should move to a variable controlled
    # by settings.py.
    SVNADMIN_PATH = '/usr/bin/svnadmin'
    return os.path.exists(SVNADMIN_PATH)


### Here we try to import "Image", from the Python Imaging Library.
### If we fail, Image is None.
Image = None
try:
    import Image
except:
    try:
        from PIL import Image
    except ImportError:
        ### Okay, for a good time, let's hack sys.modules.
        ### This permits Django to think ImageFields might
        ### possibly work.
        import sys
        sys.modules['Image'] = sys.modules['sys']

try:
    import launchpadbugs
    import launchpadbugs.connector
    import launchpadbugs.basebuglistfilter
    import launchpadbugs.text_bug
    import launchpadbugs.lphelper
except ImportError: # usually because python2libxml2 is missing
    launchpadbugs = None
    logging.warning("launchpadbugs did not import. Install python-libxml2.")
