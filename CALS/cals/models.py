
# -*- coding: UTF-8 -*-

import datetime as dt
from datetime import datetime

import logging
_LOG = logging.getLogger(__name__)

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_unicode

from tagging.fields import TagField

from cals import markup_as_restructuredtext
from cals.tools import uni_slugify, asciify, next_id

from cals.tools.models import Description, DescriptionMixin, FREETEXT_TYPES

from cals.people.models import Profile

from cals.feature.models import FEATURE_GROUPS_CHOICES, Category, FeatureValue, Feature

from cals.language.models import LanguageFamily, LanguageName, WALSCode, Language

from phonemes.models import Sound

# Glue models 

class LanguageFeature(models.Model, DescriptionMixin):
    language = models.ForeignKey(Language, related_name='features')
    feature = models.ForeignKey(Feature, related_name='languages')
    value = models.ForeignKey(FeatureValue, related_name='languages') #, related_name='languages')

    objects = models.Manager()

    class Meta:
        unique_together = ('language', 'feature')
        db_table = 'cals_languagefeature'

    def __unicode__(self):
        return u"%s / %s / %s" % (self.language, self.feature, self.value)

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
    def get_query_set(self):
        return SoundDataPointQuerySet(self.model)

#     def all_dental(self):
#         return self.get_query_set().all_dental()
# 
#     def all_alveolar(self):
#         return self.get_query_set().all_alveolar()
# 
    def vowels(self):
        return self.get_query_set().vowels()

    def consonants(self):
        return self.get_query_set().vowels()

    def with_features(self, *features):
        return self.get_query_set().with_features(*features)

    def without_features(self, *features):
        return self.get_query_set().without_features(*features)

class VowelDataPointManager(SoundDataPointManager):

    def get_query_set(self):
        return SoundDataPointQuerySet(self.model).vowels()

class ConsonantDataPointManager(SoundDataPointManager):

    def get_query_set(self):
        return SoundDataPointQuerySet(self.model).consonants()

class SoundDataPoint(models.Model):
    language = models.ForeignKey(Language)
    sound = models.ForeignKey(Sound)
    changed = models.DateTimeField(default=datetime.now)
    changed_by = models.ForeignKey(User)

    objects = SoundDataPointManager()
    vowels = VowelDataPointManager()
    consonants = ConsonantDataPointManager()

    class Meta:
        app_label = "cals"

    def save(self, *args, **kwargs):
        self.changed = datetime.now()
        return super(SoundDataPoint, self).save(self, *args, **kwargs)

    def __unicode__(self):
        return u"%s %s" % (self.sound, self.language)

# TODO: Generalize. move out to own module. in nano?

class UTC(dt.tzinfo):
    ZERO = dt.timedelta(0)
    """UTC"""
    def tzname(self, dt):
        return "UTC"
    def utcoffset(self, dt):
        return self.ZERO
    def dst(self, dt):
        return self.ZERO

# TODO: Generalize. move out to own module. in nano?

class ExternalInfo(models.Model):
    EXTERNALINFO_TYPES = (
            ('homepage', 'Homepage'),
            ('dictionary', 'Dictionary'),
    )

    language = models.ForeignKey(Language, related_name='externalinfo')
    category = models.CharField(max_length=20,
            choices=EXTERNALINFO_TYPES)
    on_request = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return u"%s %s: on request: %s, link: %s" % (self.language,
                self.category, self.on_request, self.link or 'No')

# --- Signals
from django.db.models.signals import post_save
from nano.user import new_user_created

from cals.people.models import user_unlurked
from signalhandlers import new_or_changed_language, new_user_anywhere, user_now_active

user_unlurked.connect(user_now_active, sender=Profile)
post_save.connect(new_user_anywhere, sender=User)
#post_save.connect(new_or_changed_language, sender=Language)
