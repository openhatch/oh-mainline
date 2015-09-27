# This settings file contains custom settings used for the
# main OpenHatch deployment.
#
# The live site needs some slightly different settings.
#
# So we start by loading the settings module in the same directory...
from settings import *
# ...and then we override some values.

DATABASES = {'default': dj_database_url.config()}

OHLOH_API_KEY = 'SXvLaGPJFaKXQC0VOocAg'
DEBUG = False
ADMINS = [
    ('Private Server Monitoring List',
     'monitoring-private@lists.openhatch.org',)
]

INVITE_MODE = False  # invite codes are disabled everywhere
INVITATIONS_PER_USER = 20

TEMPLATE_DEBUG = False

EMAIL_SUBJECT_PREFIX = '[Kaboom@OH] '

SEND_BROKEN_LINK_EMAILS = False
MANAGERS = ADMINS
SERVER_EMAIL = 'mr_website@linode.openhatch.org'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# Note: POSTFIX_FORWARDER_TABLE_PATH is enabled in the deployment_settings.py
#       while it is disabled by default in settings.py
#       See documentation in advanced_installation.rst for more details
POSTFIX_FORWARDER_TABLE_PATH = '/etc/postfix/virtual_alias_maps'

# always use memcached on linode-one, also
CACHE_BACKEND = "memcached://linode.openhatch.org:11211/?timeout=1"

GOOGLE_ANALYTICS_CODE = 'UA-15096810-1'

# svn mission requires a subdomain svn-mission for cloudflare to
# work properly
SVN_REPO_URL_PREFIX = 'svn://svn-mission.openhatch.org/'
GIT_REPO_URL_PREFIX = 'https://git-mission.openhatch.org/git-mission-data/git/'
# Share cookies with subdomain (necessary for Vanilla)
SESSION_COOKIE_DOMAIN = '.openhatch.org'
URL_PREFIX = 'https://openhatch.org'

RECOMMEND_BUGS = False

# Sessions in database, but cached in memcached if available
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# Set the logging level to just WARNING or above
import logging
logger = logging.getLogger('')
logger.setLevel(logging.WARNING)

# svn-mission subdomain needed in ALLOWED_HOSTS due to cloudflare
ALLOWED_HOSTS=['testserver', 'openhatch.org', 'svn-mission.openhatch.org']

# This means that, when we run 'python manage.py collectstatic'
# on the deployment, that they go in the path below.
#
# This path is important because the nginx
# configuration is consistent with it.
STATIC_ROOT='/home/deploy/milestone-a/mysite/statik'

# In production, we use localhost port 25 SMTP.
#
# settings.py explains how to get email working in
# development via a debugging-oriented SMTP server.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('MAILGUN_SMTP_SERVER', '127.0.0.1')
EMAIL_PORT = os.environ.get('MAILGUN_SMTP_PORT', 25)
EMAIL_HOST_USER = os.environ.get('MAILGUN_SMTP_LOGIN')
EMAIL_HOST_PASSWORD = os.environ.get('MAILGUN_SMTP_PASSWORD')

# This OAuth 2.0 key is controlled by Asheesh, who also
# stores its corresponding secret in the production instance.
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '1083745569348-o11asa1kur096enaq5pt8tq0rff3golt.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ['SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET']

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

INSTALLED_APPS = tuple([x for x in INSTALLED_APPS if 'debug_toolbar' not in x])
