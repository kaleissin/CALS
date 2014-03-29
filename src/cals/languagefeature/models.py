# -*- coding: UTF-8 -*-

import logging
_LOG = logging.getLogger(__name__)

from django.db import models

from cals.tools.models import DescriptionMixin

from cals.feature.models import FeatureValue, Feature

from cals.language.models import Language

__all__ = ['LanguageFeature']

class LanguageFeature(models.Model, DescriptionMixin):
    language = models.ForeignKey(Language, related_name='features')
    feature = models.ForeignKey(Feature, related_name='languages')
    value = models.ForeignKey(FeatureValue, related_name='languages')

    objects = models.Manager()

    class Meta:
        unique_together = ('language', 'feature')
        db_table = 'cals_languagefeature'
        app_label = 'cals'

    def __unicode__(self):
        return u"%s / %s / %s" % (self.language, self.feature, self.value)

