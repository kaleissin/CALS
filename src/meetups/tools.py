from django.db import IntegrityError

from verification.models import KeyGroup

from nano.badge.models import Badge

from .settings import MEETUPS

__all__ = ['setup_keygroups_and_badges']

def setup_keygroups_and_badges():
    for group, setup in MEETUPS.items():
        generator = setup.get('generator', 'cals')
        try:
            KeyGroup.objects.get_or_create(name=group, generator=generator)
        except IntegrityError:
            # .get_or_create isn't supposed to raise IntegrityError
            # Race condition possibly?
            pass
        badge_dict = setup['badge']
        Badge.objects.get_or_create(**badge_dict)
