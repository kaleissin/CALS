from __future__ import unicode_literals

from django.db import models

from verification.generators import Registry


from .generators import CALSGenerator

class Meetup(models.Model):
    keygroup = models.ForeignKey('verification.KeyGroup')
    badge = models.ForeignKey('badge.Badge')
    valid_from = models.DateField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)

registry = Registry()
registry.register('cals', CALSGenerator)
