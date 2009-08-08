from settings import *
DATABASE_ENGINE='sqlite3'
DATABASE_NAME=':memory:'
DATABASE_OPTIONS={}

### HACK
from socket import gethostname
if gethostname() in ('renaissance', 'yggdrasil', 'builder', 'vellum') and DEBUG:
    DEBUG_PROPAGATE_EXCEPTIONS=True

