from __future__ import unicode_literals

from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cals',
        'USER': 'cals',
    }
}

INSTALLED_APPS += (
    'django_extensions',
)

SECRET_KEY = 'iGDBpnD9F;*sxvbg4)qTMPJ0;zKL@#UXsavF:Zs:7e*:TeUd5n'
