# -*- coding: UTF-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

import logging
_LOG = logging.getLogger(__name__)

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from cals.tools.models import DescriptionMixin

from cals.feature.models import FeatureValue, Feature

from cals.language.models import Language

__all__ = ['LanguageFeature']


class LanguageFeatureQuerySet(models.query.QuerySet):
    def for_natlangs(self):
        return self.filter(language__natlang=True)

    def for_conlangs(self):
        return self.filter(language__natlang=False)

    def count_all(self):
        return self.count()

    def count_both(self):
        natlangs = self.for_natlangs().count()
        conlangs = self.for_conlangs().count()
        return (conlangs, natlangs)


class LanguageFeatureManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return LanguageFeatureQuerySet(self.model)

    def for_natlangs(self):
        return self.get_queryset().for_natlangs()

    def for_conlangs(self):
        return self.get_queryset().for_conlangs()

    def count_all(self):
        return self.get_queryset().count_all()

    def count_both(self):
        return self.get_queryset().count_both()


@python_2_unicode_compatible
class LanguageFeature(models.Model, DescriptionMixin):
    language = models.ForeignKey(Language, related_name='features')
    feature = models.ForeignKey(Feature, related_name='languages')
    value = models.ForeignKey(FeatureValue, related_name='languages')

    objects = LanguageFeatureManager()

    class Meta:
        unique_together = ('language', 'feature')
        db_table = 'cals_languagefeature'
        app_label = 'cals'

    def __str__(self):
        return "%s / %s / %s" % (self.language, self.feature, self.value)

    def natural_key(self):
        return (self.language.slug, self.feature)
