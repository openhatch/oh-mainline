#Django settings for the basic OpenHatch 'mysite' project

# Imports
import subprocess
import os
import logging
import datetime
import sys
import dj_database_url

LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '\n%(levelname)08s %(asctime)25s - %(name)25s - %(message)15s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'class': 'django.utils.log.NullHandler',
        },
        'console':{
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'mysite': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
}

import logging.config
logging.config.dictConfig(LOGGING)

# Figure out where in the filesystem we are.
DIRECTORY_CONTAINING_SETTINGS_PY = os.path.abspath(os.path.dirname(__file__))
# This is needed for {% version %}
MEDIA_ROOT_BEFORE_STATIC = DIRECTORY_CONTAINING_SETTINGS_PY

# Now, actual settings
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Asheesh Laroia', 'asheesh@openhatch.org'),
)

MANAGERS = ADMINS

DATABASE_OPTIONS = {
    'read_default_file': './my.cnf',
}

TEST_DATABASE_OPTIONS = {
    'read_default_file': './my.cnf',
}

DATABASE_CHARSET = 'utf8'           # omg I hate you MySQL
# have to apply it to the test database, too
TEST_DATABASE_CHARSET = 'utf8'

DATABASES = {
    'default': {
        'NAME': os.path.join(MEDIA_ROOT_BEFORE_STATIC, 'site.db'),
        'ENGINE': 'django.db.backends.sqlite3',
        'CHARSET': 'utf8',
    },
}

# Permit it to be overriden
if 'DATABASE_URL' in os.environ:
    DATABASES = {'default': dj_database_url.config()}

OTHER_DATABASES = {
    'postgres': {
        'NAME': 'openhatch',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'localhost',
        'USER': 'postgres',
        'PASSWORD': '',
        'CHARSET': 'utf8',
    },
    'docker': {
        'NAME': 'openhatch',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'postgres',
        'USER': 'openhatch',
        'PASSWORD': 'openhatch',
        'CHARSET': 'utf8',
    },
}

if os.environ.get('DOCKER'):
    DATABASES['default'] = OTHER_DATABASES['docker']

if os.environ.get('USE_POSTGRES'):
    DATABASES['default'] = OTHER_DATABASES['postgres']

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
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django_authopenid.context_processors.authopenid',
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.csrf.CsrfViewMiddleware',
    # This must live on top of Auth + Session middleware
    'mysite.base.middleware.DetectLogin',
    'django.middleware.common.CommonMiddleware',
    'mysite.base.middleware.StaticGeneratorMiddlewareOnlyWhenAnonymous',
    'sessionprofile.middleware.SessionProfileMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_authopenid.middleware.OpenIDMiddleware',
    'mysite.base.middleware.HandleWannaHelpQueue',
    'django.middleware.transaction.TransactionMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.

)

STATIC_GENERATOR_URLS = (
    r'^/people/',
    r'^/search/',
    r'^/\+cacheable/',
)

STATIC_URL = '/statik/'

STATIC_DOC_ROOT = 'static/'

# Sessions in /tmp
# mysite.account.view_helpers.clear_user_sessions assumes the DB backend, it
# will not work otherwise
SESSION_ENGINE = "django.contrib.sessions.backends.db"

INSTALLED_APPS = (
    'ghettoq',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.webdesign',
    'django.contrib.admin',
    'registration',
    'django_authopenid',
    'django_extensions',
    'south',
    'django_assets',
    'invitation',
    'mysite.search',
    'mysite.profile',
    'mysite.customs',
    'mysite.account',
    'mysite.base',
    'mysite.project',
    'mysite.missions',
    'mysite.bugsets',
    'voting',
    'reversion',
    'debug_toolbar',
    'sessionprofile',
    'model_utils',
    'djkombu',
    'inplaceeditform',
    'django_webtest',
    'social.apps.django_app.default',
    'httpproxy',
)

# testrunner allows us to control which testrunner to use
TEST_RUNNER = 'mysite.testrunner.OpenHatchTestRunner'
# Optionally, use XML reporting
if os.environ.get('USE_XML_TEST_REPORTING', None):
    TEST_RUNNER = 'mysite.testrunner.OpenHatchXMLTestRunner'

# Make test names prettier
TEST_OUTPUT_DESCRIPTIONS = True

TEST_OUTPUT_DIR = "test_output"

# AMQP, Rabbit Queue
cooked_data_password = 'AXQaTjp3'
AUTH_PROFILE_MODULE = "profile.Person"

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/'  # Landing page

OHLOH_API_KEY = 'JeXHeaQhjXewhdktn4nUw'  # This key is called "Oman testing"
                                        # at <https://www.ohloh.net/accounts/paulproteus/api_keys>
# OHLOH_API_KEY='0cWqe4uPw7b8Q5337ybPQ' # This key is called "API testing"



# Invite codes last seven days
ACCOUNT_INVITATION_DAYS = 7
INVITE_MODE = False  # Enable this on production site ...?
INVITATIONS_PER_USER = 100

DEFAULT_FROM_EMAIL = 'all@openhatch.org'

# If you're testing any of the email-related features locally, make sure the 'EMAIL_*" settings here are
# un-commented, and then open a new terminal and type "python -m smtpd -n -c DebuggingServer localhost:1025"
# to run a local email server.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_PORT = 1025

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'openhatch'
    }
}

# Launchpad credentials
LP_CREDS_BASE64_ENCODED = 'WzFdCmNvbnN1bWVyX3NlY3JldCA9IAphY2Nlc3NfdG9rZW4gPSBHV0tKMGtwYmNQTkJXOHRQMWR2Ygpjb25zdW1lcl9rZXkgPSBvcGVuaGF0Y2ggbGl2ZSBzaXRlCmFjY2Vzc19zZWNyZXQgPSBSNWtrcXBmUERiUjRiWFFQWGJIMkdoc3ZQamw2SjlOc1ZwMzViN0g2d3RjME56Q3R2Z3JKeGhNOVc5a2swU25CSnRHV1hYckdrOFFaMHZwSgoK'

GITHUB_USERNAME = 'paulproteus'
GITHUB_API_TOKEN = 'ceb85898146b6a0d4283cdf8788d8b6a'

# How ASSETS_DEBUG works
# Value     Effect
#   True        Don't pack assets in DEBUG mode
#   False       Pack assets in DEBUG mode
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
# how long the forwarder is listed
FORWARDER_LISTINGTIME_TIMEDELTA = datetime.timedelta(days=2)
# how long the forwarder actually works
FORWARDER_LIFETIME_TIMEDELTA = datetime.timedelta(days=10)
# note about the above: for 3 days, 2 forwarders for the same user work.
# at worst, you visit someone's profile and find a forwarder that works for 3 more days
# at best, you visit someone's profile and find a forwarder that works for 5 more days

# Note: POSTFIX_FORWARDER_TABLE_PATH is disabled by default in settings.py
#       while it is enabled in the deployment_settings.py
#       See documentation in advanced_installation.rst for more details
POSTFIX_FORWARDER_TABLE_PATH = None

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

WEB_ROOT = os.path.join(MEDIA_ROOT, '_cache')

SERVER_NAME = 'openhatch.org'

SVN_REPO_PATH = os.path.abspath(os.path.join(MEDIA_ROOT_BEFORE_STATIC, 'missions-userdata', 'svn'))

# This should include a trailing slash.
# For local sites, this is what you checkout
SVN_REPO_URL_PREFIX = 'file://' + SVN_REPO_PATH + '/'

# This path is used when determining whether to run svn mission tests
SVNADMIN_PATH = '/usr/bin/svnadmin'

# The script to invoke for management commands in this environment.
PATH_TO_MANAGEMENT_SCRIPT = os.path.abspath(
    os.path.join(DIRECTORY_CONTAINING_SETTINGS_PY, '../manage.py'))
SOUTH_TESTS_MIGRATE = False

GIT_REPO_PATH = os.path.join(MEDIA_ROOT_BEFORE_STATIC, 'missions-userdata', 'git')
# For local sites, this is what you clone
GIT_REPO_URL_PREFIX = GIT_REPO_PATH + '/'

# user@host spec to use when SSHing into the remote node that contains
# git and svn mission repositories.
REMOTE_REPO_SETUP_ACCESS_SPEC = os.environ.get('REMOTE_REPO_SETUP_ACCESS_SPEC')

# This setting is used by the customs bug importers.
TRACKER_POLL_INTERVAL = 1  # Days

# Inline edit permissions
ADAPTOR_INPLACEEDIT_EDIT = 'mysite.bugsets.perms.InlineEditPermissions'

DOWNLOADED_GEOLITECITY_PATH = os.path.join(MEDIA_ROOT,
                                           '../../downloads/GeoLiteCity.dat')


# Windows fix-ups
if sys.platform.startswith('win'):
    # staticgenerator seems to act weirdly on Windows, so we disable it.
    MIDDLEWARE_CLASSES.remove(
        'mysite.base.middleware.StaticGeneratorMiddlewareOnlyWhenAnonymous')

# Enable the low-quality, high-load bug recommendation system
RECOMMEND_BUGS = True

ENABLE_NEW_IWH_HANDLER = False

try:
    import bugimporters
except ImportError:
    try:
        sys.path.append(os.path.join('..', 'oh-bugimporters'))
        import bugimporters
    except ImportError:
        # meh.
        pass

AUTHENTICATION_BACKENDS = (
    'social.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.social_auth.associate_by_email',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details'
)

# These secrets correspond to a gmail account that Asheesh created
# called ohdevlogin at gmail.com. If you want the password for that
# account, or need to log in to it for some reason, ask Asheesh for
# it.
#
# Google OAuth2 login, unlike OpenID login before it,
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '905249420634-7ii10lj0dcglujqo89hlnro3oncmq27k.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'qA3pxSEa_ctja22wVNOtGBbr'

# Include a user's customizations
try:
    from local_settings import *
except ImportError:
    pass

# Settings for the IRC bot powering the IRC missions.
IRC_MISSION_SERVER = ('chat.freenode.net', 6667)
IRC_MISSION_SERVER_PRETTYNAME = 'Freenode'
IRC_MISSION_CHANNEL = '#oh-ircmission-test'
IRC_MISSIONBOT_NICK = 'oh_bottest'
IRC_MISSIONBOT_REALNAME = 'OpenHatch Mission Bot'

# the most recent git commit hash, included in the main page footer for bug
# reporting/debugging
try:
    COMMIT_HASH = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                              stdout=subprocess.PIPE).stdout.read().strip()
except OSError: # git not found on system path
    COMMIT_HASH = None
