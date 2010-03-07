from settings import *

OHLOH_API_KEY='SXvLaGPJFaKXQC0VOocAg'
DEBUG=False
ADMINS=[
    ('All OH devs', 'all@openhatch.org'),
]

INVITE_MODE=False # Suckas, invite codes are disabled everywarez
INVITATIONS_PER_USER=20

TEMPLATE_DEBUG=False

EMAIL_SUBJECT_PREFIX='[Kaboom@OH] '

SEND_BROKEN_LINK_EMAILS=True
MANAGERS=ADMINS
SERVER_EMAIL='mr_website@linode.openhatch.org'

CACHE_BACKEND = "memcached://127.0.0.1:11211/?timeout=1"

POSTFIX_FORWARDER_TABLE_PATH = '/etc/postfix/virtual_alias_maps'

try:
    from deployment_settings_secret_keys import GOOGLE_ANALYTICS_CODE
except ImportError:
    pass
