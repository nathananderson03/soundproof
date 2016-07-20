
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'soundproof_feed',
        'USER': 'root',
        'PASSWORD': '',
    }
}

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

CACHE_KEY_INSTAGRAM_UPDATE = 'instagram-tags'
CACHE_KEY_INSTAGRAM_HISTORIC_SCRAPE = 'instagram-historic-scrape'
CACHE_KEY_SEED_DISPLAY = 'display-seed'
CACHE_TIMEOUT=3600

INSTAGRAM_ENABLE_HISTORIC_SCRAPE=True
INSTAGRAM_ENABLE_SUBSCRIPTIONS=True

PRINTER_ENABLED=True
PRINTER_NAME='Canon_CP910_2'
PRINT_DPI=(300,300,)
PRINT_SIZE_INCHES=(4,6,)

PRINTER_SELPHY_PRINTER_IP="10.0.0.118"
PRINTER_USE_LPR=False
