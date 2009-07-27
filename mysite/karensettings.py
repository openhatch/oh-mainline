from settings import *


DATABASE_CHARSET = 'utf8' # omg I hate you MySQL
DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'oh_karen'             # Or path to database file if using sqlite3.
DATABASE_USER = 'oh_karen'             # Not used with sqlite3.
DATABASE_PASSWORD = 'ahmaC0Th'         # Not used with sqlite3.
DATABASE_HOST = 'localhost'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

### HACK
from socket import gethostname
DEBUG_PROPAGATE_EXCEPTIONS=True

# file: settings.py #
TEST_RUNNER = '_profiling.profile_tests'
TEST_PROFILE = '/tmp/profile-karen'

## AMQP, Rabbit Queue, Celery
AMQP_SERVER = "localhost"
AMQP_PORT = 5672
AMQP_USER = "karen"
AMQP_PASSWORD = "johT4qui"
AMQP_VHOST = "localhost"

