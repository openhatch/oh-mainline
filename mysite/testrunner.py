from django.conf import settings
import xmlrunner.extra.djangotestrunner
from django.test.simple import run_tests

def run(*args, **kwargs):
    settings.CELERY_ALWAYS_EAGER = True
    return run_tests(*args, **kwargs)

# Another option is this guy:
# xmlrunner.extra.djangotestrunner.run_tests(*args, **kwargs)
# but he breaks pdbs
