# Source: http://www.djangosnippets.org/snippets/1315/
# file: profiling.py #
from django.test.simple import run_tests
from django.conf import settings
try:
    import cProfile as profile
except ImportError:
    import profile

def profile_tests(*args, **kwargs):
    settings.CELERY_ALWAYS_EAGER = True
    profile.runctx('run_tests(*args, **kwargs)',
                {'run_tests':run_tests,'args':args,'kwargs':kwargs},
                {},
                getattr(settings,'TEST_PROFILE',None)
            )

