from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
import django.dispatch

from nano.countries.models import Country

from cals.tools import uslugify

# Signals defined here

user_unlurked = django.dispatch.Signal(providing_args=["user"])


class ProfileManager(models.Manager):
    def autobiographers(self):
        return self.get_queryset().exclude(
                country__isnull=True, 
                homepage_title__isnull=True,
                latitude__isnull=True, 
                longitude__isnull=True).exclude(
                Q(homepage__isnull=True) | Q(homepage_title='')
        )


@python_2_unicode_compatible
class Profile(models.Model):
# TODO: change date-format on profile-page, needs new date-filter
#     CHOICE_DATE = datetime(2008, 5, 1, 14, 0, 0, 7, UTC())
#     DATE_FORMAT_CHOICES = (
#             ('Y-m-d H:i O', CHOICE_DATE.isoformat),
#             ('Y-m-d H:i O', CHOICE_DATE.),
#             ('r', ''),
#             )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', primary_key=True)
    #user = models.ForeignKey(settings.AUTH_USER_MODEL, unique=True, related_name='profile', primary_key=True)
    # Denormalization of django.contrib.auth.models.User - allows public
    # backup of database without exposing passwords and email-addresses
    username = models.CharField(max_length=30, unique=True, editable=False)
    display_name = models.CharField(max_length=32, blank=True, null=True,
            help_text="Replaces username everywhere but in urls.")
    slug = models.SlugField(max_length=64, unique=True, editable=False)
    show_username = models.NullBooleanField('Always show username',
            help_text="Show username everywhere, even if display name "
            "have been set.")
    homepage = models.URLField(blank=True, null=True)
    homepage_title = models.CharField(max_length=64, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True)
    native_tongue = models.ForeignKey('Language', null=True, blank=True,
            help_text="If your L1 is not in the list, or you are multilingual, don't select anything.")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    altitude = models.IntegerField(blank=True, null=True, default=0)
    date_format = models.CharField(max_length=16, default="Y-m-d H:i O")
    is_visible = models.BooleanField(default=True)
    is_lurker = models.BooleanField(default=True)
    seen_profile = models.BooleanField(default=False, editable=False)
    seen_ipv6 = models.DateTimeField(null=True, editable=False)

    objects = ProfileManager()

    class Meta:
        ordering = ('display_name',)
        db_table = 'cals_profile'
        app_label = 'cals'

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.username = self.user.username
        self.slug = uslugify(self.username)
        if not self.display_name:
            self.display_name = self.username
#         if not self.show_username:
#             full_name = '%s %s' % (self.user.first_name.strip(), self.user.last_name.strip())
#             self.display_name = full_name.strip() or self.user.username
        super(Profile, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return "/people/%s/" % self.user.id

#     def twittername(self):
#         twitteraccounts = self.user.web20.filter(type='Twitter')
#         if twitteraccounts:


#     def get_absolute_url(self):
#         return ('profiles_profile_detail', (), { 'username': self.user.username })
#     get_absolute_url = models.permalink(get_absolute_url)
