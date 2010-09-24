# Django settings for cals project.

import sys, os

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(SITE_ROOT, 'env'))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Kaleissin', 'kaleissin@gmail.com'), # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'GMT'
#TIME_ZONE = 'Europe/Oslo'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = SITE_ROOT + '/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
#    'django.template.loaders.filesystem.load_template_source',
#    'django.template.loaders.app_directories.load_template_source',
##     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'CALS.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    SITE_ROOT + '/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.flatpages',
    'translations',
    'cals',
    'tagging',
    'countries',
#    'profiles',

    'nano.blog',
    'nano.user',
#    'nano.web20',
    'nano.link',
    'nano.badge',
    'nano.faq',
    'nano.privmsg',
    'nano.comments',

    'relay',
)

#AUTHENTICATION_BACKENDS = (
#         'django.contrib.auth.backends.ModelBackend',
##        'cals.auth.backends.LibrarythingBackend',
##        'openid_auth.models.openidbackend',
#)
AUTH_PROFILE_MODULE = 'cals.Profile'

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/logged_in'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

INTERNAL_IPS = ('127.0.0.1', '158.38.62.153',)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

FORCE_LOWERCASE_TAGS = True


# Nano-settings
NANO_LOG_FILE = '/tmp/cals.log'
NANO_USER_EMAIL_SENDER = 'kaleissin@gmail.com'

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
        'file_insertion_enabled': 0,
        'raw_enabled': 0,
        '_disable_config': 1}

import logging, logging.handlers
LOG_FORMAT = '%(asctime)s %(name)s %(pathname)s:%(lineno)d %(levelname)s %(message)s'
LOG_FILE = '/var/log/cals.log'
LOG_LEVEL = logging.DEBUG

_logger = logging.getLogger('')
_log_formatter = logging.Formatter(LOG_FORMAT)
_log_handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='D', backupCount=30)
_log_handler.setFormatter(_log_formatter)
_logger.addHandler(_log_handler)
_logger.setLevel(LOG_LEVEL)
_logger.info('Set up logging for CALS')


try:
    from localsettings import *
except ImportError:
    pass
