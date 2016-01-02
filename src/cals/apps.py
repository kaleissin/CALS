from __future__ import absolute_import
from __future__ import unicode_literals

from django.apps import AppConfig
from django.contrib.auth.apps import AuthConfig
from django.conf import settings

from actstream import registry

__ALL__ = [
    'DjangoContribAuthConfig',
]

class DjangoContribAuthConfig(AuthConfig):

    def ready(self):
        super(DjangoContribAuthConfig, self).ready()
        user_model_string = settings.AUTH_USER_MODEL.rsplit('.', 1)[1]
        registry.register(self.get_model(user_model_string))

class CalsConfig(AppConfig):
    name = "cals"
    verbose_name = "CALS"

    def ready(self):
        registry.register(self.get_model('Language'))

        from django.db.models.signals import post_save

        from nano.user import new_user_created

        import cals.signalhandlers

        from cals.people.models import user_unlurked
        from cals.signalhandlers import (
            new_or_changed_language,
            new_user_anywhere,
            user_now_active
        )
        user_unlurked.connect(user_now_active, sender='cals.Profile',
            dispatch_uid='user-unlurked')
        post_save.connect(new_user_anywhere,
            sender=settings.AUTH_USER_MODEL, dispatch_uid='new-user')
        post_save.connect(new_or_changed_language,
            sender='cals.Language', dispatch_uid='language-update')
