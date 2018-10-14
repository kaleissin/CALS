from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import NoArgsCommand
from django.contrib.auth import get_user_model

from cals.models import *


class Command(NoArgsCommand):
    def handle_noargs(self, **kwargs):
        User = get_user_model()
        for u in User.objects.all():
            try:
                p = u.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=u)
                print('Created profile for:', u)
