import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

ALLOWED_HOSTS = [
    '.herokuapp.com',
]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '..', 'debug.log'),
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'soundproof.middleware.exception_logger': {
            'handlers': ['file','console',],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file','console',],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': True,
        },
        'django': {
            'handlers': ['file','console',],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dc35jkpjsiivm1',
        'USER': 'bqdmwfasgvojtm',
        'PASSWORD': 'pXT66vmVWAi0XC9wnIjBXEdlC2',
        'HOST': 'ec2-23-21-140-156.compute-1.amazonaws.com',
        'PORT': '5432',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

AWS = {
    'REGION': 'ap-southeast-2',
    'AWS_ACCESS_KEY_ID': 'AKIAIMCJ263SF5JO5PHA',
    'AWS_SECRET_ACCESS_KEY': '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',
}

STORES = {
    'image': {
        'region': 's3-{}'.format(AWS['REGION']),
        'bucket': 'soundproof-images-heroku',
        'kvstore': {
            'path': 's3://soundproof-images-heroku',
            'host': 's3-ap-southeast-2.amazonaws.com',
        }
    },
}

INSTAGRAM_ID='94b19564477e428792b9913f22fe969a'
INSTAGRAM_SECRET='258d59a978c943a0b62b904c86f219e9'
INSTAGRAM_VERIFY_TOKEN='1588538786.94b1956.835bd997d8b04452a2b5b6f7ed9f7002'

CACHE_KEY_INSTAGRAM_UPDATE='instagram-tags'
CACHE_KEY_INSTAGRAM_HISTORIC_SCRAPE='instagram-historic-scrape'
CACHE_KEY_SEED_DISPLAY='display-seed'
CACHE_TIMEOUT=3600

INSTAGRAM_ENABLE_HISTORIC_SCRAPE=True
INSTAGRAM_ENABLE_SUBSCRIPTIONS=True

FETCH_FOLLOWERS=True

#for django-storages
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
#duplicate these for django-storages
AWS_ACCESS_KEY_ID = AWS['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = AWS['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = STORES['image']['bucket']
#end django-storages
