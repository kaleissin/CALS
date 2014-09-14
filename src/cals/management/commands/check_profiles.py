from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

from cals.models import *

class Command(NoArgsCommand):
    def handle_noargs(self, **kwargs):
        for u in User.objects.all():
            try:
                p = u.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=u)
                print 'Created profile for:', u

