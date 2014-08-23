from __future__ import unicode_literals

from django.db import IntegrityError

from verification.generators import Registry


from .generators import CALSGenerator

registry = Registry()
registry.register('cals', CALSGenerator)

