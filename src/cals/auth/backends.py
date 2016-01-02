from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys
import logging
logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s',
        filename='/tmp/cals.log',
        filemode='a')

from django.conf import settings
from django.contrib.auth.models import User, Group, check_password, SiteProfileNotAvailable
from django.db.models import get_model

logging.info('Starting to log in LibrarythingBackend')
class LibrarythingBackend:
    # http://www.djangoproject.com/documentation/0.96/authentication/#writing-an-authentication-backend
    def authenticate(self, username=None, password=None):
        logging.debug('LibrarythingBackend: authenticating')
        username = '%s' % username.strip()
        password = '%s' % password.strip()
        if not (username and password):
            return None
        valid = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Create a new user.
            user = self._make_user(username, password)
            return user
        if check_password(password, user.password):
            logging.info('Returning user: %s', user)
            return user
        logging.info('Invalid password for user: %s', user)
        return None

    def _make_user(self, username, password, *args, **kwargs):
        "Create a new user"
        logging.info('Making user: %s/%s', username, password)
        # Clean input
        username = '%s' % username.strip()
        password = '%s' % username.strip()
        user = User(username=username)
        user.set_password(password)
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        user.save()
        logging.info('Saved user: %s', user)
        # Profile
        if (not hasattr(settings, 'AUTH_PROFILE_MODULE')) or \
                (not settings.AUTH_PROFILE_MODULE):
            raise SiteProfileNotAvailable
        profile_model = get_model(*settings.AUTH_PROFILE_MODULE.split('.'))
        if profile_model is None:
            raise SiteProfileNotAvailable
        profile = profile_model.objects.create(user=user)
        user.message_set.create(message="You're now registered, as '%s'" % username)
        logging.info("You're now registered, as '%s'", username)
        return user

    def get_user(self, user_id):
        try:
            print('Fetching user with id', user_id)
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

