# Django settings for cals project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Kaleissin', 'kaleissin@gmail.com'), # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'
#TIME_ZONE = 'Europe/Oslo'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/home/django-media/CALS/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://media.aldebaaran.uninett.no/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = 'http://media.aldebaaran.uninett.no/admin/'

# Make this unique, and don't share it with anybody.

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'CALS.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/home/django-sites/CALS/templates/',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.flatpages',
    'django.contrib.comments',
    'translation',
    'cals',
    'tagging',
    'countries',
#    'profiles',
    'nano.blog',
    'nano.user',
#    'nano.web20',
    'webalizer',
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
    'django.core.context_processors.request'
)

INTERNAL_IPS = ('127.0.0.1', '158.38.62.153',)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Application-specific

#The trust root to use for OpenID requests
#OPENID_TRUST_ROOT = [The host of the request]

#The host to handle the response from the OpenID server
#OPENID_RETURN_HOST = [The host of the request]

#Setting to turn off OpenID iNames
#OPENID_DISALLOW_INAMES = False

#The CSS class to use for the openid_url form field
#LOGIN_OPENID_URL_CLASS = 'openid'


FORCE_LOWERCASE_TAGS = True


# Nano-settings
NANO_LOG_FILE = '/tmp/cals.log'
NANO_USER_EMAIL_SENDER = 'calsbot@gmail.com'

# Webalizer
WEBALIZER_DIR = '/home/www/webalizer/CALS/'
