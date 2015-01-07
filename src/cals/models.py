
# -*- coding: UTF-8 -*-

import logging
_LOG = logging.getLogger(__name__)

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from django.utils.timezone import now as tznow

from cals import markup_as_restructuredtext

from cals.language.models import ExternalInfo

from cals.people.models import Profile

from cals.language.models import Language

from phonemes.models import Sound


def add_filter(queryset, **kwargs):
    return queryset.filter(**kwargs)

def add_exclude(queryset, **kwargs):
    return queryset.exclude(**kwargs)

def with_args(qs, keyword, *values):
    for v in values:
        qs = add_filter(qs, **{keyword: v})
    return qs

def without_args(qs, keyword, *values):
    for v in values:
        qs = add_exclude(qs, **{keyword: v})
    return qs

# Glue models

class SoundDataPointQuerySet(models.query.QuerySet):

#     def all_dental(self):
#         return self.filter(features__name__startswith='dental')
# 
#     def all_alveolar(self):
#         return self.filter(features__name__endswith='alveolar')
# 
#     def dental(self):
#         return self.filter(features__name='dental')
# 
#     def alveolar(self):
#         return self.filter(features__name='alveolar')
# 
    def vowels(self):
        return self.filter(sound__features__name='vowel')

    def consonants(self):
        return self.exclude(sound__features__name='vowel').exclude(sound__features__name='diphthong')

    def with_features(self, *features):
        return with_args(self, 'sound__features__name', *features)

    def without_features(self, *features):
        return without_args(self, 'sound__features__name', *features)

class SoundDataPointManager(models.Manager):
    def get_queryset(self):
        return SoundDataPointQuerySet(self.model)

#     def all_dental(self):
#         return self.get_queryset().all_dental()
# 
#     def all_alveolar(self):
#         return self.get_queryset().all_alveolar()
# 
    def vowels(self):
        return self.get_queryset().vowels()

    def consonants(self):
        return self.get_queryset().vowels()

    def with_features(self, *features):
        return self.get_queryset().with_features(*features)

    def without_features(self, *features):
        return self.get_queryset().without_features(*features)

class VowelDataPointManager(SoundDataPointManager):

    def get_queryset(self):
        return SoundDataPointQuerySet(self.model).vowels()

class ConsonantDataPointManager(SoundDataPointManager):

    def get_queryset(self):
        return SoundDataPointQuerySet(self.model).consonants()

class SoundDataPoint(models.Model):
    language = models.ForeignKey(Language)
    sound = models.ForeignKey(Sound)
    changed = models.DateTimeField(default=tznow)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    objects = SoundDataPointManager()
    vowels = VowelDataPointManager()
    consonants = ConsonantDataPointManager()

    class Meta:
        app_label = "cals"

    def save(self, *args, **kwargs):
        self.changed = tznow()
        return super(SoundDataPoint, self).save(self, *args, **kwargs)

    def __unicode__(self):
        return u"%s %s" % (self.sound, self.language)

