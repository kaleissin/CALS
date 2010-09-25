
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

from cals.feature.models import FEATURE_GROUPS_CHOICES, Category, Feature, FeatureValue

from cals.language.models import LanguageFamily, LanguageName, WALSCode, Language

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

from signalhandlers import new_or_changed_language, new_user_anywhere

post_save.connect(new_user_anywhere, sender=User)
#post_save.connect(new_or_changed_language, sender=Language)
