# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import logging
_LOG = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.html import escape
from django.utils.timezone import now as tznow

from cals.tools import uslugify

from cals.language.models import Language

def get_interlinear(model):
    if not model.interlinear.strip():
        return ''
    interlinear = model.interlinear
    format = model.il_format
    if format == 'leipzig':
        try:
            from interlinears.leipzig import InterlinearText
        except ImportError, e:
            assert False, e
            format = 'monospace'
        else:
            il = InterlinearText()
            return il.do_text(interlinear)
    return '<pre>%s</pre>' % escape(interlinear)

class Interlinear(models.Model):
    INTERLINEAR_FORMATS = (
            ('monospace', 'WYSIWYG monospace'),
            ('leipzig', 'Leipzig Glossing Rules'),
    )

    interlinear = models.TextField('Interlinear', blank=True, default='', db_column='il_text')
    il_xhtml = models.TextField('Interlinear, formatted', blank=True, default='', db_column='il_xhtml')
    il_format = models.CharField('Interlinear format', max_length=20, choices=INTERLINEAR_FORMATS, blank=True, default='monospace')

    class Meta:
        abstract = True

    def get_interlinear(self):
        return get_interlinear(self)

    def save(self, **kwargs):
        new_il = self.get_interlinear()
        self.il_xhtml = new_il if new_il else ''
        super(Interlinear, self).save(**kwargs)

class TranslationExerciseCategory(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name_plural = 'translation-exercise categories'
        db_table = 'cals_translationcategory'

    def __unicode__(self):
        return self.name

class TranslationExercise(models.Model):
    name = models.CharField(max_length=64, unique=True,
            help_text="A short name to refer to the translation excrcise")
    slug = models.SlugField(max_length=64, unique=True, editable=False)
    exercise = models.TextField(unique=True)
    comment = models.TextField(blank=True, null=True)
    category = models.ForeignKey(TranslationExerciseCategory,
            related_name='exercises')
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='translation_exercises'
    )
    added = models.DateTimeField(default=tznow, editable=False)

    class Meta:
        db_table = 'cals_translationexercise'
        ordering = ('category', 'slug',)
        get_latest_by = 'added'

    def __unicode__(self):
        return self.name

    def save(self, user=None, **kwargs):
        if not self.id:
            self.slug = uslugify(self.name)
            if user:
                self.added_by = user
            self.added = tznow()
        super(TranslationExercise, self).save(**kwargs)

class TranslationManager(models.Manager):
    def get_queryset(self):
        qs = super(TranslationManager, self).get_queryset()
        return qs.select_related('language').filter(language__visible=True)

class Translation(Interlinear):
    translation = models.TextField()
    exercise = models.ForeignKey(TranslationExercise, related_name='translations')
    language = models.ForeignKey(Language, related_name='translations')
    translator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='translations'
    )
    added = models.DateTimeField(default=tznow, editable=False)
    last_modified = models.DateTimeField(default=tznow, editable=False)

    _default_manager = TranslationManager()
    _base_manager = _default_manager
    objects = _default_manager
    all_translations = models.Manager()

    class Meta:
        db_table = 'cals_translation'
        ordering = ('exercise', 'language', 'translator')
        unique_together = (('language', 'translator', 'exercise'),)
        get_latest_by = 'last_modified'

    def __unicode__(self):
        return self.translation

    def get_url_kwargs(self):
        return {
            'exercise': self.exercise.slug,
            'language': self.language.id,
            'translator': self.translator.id
        }

    def get_absolute_url(self):
        return reverse('translation-detail', kwargs=self.get_url_kwargs())

    def get_update_url(self):
        return reverse('translation-update', kwargs=self.get_url_kwargs())

    def get_delete_url(self):
        return reverse('translation-delete', kwargs=self.get_url_kwargs())

    def save(self, user=None, batch=False, *args, **kwargs):
        if not self.id and user:
            self.translator = user
        if not batch:
            self.last_modified = tznow()
        super(Translation, self).save(*args, **kwargs)

