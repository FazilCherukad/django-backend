

ALLOWED_HOSTS = ['192.168.43.54', '127.0.0.1', 'localhost', '192.168.157.251', '192.168.100.100']
ES_URL = 'http://localhost:9200/'
SENTRY_DSN = "https://5xxx6@sentry.io/1504088"
MEMCACHED_LOCATION = '127.0.0.1:11211'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': MEMCACHED_LOCATION,
    }
}

TEXT_LOCAL_API_KEY = "um8/jdjkskskskkkkkkk"
TEXT_LOCAL_SENDER_ID = "xxx"

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'db',
        'USER': 'dbuser',
        'PASSWORD': 'dbpass',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
WSGI_APPLICATION = 'django.wsgi.application'
DB_SEARCH_ENABLED = True
CELERY_BROKER_URL = 'amqp://localhost'

LOGPIPE = {
    # Required Settings
    'OFFSET_BACKEND': 'logpipe.backend.kafka.ModelOffsetStore',
    'CONSUMER_BACKEND': 'logpipe.backend.kafka.Consumer',
    'PRODUCER_BACKEND': 'logpipe.backend.kafka.Producer',
    'KAFKA_BOOTSTRAP_SERVERS': [
        'kafka:9092'
    ],
    'KAFKA_CONSUMER_KWARGS': {
        'group_id': 'django-logpipe',
    },

    # Optional Settings
    # 'KAFKA_SEND_TIMEOUT': 10,
    # 'KAFKA_MAX_SEND_RETRIES': 0,
    # 'MIN_MESSAGE_LAG_MS': 0,
    # 'DEFAULT_FORMAT': 'json',
}

ONESIGNAL_APP_ID = "signal_id"
ONESIGNAL_REST_API_KEY = "api"
ONESIGNAL_USER_AUTH_KEY = "api"
