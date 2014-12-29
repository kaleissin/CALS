"""Common settings and globals."""

from os.path import abspath, basename, dirname, join, normpath, splitext, split
from os.path import isfile, getsize
from sys import path
import json, sys, os

# Normally you should not import ANYTHING from Django directly
# into your settings, but ImproperlyConfigured is an exception.
# reverse_lazy() exists to be safe for such use.
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse_lazy


def get_env_setting(setting):
        """ Get the environment setting or return exception """
        try:
                return environ[setting]
        except KeyError:
                error_msg = "Set the %s env variable" % setting
                raise ImproperlyConfigured(error_msg)

def get_json_config(environment):
    # use the first file found
    for location in CONFIG_PATH:
        filename = join(location, SITE_NAME + '.config.json')
        if isfile(filename) and getsize(filename) > 0:
            with file(filename, 'r') as CONFIG:
                config = json.load(CONFIG)
                if environment in config:
                    return config[environment]
    # Maybe raise an error instead?
    return {}

def get_environment(filename):
    return splitext(split(filename)[-1])[0]

# What environment are we in?
ENVIRONMENT = get_environment(__file__)

########## PATH CONFIGURATION
# Absolute filesystem path to the Django project directory:
DJANGO_ROOT = dirname(dirname(abspath(__file__)))

# Absolute filesystem path to the top-level project folder:
SITE_ROOT = dirname(DJANGO_ROOT)

# Path to look for config-files
CONFIG_PATH = ['/etc/django-sites.d', '/usr/local/etc/django-sites.d', SITE_ROOT]

# Site name:
SITE_NAME = basename(DJANGO_ROOT)

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(DJANGO_ROOT)
########## END PATH CONFIGURATION

sys.path.append(os.path.join(SITE_ROOT, 'env'))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Kaleissin', 'kaleissin@gmail.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = SITE_ROOT + '/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = SITE_ROOT + '/static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    DJANGO_ROOT + '/static',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'nano.chunk.loader.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'CALS.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'CALS.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    SITE_ROOT + '/CALS/templates',
)

DJANGO_APPS = (
    'cals.apps.DjangoContribAuthConfig',
#     'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.flatpages',
)

THIRD_PARTY_APPS = (
    'taggit',
    'actstream',
    'social.apps.django_app.default',
)

PROJECT_APPS = (
    'translations',
    'cals',
    'nano.countries',
#    'languages',
    'phonemes',
    'wordlist',

    'verification',

    'nano.blog',
    'nano.badge',
    'nano.mark',
    'nano.comments',
    'nano.chunk',

#    'relay',
    'nano.privmsg',
    'nano.user',
    'nano.faq',
    'meetups',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

AUTH_PROFILE_MODULE = 'cals.Profile'

LOGIN_URL = '/'
LOGIN_ERROR_URL = '/'
LOGIN_REDIRECT_URL = '/logged_in'

AUTHENTICATION_BACKENDS = (
    'social.backends.twitter.TwitterOAuth',
    'social.backends.github.GithubOAuth2',
    'social.backends.open_id.OpenIdAuth',
    'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "django.core.context_processors.tz",
        "django.contrib.messages.context_processors.messages",
        "django.core.context_processors.request",
        "social.apps.django_app.context_processors.backends",
)

INTERNAL_IPS = ['127.0.0.1']

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CACHES = {
    'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
    }
}

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
        'file_insertion_enabled': 0,
        'raw_enabled': 0,
        '_disable_config': 1,
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(name)s %(pathname)s:%(lineno)d %(levelname)s %(message)s',
            'datefmt' : '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'default': {
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'default',
            'filename': '/var/log/cals.log',
        },
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db': {
            'handlers': ['null'],
            'propagate': False,
        },
    },
}

# -- 3rd party settings

FORCE_LOWERCASE_TAGS = True

# Nano-settings
NANO_USER_EMAIL_SENDER = 'kaleissin@gmail.com'
NANO_BLOG_USE_TAGS = True
ACTSTREAM_SETTINGS = {

    'MODELS': ('auth.user', 'cals.language',),
}

# Python Social Auth
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email',]
