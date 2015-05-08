from .base import *

# What environment are we in?
ENVIRONMENT = get_environment(__file__)

config = get_json_config(ENVIRONMENT)

# Sets SECRET_KEY, DATABASES, various EMAIL
# XXX This should use unification
for setting, value in config.items():
    locals()[setting] = value

# Set in config-file:
# * ALLOWED_HOSTS
# * DATABASES
# * SECRET_KEY

# Rather important

DEBUG = False
TEMPLATE_DEBUG = DEBUG

########## IN-MEMORY TEST DATABASE
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}

