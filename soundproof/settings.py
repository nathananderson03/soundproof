"""
Django settings for soundproof project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
from __future__ import absolute_import, print_function

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

from django.conf import global_settings

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'xknz+ykx8yiub^vv-8i#9d%p^undw3zpfm1+zl2*t&szzu#sw$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

TEMPLATE_LOADERS = global_settings.TEMPLATE_LOADERS + (
    'apptemplates.Loader',
)

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'soundproof',
    'storages',
    'microsite',
    'colorful',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'soundproof.middleware.exception_logger.ExceptionLogger',
)

ROOT_URLCONF = 'soundproof.urls'

WSGI_APPLICATION = 'soundproof.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

# see site_settings.py

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Melbourne'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = 'soundproof/staticfiles'
STATICFILES_DIRS = (
    os.path.abspath(os.path.join(BASE_DIR, 'soundproof', 'static')),
    os.path.abspath(os.path.join(BASE_DIR, 'assets')),
)

SITE_ID = 1
LOGIN_URL = '/admin/login/'

CACHES = {
    'default':{
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    },
}

AWS = {
    'AWS_ACCESS_KEY_ID': 'AKIAIMCJ263SF5JO5PHA',
    'AWS_SECRET_ACCESS_KEY': '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',
}

STORES = {
    'image': {
        'region': 's3-ap-southeast-2',
        'bucket': 'soundproof-images',
        'kvstore': {
            'path': 's3://soundproof-images',
            'host': 's3-ap-southeast-2.amazonaws.com',
        }
    },
    # for testing
    #'image': {
    #    'fs_path': '/static/images',
    #    'kvstore': {
    #        'path': 'file://~/Workspace/soundproof-hashtag-feed/soundproof/static/images',
    #    },
    #},
}

INSTAGRAM_ID = '72ce3f8050fb437c96aa81807fe93a9a'
INSTAGRAM_SECRET = 'c6ed6bebf82c497696e065111e92532f'
INSTAGRAM_VERIFY_TOKEN = 'PNMJ9d0n7EnjVM5CmW2j'

INSTAGRAM_HISTORIC_IMAGE_COUNT = 50

CACHE_KEY_INSTAGRAM_UPDATE = 'instagram-tags'
CACHE_KEY_INSTAGRAM_HISTORIC_SCRAPE = 'instagram-historic-scrape'
CACHE_KEY_SEED_DISPLAY = 'display-seed'
CACHE_TIMEOUT=3600

INSTAGRAM_ENABLE_HISTORIC_SCRAPE=True
INSTAGRAM_ENABLE_SUBSCRIPTIONS=False

PRINTER_ENABLED=True
if os.environ.get('PRINTER', 'ds40') == 'selphy':
    PRINTER_NAME='Selphys'
    PRINTER_OPTIONS=[
        # this is a paper size specified in /etc/cups/ppd/<printer name>
        '-o media=Postcard.Fullbleed',
        # scale the image to fit
        '-o fit-to-page',
    ]
    PRINTER_SELPHY_PRINTER_IP="10.0.0.118"
else:
    PRINTER_NAME='Dai_Nippon_Printing_DS40'
    PRINTER_OPTIONS=[]
PRINT_DPI=(300,300,)
PRINT_SIZE_INCHES=(4,6,)
PRINTER_USE_LPR=True

USE_PIL = False

REFRESH_INSTAGRAM_IMAGE_FREQUENCY = 60*60*24
REFRESH_INSTAGRAM_USER_FREQUENCY = 60*60*24
LOG_ENGAGEMENT_FREQUENCY = 60*15

# allow loading of specific settings files
# must be in full import name, ie 'soundproof.site_settings'
if 'SOUNDPROOF_SITE_SETTINGS' in os.environ:
    ss = __import__(os.environ['SOUNDPROOF_SITE_SETTINGS'], fromlist=['*'])
    for name in dir(ss):
        globals()[name] = getattr(ss, name)
else:
    try: from .site_settings import *
    except: pass


# set our AWS variables
if 'AWS' in globals():
    if 'AWS_ACCESS_KEY_ID' not in os.environ:
        os.environ['AWS_ACCESS_KEY_ID'] = AWS['AWS_ACCESS_KEY_ID']
    if 'AWS_SECRET_ACCESS_KEY' not in os.environ:
        os.environ['AWS_SECRET_ACCESS_KEY'] = AWS['AWS_SECRET_ACCESS_KEY']
