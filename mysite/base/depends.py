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
