# Django settings for mysite project.

import os
import logging

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
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'k%&pic%c5%6$%(h&eynhgwhibe9-h!_iq&(@ktx#@1-5g2+he)'

TEMPLATE_CONTEXT_PROCESSORS = (
            'django.core.context_processors.auth',
            'django.core.context_processors.debug',
            'django.core.context_processors.i18n',
            'django.core.context_processors.media',
            'django.core.context_processors.request',
            'django_authopenid.context_processors.authopenid',
        )

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
    'django_authopenid.middleware.OpenIDMiddleware',
    'mysite.base.middleware.LocationMiddleware',
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
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.webdesign',
    'django.contrib.admin',
    'registration',
    'django_authopenid',
    'django_extensions',
    'windmill',
    'south',
    'django_assets',
    'celery',
    'invitation',
    'mysite.search',
    'mysite.profile',
    'mysite.customs',
    'mysite.account',
    'mysite.base',
    'mysite.info',
    'mysite.project',
    'mysite.senseknocker',
)

# file: settings.py #
TEST_RUNNER = 'mysite._profiling.profile_tests'
TEST_PROFILE = '/tmp/openhatch-profiling-data.%s' % os.environ.get('USER', 'unknown')

## AMQP, Rabbit Queue, Celery
AMQP_SERVER = "localhost"
AMQP_PORT = 5672
AMQP_USER = "rabbiter"
AMQP_PASSWORD = "johT4qui"
AMQP_VHOST = "localhost"

cooked_data_password = 'AXQaTjp3'
AUTH_PROFILE_MODULE = "profile.Person"

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/' # Landing page

OHLOH_API_KEY='JeXHeaQhjXewhdktn4nUw' # This key is called "Oman testing"
                                        # at <https://www.ohloh.net/accounts/paulproteus/api_keys>
#OHLOH_API_KEY='0cWqe4uPw7b8Q5337ybPQ' # This key is called "API testing"

applog = logging.getLogger('applog')
applog.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_formatter = logging.Formatter('%(asctime)s %(funcName)s:%(lineno)d %(levelname)-8s %(message)s')
_handler.setFormatter(_formatter)
applog.addHandler(_handler)

# Invite codes last seven days
ACCOUNT_INVITATION_DAYS=7
INVITE_MODE=False # Enable this on production site ...?
INVITATIONS_PER_USER=5

DEFAULT_FROM_EMAIL = 'all@openhatch.org'

# Don't cache on dev server
CACHE_BACKEND = 'dummy://'

# Launchpad credentials
LP_CREDS_BASE64_ENCODED='WzFdCmNvbnN1bWVyX3NlY3JldCA9IAphY2Nlc3NfdG9rZW4gPSBHV0tKMGtwYmNQTkJXOHRQMWR2Ygpjb25zdW1lcl9rZXkgPSBvcGVuaGF0Y2ggbGl2ZSBzaXRlCmFjY2Vzc19zZWNyZXQgPSBSNWtrcXBmUERiUjRiWFFQWGJIMkdoc3ZQamw2SjlOc1ZwMzViN0g2d3RjME56Q3R2Z3JKeGhNOVc5a2swU25CSnRHV1hYckdrOFFaMHZwSgoK'

GITHUB_USERNAME='openhatched'
GITHUB_API_TOKEN='6f2b15214757ff724155654c97f4ce92'

# Set this to false to bundle files even if not in production.
# ASSETS_DEBUG = False

ASSETS_EXPIRE = 'querystring'
