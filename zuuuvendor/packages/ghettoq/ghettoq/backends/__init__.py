import sys

BACKEND_ALIASES = {
    "redis": "ghettoq.backends.pyredis.RedisBackend",
    "database": "ghettoq.backends.database.DatabaseBackend",
    "mongodb": "ghettoq.backends.mongodb.MongodbBackend",
    "beanstalk": "ghettoq.backends.beanstalk.BeanstalkBackend",
    "couchdb": "ghettoq.backends.couch_db.CouchdbBackend",
}
_backend_cache = {}


def resolve_backend(backend):
    backend = BACKEND_ALIASES.get(backend.lower(), backend)
    backend_module_name, backend_cls_name = backend.rsplit('.', 1)
    return backend_module_name, backend_cls_name


def _get_backend_cls(backend):
    backend_module_name, backend_cls_name = resolve_backend(backend)

    __import__(backend_module_name)
    backend_module = sys.modules[backend_module_name]
    return getattr(backend_module, backend_cls_name)


def get_backend_cls(backend):
    if backend not in _backend_cache:
        _backend_cache[backend] = _get_backend_cls(backend)
    return _backend_cache[backend]


def Connection(type, *args, **kwargs):
    return get_backend_cls(type)(*args, **kwargs)
