"""Some helpers for deprecation messages"""

import warnings

from scrapy.exceptions import ScrapyDeprecationWarning

def attribute(obj, oldattr, newattr, version='0.12'):
    cname = obj.__class__.__name__
    warnings.warn("%s.%s attribute is deprecated and will be no longer supported "
        "in Scrapy %s, use %s.%s attribute instead" % \
        (cname, oldattr, version, cname, newattr), ScrapyDeprecationWarning, stacklevel=3)
