# Django settings for mysite project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Asheesh Laroia', 'asheesh@openhatch.org'),
    ('Raphael Krut-Landau', 'raphael@openhatch.org')
)

MANAGERS = ADMINS

DATABASE_OPTIONS = {
    'read_default_file': './my.cnf',
}

TEST_DATABASE_OPTIONS = {
    'read_default_file': './my.cnf',
}

DATABASE_CHARSET = 'utf8' # omg I hate you MySQL
DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'oh_milestone_a'             # Or path to database file if using sqlite3.
DATABASE_USER = 'oh_milestone_a'             # Not used with sqlite3.
DATABASE_PASSWORD = 'ahmaC0Th'         # Not used with sqlite3.
DATABASE_HOST = 'renaissance.local'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_HOST = 'localhost'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'k%&pic%c5%6$%(h&eynhgwhibe9-h!_iq&(@ktx#@1-5g2+he)'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'mysite.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

STATIC_DOC_ROOT = 'static/'

# Sessions in /tmp
SESSION_ENGINE="django.contrib.sessions.backends.file"

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.webdesign',
    'django.contrib.admin',
    'windmill',
    'south',
    'celery',
    'search',
    'profile',
    'customs',
    'consulting',
)

### HACK
from socket import gethostname
if gethostname() in ('renaissance', 'yggdrasil', 'builder', 'vellum') and DEBUG:
    DEBUG_PROPAGATE_EXCEPTIONS=True

# file: settings.py #
TEST_RUNNER = '_profiling.profile_tests'
TEST_PROFILE = '/tmp/profile'

## AMQP, Rabbit Queue, Celery
AMQP_SERVER = "localhost"
AMQP_PORT = 5672
AMQP_USER = "rabbiter"
AMQP_PASSWORD = "johT4qui"
AMQP_VHOST = "localhost"

cooked_data_password = 'AXQaTjp3'
AUTH_PROFILE_MODULE = "profile.Person"

LOGIN_URL = '/people/login/'

OHLOH_API_KEY='JeXHeaQhjXewhdktn4nUw' # "Oman testing"

