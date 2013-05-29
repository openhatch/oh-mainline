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
DATABASES['default']['HOST'] ='linode.openhatch.org'

OHLOH_API_KEY='SXvLaGPJFaKXQC0VOocAg'
DEBUG=False
ADMINS=[
    ('Private Server Monitoring List', 'monitoring-private@lists.openhatch.org',)
]

INVITE_MODE=False # Suckas, invite codes are disabled everywarez
INVITATIONS_PER_USER=20

TEMPLATE_DEBUG=False

EMAIL_SUBJECT_PREFIX='[Kaboom@OH] '

SEND_BROKEN_LINK_EMAILS=False
MANAGERS=ADMINS
SERVER_EMAIL='mr_website@linode.openhatch.org'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

POSTFIX_FORWARDER_TABLE_PATH = '/etc/postfix/virtual_alias_maps'

CELERY_ALWAYS_EAGER = False # srsly

### always use memcached on linode-one, also
CACHE_BACKEND = "memcached://linode.openhatch.org:11211/?timeout=1"

GOOGLE_ANALYTICS_CODE='UA-15096810-1'

SVN_REPO_URL_PREFIX = 'svn://openhatch.org/'
GIT_REPO_URL_PREFIX = 'https://openhatch.org/git-mission-data/git/'
SESSION_COOKIE_DOMAIN='.openhatch.org' # Share cookies with subdomain (necessary for Vanilla)
URL_PREFIX='https://openhatch.org'

RECOMMEND_BUGS=False

### Sessions in database, but cached in memcached if available
SESSION_ENGINE="django.contrib.sessions.backends.cached_db"

### Set the logging level to just WARNING or above
import logging
logger = logging.getLogger('')
logger.setLevel(logging.WARNING)
