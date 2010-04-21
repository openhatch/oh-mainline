# Django settings for mysite project.

import os
import logging
import datetime

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

DATABASE_CHARSET = 'utf8'           # omg I hate you MySQL
DATABASE_ENGINE = 'mysql'           # Other options:
                                    # 'postgresql_psycopg2', 'postgresql', 'mysql',
                                    # 'sqlite3' or 'oracle'.
DATABASE_NAME = 'oh_milestone_a'    # Or path to database file if using sqlite3.

# NB: None of the following DATABASE_ options are used with sqlite3.
DATABASE_USER = 'oh_milestone_a'    
DATABASE_PASSWORD = 'ahmaC0Th'      
DATABASE_HOST = 'renaissance.local' # Set to empty string for localhost. 
DATABASE_HOST = 'localhost'         # Set to empty string for localhost. 
DATABASE_PORT = ''                  # Set to empty string for default. 

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

MEDIA_ROOT_BEFORE_STATIC = os.path.dirname(__file__) # This is needed for {% version %}

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(MEDIA_ROOT_BEFORE_STATIC, 'static')

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
    'mysite.base.middleware.DetectLogin', # This must live on top of Auth + Session middleware
    'django.middleware.common.CommonMiddleware',
    'staticgenerator.middleware.StaticGeneratorMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_authopenid.middleware.OpenIDMiddleware',
    'mysite.base.middleware.LocationMiddleware',
    'mysite.base.middleware.HandleWannaHelpQueue',
    # Django debug toolbar
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'mysite.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    
)

STATIC_GENERATOR_URLS = (
    r'^/people/',
    r'^/search/',
)

STATIC_DOC_ROOT = 'static/'

# Sessions in /tmp
SESSION_ENGINE="django.contrib.sessions.backends.file"

## Django search via Haystack
HAYSTACK_SITECONF='mysite.haystack_configuration'
HAYSTACK_SEARCH_ENGINE='solr'
HAYSTACK_SOLR_URL='http://127.0.0.1:8983/solr'

INSTALLED_APPS = (
    'ghettoq',
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
    'mysite.project',
    'mysite.senseknocker',
    'haystack',
    'voting',
    #'debug_toolbar',
)

# file: settings.py #
TEST_RUNNER = 'mysite._profiling.profile_tests'
TEST_PROFILE = '/tmp/openhatch-profiling-data.%s' % os.environ.get('USER', 'unknown')

## AMQP, Rabbit Queue, Celery
CARROT_BACKEND = 'amqp'
BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = 'rabbiter'
BROKER_PASSWORD = 'johT4qui'
BROKER_VHOST = 'localhost'


cooked_data_password = 'AXQaTjp3'
AUTH_PROFILE_MODULE = "profile.Person"

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/' # Landing page

OHLOH_API_KEY='JeXHeaQhjXewhdktn4nUw' # This key is called "Oman testing"
                                        # at <https://www.ohloh.net/accounts/paulproteus/api_keys>
#OHLOH_API_KEY='0cWqe4uPw7b8Q5337ybPQ' # This key is called "API testing"

logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(funcName)s:%(lineno)d %(levelname)-8s %(message)s',
)

# Invite codes last seven days
ACCOUNT_INVITATION_DAYS=7
INVITE_MODE=False # Enable this on production site ...?
INVITATIONS_PER_USER=100

DEFAULT_FROM_EMAIL = 'all@openhatch.org'

#CACHE_BACKEND = 'file:///tmp/django_cache_belonging_to_%s' % os.environ.get('USER', 'unknown')
CACHE_BACKEND = "dummy://"
#CACHE_BACKEND = "memcached://127.0.0.1:11211/?timeout=1"

# Launchpad credentials
LP_CREDS_BASE64_ENCODED='WzFdCmNvbnN1bWVyX3NlY3JldCA9IAphY2Nlc3NfdG9rZW4gPSBHV0tKMGtwYmNQTkJXOHRQMWR2Ygpjb25zdW1lcl9rZXkgPSBvcGVuaGF0Y2ggbGl2ZSBzaXRlCmFjY2Vzc19zZWNyZXQgPSBSNWtrcXBmUERiUjRiWFFQWGJIMkdoc3ZQamw2SjlOc1ZwMzViN0g2d3RjME56Q3R2Z3JKeGhNOVc5a2swU25CSnRHV1hYckdrOFFaMHZwSgoK'

GITHUB_USERNAME='openhatched'
GITHUB_API_TOKEN='6f2b15214757ff724155654c97f4ce92'

# Set this to false to bundle files even if not in production.
ASSETS_DEBUG = True

ADD_VERSION_STRING_TO_IMAGES = True
ADD_VERSION_STRING_TO_IMAGES_IN_DEBUG_MODE = True

# The setting below adds a querystring to assets, e.g. bundle.css?1264015076
# This querystring changes whenever we change the asset. This prevents the
# client's cached version of an asset from overriding our new asset.
ASSETS_EXPIRE = 'querystring'
WHAT_SORT_OF_IMAGE_CACHE_BUSTING = ASSETS_EXPIRE

INTERNAL_IPS = ('127.0.0.1',)

FORWARDER_DOMAIN = "forwarder.openhatch.org"
FORWARDER_LISTINGTIME_TIMEDELTA = datetime.timedelta(days=2) # how long the forwarder is listed
FORWARDER_LIFETIME_TIMEDELTA = datetime.timedelta(days=5) # how long the forwarder actually works
# note about the above: for 3 days, 2 forwarders for the same user work.
# at worst, you visit someone's profile and find a forwarder that works for 3 more days
# at best, you visit someone's profile and find a forwarder that works for 5 more days
# at worst, we run a postfixifying celery job once every two days for each user

POSTFIX_FORWARDER_TABLE_PATH = '/tmp/email_forwarders'

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

#CELERY_ALWAYS_EAGER = True # This is set to True in the test runner also.

WEB_ROOT = os.path.join(MEDIA_ROOT, '_cache')
