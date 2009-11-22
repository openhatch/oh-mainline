from settings import *

### HACK
from socket import gethostname
if gethostname() in ('renaissance', 'yggdrasil', 'builder', 'vellum') and DEBUG:
    DEBUG_PROPAGATE_EXCEPTIONS=True

