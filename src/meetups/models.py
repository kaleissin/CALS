from __future__ import unicode_literals

from datetime import datetime

from random import sample

import pytz

from django.db import models
from django.db.models.loading import get_model
from django.core.urlresolvers import reverse_lazy

from verification.generators import Registry

from .generators import (
    CALSGenerator,
    HexColorGenerator,
    ZeroPaddedNumberGenerator,
    IsoDateGenerator,
)

class Meetup(models.Model):
    keygroup = models.ForeignKey('verification.KeyGroup')
    badge = models.ForeignKey('badge.Badge')
    valid_from = models.DateField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    estimated_number_of_attendees = models.IntegerField(default=0, blank=True, null=True)

    def get_absolute_url(self):
        return reverse_lazy('meetup-activate', kwargs={'group': self.keygroup.name})

    def generate_keys(self):
        Key = get_model('verification', 'Key')
        Generator = self.keygroup.get_generator()
        used_keys = set(Key.objects.filter(
            group__generator=Generator.name
        ).values_list('key', flat=True))
        generator = Generator()
        all_keys = set(generator.generate_all_keys())
        keys = sample(all_keys - used_keys, self.estimated_number_of_attendees)
        expires = datetime.combine(self.valid_until, datetime.max.time())
        for keystring in keys:
            key = Key.objects.create(
                key=keystring,
                group=self.keygroup,
                expires=expires.replace(tzinfo=pytz.utc),
            )


registry = Registry()
registry.register('cals', CALSGenerator)
registry.register('hexcolor', HexColorGenerator)
registry.register('isodate', IsoDateGenerator)
registry.register('zeropaddedpin', ZeroPaddedNumberGenerator)
