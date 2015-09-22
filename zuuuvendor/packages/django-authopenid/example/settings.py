# -*- coding: utf-8 -*-
import os, platform

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
        ('Benoit Chesneau', 'bchesneau@gmail.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3' 
DATABASE_NAME = 'test.db'

TIME_ZONE = 'Europe/Paris'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1
USE_I18N = True

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'static')

MEDIA_URL = '/media'

ADMIN_MEDIA_PREFIX = '/media/admin/'

ugettext = lambda s: s
LOGIN_URL = '/%s%s' % (ugettext('account/'), ugettext('signin/'))

SECRET_KEY = 'a1wyygkm7g&6u3xx47ohe&4yh^47w39wr0$73jq9_y*59-=mt&'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django_authopenid.context_processors.authopenid',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django_authopenid.middleware.OpenIDMiddleware',
)

ROOT_URLCONF = 'example.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 10

OPENID_SREG = {
    "required": ['fullname', 'country']
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'registration',
    'django_authopenid',
)
