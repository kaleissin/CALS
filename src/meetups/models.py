from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse_lazy

from verification.generators import Registry


from .generators import CALSGenerator

class Meetup(models.Model):
    keygroup = models.ForeignKey('verification.KeyGroup')
    badge = models.ForeignKey('badge.Badge')
    valid_from = models.DateField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse_lazy('meetup-activate', kwargs={'group': self.keygroup.name})


registry = Registry()
registry.register('cals', CALSGenerator)
