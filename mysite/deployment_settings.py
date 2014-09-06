# This settings file contains custom settings used for the
# main OpenHatch deployment.
#
# The live site needs some slightly different settings.
#
# So we start by loading the settings module in the same directory...
from settings import *
# ...and then we override some values.

# Use MySQL in production
DATABASES['default'] = OTHER_DATABASES['mysql']
# But use the linode as our MySQL server
DATABASES['default']['HOST'] = 'linode.openhatch.org'

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

CELERY_ALWAYS_EAGER = False  # srsly

# always use memcached on linode-one, also
CACHE_BACKEND = "memcached://linode.openhatch.org:11211/?timeout=1"

GOOGLE_ANALYTICS_CODE = 'UA-15096810-1'

SVN_REPO_URL_PREFIX = 'svn://svn-mission.openhatch.org/'
GIT_REPO_URL_PREFIX = 'https://openhatch.org/git-mission-data/git/'
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

ALLOWED_HOSTS=['testserver', 'openhatch.org']

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
EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = 25
