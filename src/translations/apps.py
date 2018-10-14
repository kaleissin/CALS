from __future__ import absolute_import
from __future__ import unicode_literals

from django.apps import AppConfig


class TranslationConfig(AppConfig):
    name = 'translations'

    def ready(self):
        # -- actstream
        from actstream import registry

        registry.register(self.get_model('Translation'))

        # -- signals

        from translations.signalhandlers import new_translation

        from django.db.models.signals import post_save

        post_save.connect(new_translation, sender='translations.Translation', dispatch_uid='new_translation')
