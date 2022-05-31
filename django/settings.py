"""
Django settings for odruz project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import ast
from django.utils.translation import ugettext_lazy as _
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from config import (
    ALLOWED_HOSTS,
    DEBUG,
    WSGI_APPLICATION,
    DB_SEARCH_ENABLED,
    ES_URL,
    SENTRY_DSN,
    DATABASES,
    CACHES,
    LOGPIPE,
    CELERY_BROKER_URL
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')y!&9ju7gggggggggggg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = DEBUG
ALLOWED_HOSTS = ALLOWED_HOSTS
AUTH_USER_MODEL = "account.User"

def get_bool_from_env(name, default_value):
    if name in os.environ:
        value = os.environ[name]
        try:
            return ast.literal_eval(value)
        except ValueError as e:
            raise ValueError('{} is an invalid value for {}'.format(value, name))(e)
    return default_value


# Application definition

INSTALLED_APPS = [
    'account',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    'uom',
    'refs',
    'core',
    'manufacture',
    'search',
    'products',
    'content',
    'plans',
    'store',
    'customer',
    'store_products',
    'order',
    'store_shipping',
    'offer',
    'store_content',
    'developer',
    'delivery_boy',
    'help',
    'analytics',

    #external
    'graphene_django',
    'django_celery_results',
    'versatileimagefield',
    'corsheaders',
    'simple_history',
    'logpipe',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',

]

ROOT_URLCONF = 'odruz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = WSGI_APPLICATION

#Graphene
GRAPHENE = {
    'SCHEMA': 'django.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# SEARCH CONFIGURATION
DB_SEARCH_ENABLED = DB_SEARCH_ENABLED

# support deployment-dependant elastic enviroment variable
# ES_URL = (
#     os.environ.get('ELASTICSEARCH_URL')
#     or os.environ.get('SEARCHBOX_URL')
#     or os.environ.get('BONSAI_URL'))
ES_URL = ES_URL
ENABLE_SEARCH = bool(ES_URL) or DB_SEARCH_ENABLED  # global search disabling
SEARCH_BACKEND = 'search.backend.postgresql'

if ES_URL:
    SEARCH_BACKEND = 'search.backend.elasticsearch'
    INSTALLED_APPS.append('django_elasticsearch_dsl')
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ES_URL}}


#SENTRY
# SENTRY_DSN = os.environ.get('SENTRY_DSN')
SENTRY_DSN = SENTRY_DSN
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()]
    )
    # INSTALLED_APPS.append('raven.contrib.django.raven_compat')
    # RAVEN_CONFIG = {
    #     'dsn': SENTRY_DSN,
    #     'release': __version__}


# ENABLE_SILK = get_bool_from_env('ENABLE_SILK', False)
ENABLE_SILK = True
if ENABLE_SILK:
    MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')
    INSTALLED_APPS.append('silk')


#Authentication

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]


#Cache
CACHES = CACHES

# Kafka channel
LOGPIPE = LOGPIPE


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = DATABASES

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


#Image storage

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'products': [
        ('product_gallery', 'thumbnail__540x540'),
        ('product_gallery_2x', 'thumbnail__1080x1080'),
        ('product_small', 'thumbnail__60x60'),
        ('product_small_2x', 'thumbnail__120x120'),
        ('product_list', 'thumbnail__255x255'),
        ('product_list_2x', 'thumbnail__510x510')],
    'default_image': [
        ('product_gallery', 'thumbnail__540x540'),
        ('product_gallery_2x', 'thumbnail__1080x1080'),
        ('product_small', 'thumbnail__60x60'),
        ('product_small_2x', 'thumbnail__120x120'),
        ('product_list', 'thumbnail__255x255'),
        ('product_list_2x', 'thumbnail__510x510')],
    'background_images': [
        ('header_image', 'thumbnail__1080x440')]}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    'create_images_on_demand': get_bool_from_env(
        'CREATE_IMAGES_ON_DEMAND', DEBUG),
}

PLACEHOLDER_IMAGES = {
    60: 'images/placeholder60x60.png',
    120: 'images/placeholder120x120.png',
    255: 'images/placeholder255x255.png',
    540: 'images/placeholder540x540.png',
    1080: 'images/placeholder1080x1080.png'}

DEFAULT_PLACEHOLDER = 'images/placeholder255x255.png'


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
LANGUAGES = (
    ('en', _("English")),
    ('en-us', _("US English")),
    ('it', _('Italian')),
    ('nl', _('Dutch')),
    ('fr', _('French')),
    ('es', _('Spanish')),
)

PARLER_DEFAULT_LANGUAGE_CODE = 'en'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

MEDIA_URL = '/media/'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]

#Celery

# CELERY_BROKER_URL = os.environ.get(
#     'CELERY_BROKER_URL', os.environ.get('CLOUDAMQP_URL')) or ''
CELERY_TASK_ALWAYS_EAGER = not CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_IMPORTS = (
    'order.tasks',
    'content.utils.thumbnails',
    'developer.utils.thumbnails',
    'products.utils.thumbnails',
    'store.utils.thumbnails',
    'store_content.utils.thumbnails',
    'store_products.tasks'
)

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (

)
CORS_ORIGIN_REGEX_WHITELIST = (

)