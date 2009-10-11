from settings import *

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME="/dev/shm/django-test.db"

DATABASE_OPTIONS = {}
TEST_DATABASE_OPTIONS = {
    'init_command':
        'PRAGMA temp_store = MEMORY; PRAGMA synchronous=OFF;'
}

