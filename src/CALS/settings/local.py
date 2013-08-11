from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cals',
        'USER': 'cals',
    }
}

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)

SECRET_KEY = 'iGDBpnD9F;*sxvbg4)qTMPJ0;zKL@#UXsavF:Zs:7e*:TeUd5n'
