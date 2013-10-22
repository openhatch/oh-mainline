from settings import *

FORCE_SCRIPT_NAME = 'demo'
MEDIA_URL = '/' + FORCE_SCRIPT_NAME + '/static/'
STATIC_DOC_ROOT = FORCE_SCRIPT_NAME + '/static/'
LOGIN_URL = '/' + FORCE_SCRIPT_NAME + '/account/login/'
