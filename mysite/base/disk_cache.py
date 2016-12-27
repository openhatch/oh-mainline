# Note:
# This is a total hack to implement simple disk-based memoization,
# with no expiration.

import os
PATH = '/tmp/django_cache_belonging_to_%s' % os.environ.get('USER', 'unknown')


def set(key, value):
    if not os.path.isdir(PATH):
        os.mkdir(PATH)
    file_obj = file(os.path.join(PATH, key), 'w')
    file_obj.write(value)
    file_obj.close()


def get(key):
    try:
        with open(os.path.join(PATH, key)) as f:
            return f.read()
    except IOError:
        return None
